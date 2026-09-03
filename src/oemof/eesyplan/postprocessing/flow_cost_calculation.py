import json

import plotly.express as px
import plotly.io as pio
import pandas as pd
import numpy as np
from oemof.solph.components import Source
import logging
import os
import matplotlib.pyplot as plt
import oemof.solph
from oemof.tools import logger
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx

from oemof.solph import EnergySystem
from oemof.solph import Model
from oemof.solph import buses
from oemof.solph import components
from oemof.solph import create_time_index
from oemof.solph import flows
from oemof.solph import processing
from oemof.solph import Results
from collections import defaultdict

'''
Naming conventions used throughout the cost-propagation code
------------------------------------------------------------
f    = flow
tot  = total            [EUR]
spec = specific         [EUR/kWh]
p    = propagated       (own cost + share of the upstream cost)
c    = cost
v    = value
'''


# ============================================================================
# Cost propagation
# ============================================================================
#
# After the optimisation every flow gets an absolute and a specific cost
# assigned. These "propagated" costs are the basis for LCOE/LCOH calculations.
# A flow's propagated cost is its own cost (investment + operation) plus the
# cost of all upstream flows that feed into it, weighted by how much of the
# upstream energy this flow actually consumes.
#
# Two situations need special treatment:
#   * Storage  - energy can be stored for many timesteps, so a discharge flow
#                inherits the cost of the energy currently held in the store
#                (tracked over time, see _propagate_storage_outflow).
#   * Cycles   - if a component (indirectly) receives its own output as input
#                the propagation would be non-linear. The cyclic region is then
#                treated as one block whose internal cost and the propagated
#                cost of all inflows into the cycle is shared among the flows
#                leaving the cycle (see _propagate_circular_outflow).
# ----------------------------------------------------------------------------

# Column layout of every per-flow DataFrame built during propagation.
FLOW_COLUMNS = [
    "flow_v",        # energy flow per timestep [kWh]
    "var_c_tot",     # absolute variable cost of the flow itself [EUR]
    "var_c_spec",    # specific variable cost of the flow itself [EUR/kWh]
    "fix_c_tot_p",   # propagated absolute fixed cost [EUR]
    "fix_c_spec_p",  # propagated specific fixed cost [EUR/kWh]
    "var_c_tot_p",   # propagated absolute variable cost [EUR]
    "var_c_spec_p",  # propagated specific variable cost [EUR/kWh]
]

# Cost columns that must be reset to 0 wherever the flow itself is 0.
ZERO_WHEN_NO_FLOW = [
    "var_c_tot", "var_c_spec",
    "fix_c_tot_p", "fix_c_spec_p",
    "var_c_tot_p", "var_c_spec_p",
]

# Flow classification labels used by the propagation algorithm.
FROM_SOURCE = "from_source"
TO_STORAGE = "to_storage"
FROM_STORAGE = "from_storage"
NORMAL = "normal"
CIRCULAR_INTERNAL = "circular_internal"
CIRCULAR_INFLOW = "circular_inflow"
CIRCULAR_OUTFLOW = "circular_outflow"


def fix_simultaneous_storage_flows(f_all: dict, storage_nodes: set) -> dict:
    """Remove simultaneous charging and discharging of a storage.

    The optimiser may report a storage charging and discharging in the same
    timestep. Only the net flow is physically meaningful, so the smaller of the
    two is set to 0 while the net flow is kept, and the associated variable
    costs are scaled accordingly.
    """
    for storage in storage_nodes:
        # Locate the storage's charging (in) and discharging (out) flow.
        f_in_key = None
        f_out_key = None
        for f in f_all:
            source, target = f
            if target == storage:
                f_in_key = f   # electricity -> battery_storage
            if source == storage:
                f_out_key = f  # battery_storage -> electricity

        if f_in_key is None or f_out_key is None:
            logging.warning("No flow pair found for storage %s", storage)
            continue

        in_flow = f_all[f_in_key]["flow_df"]["flow_v"]
        out_flow = f_all[f_out_key]["flow_df"]["flow_v"]

        both_active = (in_flow > 0) & (out_flow > 0)
        n_conflicts = int(both_active.sum())
        if n_conflicts == 0:
            continue

        logging.info("Storage %s: fixing %d simultaneous charge/discharge "
                     "timesteps", storage, n_conflicts)

        net = in_flow - out_flow  # >0 -> net charging, <0 -> net discharging

        # Net charging: keep the net on the inflow, zero the outflow.
        load_mask = both_active & (net >= 0)
        f_all[f_in_key]["flow_df"].loc[load_mask, "flow_v"] = net[load_mask]
        f_all[f_out_key]["flow_df"].loc[load_mask, "flow_v"] = 0.0

        # Net discharging: keep -net on the outflow, zero the inflow.
        discharge_mask = both_active & (net < 0)
        f_all[f_out_key]["flow_df"].loc[discharge_mask, "flow_v"] = (-net)[discharge_mask]
        f_all[f_in_key]["flow_df"].loc[discharge_mask, "flow_v"] = 0.0

        # Scale var_c_tot proportionally to the changed flow and recompute spec.
        for f_key, mask, new_flow, old_flow in [
            (f_in_key, load_mask, net[load_mask], in_flow[load_mask]),
            (f_out_key, discharge_mask, (-net)[discharge_mask], out_flow[discharge_mask]),
        ]:
            scale = new_flow / old_flow.replace(0, np.nan)
            f_all[f_key]["flow_df"].loc[mask, "var_c_tot"] *= scale.fillna(0)
            fv = f_all[f_key]["flow_df"]["flow_v"]
            vc = f_all[f_key]["flow_df"]["var_c_tot"]
            f_all[f_key]["flow_df"]["var_c_spec"] = np.where(fv == 0, 0, vc / fv)

        # Re-apply the "all cost columns are 0 where flow is 0" rule.
        for f_key in [f_in_key, f_out_key]:
            zero_mask = f_all[f_key]["flow_df"]["flow_v"] == 0
            f_all[f_key]["flow_df"].loc[zero_mask, ZERO_WHEN_NO_FLOW] = 0.0

    return f_all


def find_circular_nodes(f_all: dict, cycles: list) -> tuple:
    """Return the set of nodes and flows that belong to a non-storage cycle.

    Pure storage cycles (bus -> storage -> bus) are skipped because they are
    already handled by the dedicated to_storage/from_storage logic.
    """
    circular_nodes = set()
    internal_flows = set()

    for cycle in cycles:
        cycle_set = set(cycle)

        # Skip 2-node cycles that only consist of a storage round trip.
        contains_storage = any(
            isinstance(node_obj, oemof.solph.components.GenericStorage)
            for f in f_all
            for node_obj in (f[0], f[1])
            if node_obj.label in cycle_set
        )
        if len(cycle) <= 2 and contains_storage:
            continue

        circular_nodes.update(cycle)
        for f in f_all:
            if f[0].label in cycle_set and f[1].label in cycle_set:
                internal_flows.add(f)

    return circular_nodes, internal_flows


def get_cycle_inflows_outflows(f_all: dict, circular_nodes: set,
                               internal_flows: set) -> tuple:
    """Split the external flows of a cycle into inflows and outflows.

    inflows  : external flows entering the cyclic region (X -> A)
    outflows : external flows leaving the cyclic region (C -> Y)
    """
    cycle_inflows = set()
    cycle_outflows = set()

    for f in f_all:
        if f in internal_flows:
            continue
        if f[1].label in circular_nodes:
            cycle_inflows.add(f)
        if f[0].label in circular_nodes:
            cycle_outflows.add(f)

    return cycle_inflows, cycle_outflows


def _extract_storage(results) -> tuple:
    """Return (storage_content DataFrame, set of storage node objects)."""
    try:
        storage_content = results.to_df("storage_content").clip(lower=0)
        storage_nodes = set(storage_content.columns)
    except KeyError:
        storage_content = None
        storage_nodes = set()
    logging.info("Storage nodes: %s", storage_nodes)
    return storage_content, storage_nodes


def _build_flow_frame(flow_series: pd.Series, var_cost_series: pd.Series,
                      timeindex: pd.Index) -> pd.DataFrame:
    """Create the per-flow DataFrame holding flow values and own costs.

    Propagated columns start as NaN (filled later) and all cost columns are
    forced to 0 wherever the flow is 0.
    """
    frame = pd.DataFrame(np.nan, index=timeindex, columns=FLOW_COLUMNS)
    frame["flow_v"] = flow_series.values.clip(min=0)
    frame["var_c_tot"] = var_cost_series
    frame["var_c_spec"] = np.where(
        frame["flow_v"] == 0, 0, frame["var_c_tot"] / frame["flow_v"]
    )
    frame.loc[frame["flow_v"] == 0, ZERO_WHEN_NO_FLOW] = 0
    return frame


def _classify_flow_type(source, target, storage_nodes: set) -> str:
    """Classify a flow by its endpoints (storage/source/normal)."""
    if source in storage_nodes:
        return FROM_STORAGE
    if target in storage_nodes:
        return TO_STORAGE
    if isinstance(source, Source):
        return FROM_SOURCE
    return NORMAL


def _init_flow_records(flow_v: pd.DataFrame, abs_var_cost_values: pd.DataFrame,
                       invest_costs_df: pd.DataFrame, storage_nodes: set,
                       flows_to: dict) -> dict:
    """Build the nested ``f_all`` dictionary, one record per flow.

    Each record holds the per-flow DataFrame, the specific fixed cost derived
    from the investment cost, the flow's direct upstream flows and its type.
    """
    timeindex = flow_v.index
    f_all = {}
    for f in flow_v.columns:
        source, target = f
        frame = _build_flow_frame(flow_v[f], abs_var_cost_values[f], timeindex)
        total_flow = frame["flow_v"].sum()

        has_invest = f in invest_costs_df.columns
        fix_c_spec = (invest_costs_df[f].iloc[0] / total_flow
                      if has_invest and total_flow != 0 else 0)

        f_all[f] = {
            "flow_df": frame,
            "fix_c_spec": fix_c_spec,
            "tot_flow": total_flow,
            "type": _classify_flow_type(source, target, storage_nodes),
            # Direct upstream flows = flows whose target is this flow's source.
            "inputs": flows_to[source],
            "calculated": False,
            # Cost breakdown: DataFrame(time x (origin, type)) holding how much
            # of this flow's propagated cost comes from each directly
            # contributing flow (the flow itself and its input flows).
            "contrib": pd.DataFrame(
                0.0, index=timeindex,
                columns=pd.MultiIndex.from_arrays([[], []],
                                                  names=["origin", "type"]),
            ),
        }
    return f_all


def _own_contrib(f, f_all: dict) -> pd.DataFrame:
    """Build the 'own cost' part of a flow's cost breakdown.

    Returns a DataFrame indexed by time whose ``(origin, type)`` columns hold
    the flow's own fixed and variable cost per timestep (origin = the flow
    itself). Every other cost origin is propagated through the upstream flows.
    """
    df = f_all[f]["flow_df"]
    self_label = f"{f[0].label}->{f[1].label}"
    own = pd.DataFrame(
        0.0, index=df.index,
        columns=pd.MultiIndex.from_arrays([[], []], names=["origin", "type"]),
    )
    own[(self_label, "fix")] = f_all[f]["fix_c_spec"] * df["flow_v"]
    own[(self_label, "var")] = df["var_c_tot"]
    return own


def _sum_columns_by_level(df: pd.DataFrame, level) -> pd.DataFrame:
    """Sum DataFrame columns grouped by a column index level.

    Works around ``DataFrame.groupby(axis=1)`` being removed in pandas 3.0 by
    transposing, grouping on the transposed index and transposing back.
    """
    return df.T.groupby(level=level).sum().T


def _validate_no_simultaneous_storage(f_all: dict, storage_nodes: set) -> None:
    """Log how many simultaneous charge/discharge timesteps remain (should be 0)."""
    for storage in storage_nodes:
        f_in = next(f for f in f_all if f[1] == storage)
        f_out = next(f for f in f_all if f[0] == storage)
        both = ((f_all[f_in]["flow_df"]["flow_v"] > 0)
                & (f_all[f_out]["flow_df"]["flow_v"] > 0))
        logging.debug("Storage %s: %d simultaneous timesteps remain",
                      storage, int(both.sum()))


def _seed_source_flows(f_all: dict) -> None:
    """Initialise flows coming straight from a Source.

    A source flow has no upstream cost, so its propagated cost equals its own
    cost. These flows are the starting point of the propagation.
    """
    for f, rec in f_all.items():
        if rec["type"] != FROM_SOURCE:
            continue
        df = rec["flow_df"]
        df["fix_c_spec_p"] = rec["fix_c_spec"]
        df["fix_c_tot_p"] = rec["fix_c_spec"] * df["flow_v"]
        df["var_c_spec_p"] = df["var_c_spec"]
        df["var_c_tot_p"] = df["var_c_tot"]
        rec["contrib"] = _own_contrib(f, f_all)
        rec["calculated"] = True


def _input_is_usable(rec_in: dict) -> bool:
    """True if an upstream flow is calculated and has no NaN where it is active."""
    if not rec_in["calculated"]:
        return False
    active = rec_in["flow_df"]["flow_v"] != 0
    return not rec_in["flow_df"].loc[active, "fix_c_tot_p"].isna().any()


def _inputs_ready(f, f_all: dict) -> bool:
    """Check whether all upstream flows needed for ``f`` are settled.

    An upstream flow blocks propagation only if it is not yet calculated *and*
    it is active at the same timesteps as ``f`` (otherwise it cannot contribute
    cost to ``f`` and can be ignored). The storage round-trip dependency
    (a to_storage flow waiting on its own from_storage flow) is skipped to avoid
    a deadlock.
    """
    for f_in in f_all[f]["inputs"]:
        rec_in = f_all[f_in]

        if rec_in["calculated"]:
            if not _input_is_usable(rec_in):
                return False
            continue

        # Storage circularity: a to_storage flow must not wait on the matching
        # from_storage flow of the same storage.
        if (f_all[f]["type"] == TO_STORAGE
                and rec_in["type"] == FROM_STORAGE
                and f_in[1] == f[0]):
            continue

        both_active = ((f_all[f]["flow_df"]["flow_v"] != 0)
                       & (rec_in["flow_df"]["flow_v"] != 0))
        if both_active.any():
            return False

    return True


def _propagate_circular_outflow(f, f_all: dict, internal_flows: set,
                                cycle_inflows: set, cycle_outflows: set,
                                required_inflows: set = None) -> bool:
    """Assign cost to a flow leaving a cyclic region.

    The cyclic region is treated as one block: the sum of the own costs of all
    internal flows plus the propagated costs of all inflows into the cycle is
    distributed over the cycle's outflows proportionally to their energy.
    Returns True once the flow has been calculated.

    ``required_inflows`` (default: all ``cycle_inflows``) limits the inflows
    the block waits for and distributes. Storage charge flows pass it to ignore
    their own storage's discharge flow: charging and discharging never happen
    in the same timestep (see ``fix_simultaneous_storage_flows``), so the
    charge flow's cost cannot depend on the discharge flow's cost.
    """
    if required_inflows is None:
        required_inflows = cycle_inflows
    # Every internal flow and every required inflow into the cycle must be
    # settled first.
    if not all(f_all[fi]["calculated"] for fi in internal_flows | required_inflows):
        return False

    df = f_all[f]["flow_df"]

    internal_own_fix = sum(
        f_all[fi]["fix_c_spec"] * f_all[fi]["flow_df"]["flow_v"]
        for fi in internal_flows
    )
    internal_own_var = sum(
        f_all[fi]["flow_df"]["var_c_tot"] for fi in internal_flows
    )

    # Propagated cost of all required inflows into the cycle. The guard above
    # ensures they are settled (and NaN-free) before the outflows can be
    # calculated, so their cost is known and can be shared among the outflows.
    inflow_fix = sum(
        f_all[fi]["flow_df"]["fix_c_tot_p"] for fi in required_inflows
    )
    inflow_var = sum(
        f_all[fi]["flow_df"]["var_c_tot_p"] for fi in required_inflows
    )

    tot_outflow = sum(f_all[fo]["flow_df"]["flow_v"] for fo in cycle_outflows)
    weight = pd.Series(
        np.where(tot_outflow != 0, df["flow_v"] / tot_outflow, 0),
        index=df.index,
    )

    # Own cost plus this flow's share of the internal and inflow cycle cost.
    block_fix = internal_own_fix + inflow_fix
    block_var = internal_own_var + inflow_var
    df["fix_c_tot_p"] = f_all[f]["fix_c_spec"] * df["flow_v"] + block_fix * weight
    df["var_c_tot_p"] = df["var_c_tot"] + block_var * weight

    active = df["flow_v"] != 0
    df.loc[active, "fix_c_spec_p"] = df.loc[active, "fix_c_tot_p"] / df.loc[active, "flow_v"]
    df.loc[active, "var_c_spec_p"] = df.loc[active, "var_c_tot_p"] / df.loc[active, "flow_v"]

    # Breakdown: the flow's own cost plus each internal flow's own cost and
    # each inflow's full propagated cost, weighted by this flow's share of the
    # total cycle outflow.
    contrib = _own_contrib(f, f_all)
    internal_own = pd.DataFrame(
        0.0, index=df.index,
        columns=pd.MultiIndex.from_arrays([[], []], names=["origin", "type"]),
    )
    for fi in internal_flows:
        fi_df = f_all[fi]["flow_df"]
        label = f"{fi[0].label}->{fi[1].label}"
        internal_own[(label, "fix")] = f_all[fi]["fix_c_spec"] * fi_df["flow_v"]
        internal_own[(label, "var")] = fi_df["var_c_tot"]
    for fi in cycle_inflows:
        if fi not in required_inflows:
            continue
        fi_df = f_all[fi]["flow_df"]
        label = f"{fi[0].label}->{fi[1].label}"
        internal_own[(label, "fix")] = fi_df["fix_c_tot_p"]
        internal_own[(label, "var")] = fi_df["var_c_tot_p"]
    contrib = contrib.add(internal_own.mul(weight, axis=0), fill_value=0.0)
    f_all[f]["contrib"] = _sum_columns_by_level(contrib, [0, 1])

    f_all[f]["calculated"] = True
    return True


def _storage_soc_bounds(storage_content, storage, index) -> tuple:
    """Split ``storage_content`` into start- and end-of-interval levels.

    oemof reports ``storage_content`` with one entry more than the number of
    flow timesteps: ``storage_content[t]`` is the level at the START of interval
    ``t`` and ``storage_content[t+1]`` the level at its END
    (``end = start + inflow - outflow``). This helper returns two series aligned
    to the flow ``index``: ``soc_start`` and ``soc_after``.
    """
    soc = storage_content[storage]
    n = len(index)
    if len(soc) == n + 1:
        soc_start = pd.Series(soc.values[:-1], index=index)
        soc_after = pd.Series(soc.values[1:], index=index)
    else:
        # Fallback for an unexpected length: treat the values as start-of-
        # interval levels and shift to obtain the end-of-interval levels.
        soc_start = soc.reindex(index)
        soc_after = soc_start.shift(-1)
        soc_after.iloc[-1] = soc_start.iloc[-1]
        logging.warning("Unexpected storage_content length %d for %d timesteps; "
                        "using fallback alignment", len(soc), n)
    return soc_start, soc_after


def _propagate_storage_outflow(f, f_all: dict, storage_content) -> bool:
    """Assign cost to a storage discharge flow.

    The specific cost of the energy held in the store is tracked over the year
    in a running cost account. Iteration starts at the timestep of minimum state
    of charge, so the account starts (almost) empty. When the store is charged,
    the inflow cost is added to the account; when it is discharged, the outflow
    inherits the current specific cost of the stored energy. Because charging
    and discharging never happen in the same timestep (see
    ``fix_simultaneous_storage_flows``), the specific cost stays constant across
    a pure discharge sequence and only changes while charging. The account is
    drained proportionally to the discharged storage CONTENT (the delivered flow
    divided by the outflow conversion factor), so the stored energy's price
    level stays constant even when discharging has delivery losses.

    Returns True once the flow has been calculated, False if the charging flow's
    cost is not known yet.
    """
    storage = f[0]
    f_in = f_all[f]["inputs"][0]            # the storage's single charging flow
    # Use the charging flow directly but wait until its cost is known.
    if not f_all[f_in]["calculated"]:
        return False
    if storage_content is None or storage not in storage_content.columns:
        logging.warning("No storage_content for %s", storage.label)
        return False

    df = f_all[f]["flow_df"]

    # soc_start[t] = content BEFORE the flows of step t, soc_after[t] = content
    # AFTER them. The discharge at step t draws from soc_start[t].
    soc_start, soc_after = _storage_soc_bounds(storage_content, storage, df.index)

    out_v = df["flow_v"].to_numpy()
    ss = soc_start.to_numpy()
    sa = soc_after.to_numpy()
    n = len(df)

    # Start at the minimum state of charge so the cost account starts (near) empty.
    start = int(np.argmin(ss))

    fix_spec = np.zeros(n)
    var_spec = np.zeros(n)
    fix_tot = np.zeros(n)
    var_tot = np.zeros(n)

    # One-hop cost account: the store holds the charging flow's FULL propagated
    # cost (fixed and variable tracked separately). Each charge adds to the
    # account, each discharge removes a proportional share (the specific cost
    # therefore stays constant across a discharge sequence), and the breakdown
    # shows the charging flow as a single origin instead of dissolving it into
    # its own upstream origins.
    charge_fix = f_all[f_in]["flow_df"]["fix_c_tot_p"].to_numpy()
    charge_var = f_all[f_in]["flow_df"]["var_c_tot_p"].to_numpy()
    charge_label = f"{f_in[0].label}->{f_in[1].label}"
    running_fix = 0.0
    running_var = 0.0
    rel_fix = np.zeros(n)
    rel_var = np.zeros(n)

    # The discharge flow is measured in DELIVERED units while the storage
    # content drops by delivered/outflow_conversion_factor (the oemof balance
    # equation). The cost account is tracked per stored-content unit, so the
    # amount of content that actually leaves the store must be used for the
    # proportional removal, otherwise the specific cost of the stored energy
    # drifts during discharge.
    cf = storage.outflow_conversion_factor
    if hasattr(cf, "__getitem__") and not isinstance(cf, (int, float)):
        fac = np.array([float(cf[i]) for i in range(n)])
    else:
        fac = np.full(n, float(cf))
    fac = np.where(fac > 0, fac, 1.0)

    contrib_out = _own_contrib(f, f_all)
    own_fix_spec = f_all[f]["fix_c_spec"]
    own_var = df["var_c_tot"].to_numpy()

    for k in range(n):
        t = (start + k) % n

        # Energy charged this step adds its cost to the store (0 on discharge
        # steps, since charging and discharging are mutually exclusive).
        running_fix += charge_fix[t]
        running_var += charge_var[t]

        out = out_v[t]
        if out > 0:
            # FIX: the denominator is the content BEFORE the discharge
            # (start-of-interval level soc_start[t]). The previous version used
            # ``soc_end + outflow`` based on the wrong assumption that
            # ``storage_content[t]`` was the end-of-interval level, which made
            # the specific cost vary with the discharge amount even without any
            # charging. Discharging removes energy and its proportional cost, so
            # the specific cost stays constant across a discharge sequence.
            denom = ss[t]
            spec_fix = running_fix / denom if denom > 0 else 0
            spec_var = running_var / denom if denom > 0 else 0
            # Content actually removed: the delivered flow loses
            # outflow_conversion_factor < 1 in the storage. The account must be
            # drained by this amount (not by the delivered ``out``) and the
            # delivered unit carries spec/outflow_conversion_factor cost.
            rem = min(out / fac[t], denom)
            fix_out = spec_fix * rem
            var_out = spec_var * rem

            fix_spec[t] = spec_fix / fac[t] + own_fix_spec
            var_spec[t] = spec_var / fac[t] + own_var[t] / out
            fix_tot[t] = fix_out + own_fix_spec * out
            var_tot[t] = var_out + own_var[t]

            if denom > 0:
                rel_fix[t] = fix_out
                rel_var[t] = var_out
                running_fix *= (denom - rem) / denom
                running_var *= (denom - rem) / denom
            else:
                running_fix = 0.0
                running_var = 0.0
        else:
            # Charging or idle: record the blended specific cost of the stored
            # energy (content after charging); no cost leaves the store.
            denom = sa[t]
            fix_spec[t] = running_fix / denom if denom > 0 else 0
            var_spec[t] = running_var / denom if denom > 0 else 0

    contrib_out[(charge_label, "fix")] = rel_fix
    contrib_out[(charge_label, "var")] = rel_var

    df["fix_c_spec_p"] = fix_spec
    df["var_c_spec_p"] = var_spec
    df["fix_c_tot_p"] = fix_tot
    df["var_c_tot_p"] = var_tot

    f_all[f]["contrib"] = _sum_columns_by_level(contrib_out, [0, 1])
    f_all[f]["calculated"] = True
    return True


def _propagate_generic_flow(f, f_all: dict, flows_from: dict) -> None:
    """Propagate cost into a normal (non-storage, non-cyclic) flow.

    The flow inherits a share of the total cost of all its usable upstream
    flows, weighted by how much of the source node's total output it carries,
    and adds its own variable and fixed cost on top.
    """
    source, target = f
    df = f_all[f]["flow_df"]

    # Total energy leaving the source node this timestep (for the weighting).
    tot_f_out = sum(
        f_all[fo]["flow_df"]["flow_v"] for fo in flows_from[source]
    )

    # Sum the propagated cost of all usable inputs (calculated, no active NaN).
    usable_inputs = [fi for fi in f_all[f]["inputs"] if _input_is_usable(f_all[fi])]
    f_in_var_sum = sum(f_all[fi]["flow_df"]["var_c_tot_p"] for fi in usable_inputs)
    f_in_fix_sum = sum(f_all[fi]["flow_df"]["fix_c_tot_p"] for fi in usable_inputs)

    weight = pd.Series(
        np.where(tot_f_out != 0, df["flow_v"] / tot_f_out, 0),
        index=df.index,
    )

    # Inherited upstream share plus this flow's own cost.
    df["var_c_tot_p"] = f_in_var_sum * weight + df["var_c_tot"]
    df["fix_c_tot_p"] = f_in_fix_sum * weight + f_all[f]["fix_c_spec"] * df["flow_v"]

    active = df["flow_v"] != 0
    df.loc[active, "var_c_spec_p"] = df.loc[active, "var_c_tot_p"] / df.loc[active, "flow_v"]
    df.loc[active, "fix_c_spec_p"] = df.loc[active, "fix_c_tot_p"] / df.loc[active, "flow_v"]

    # One-hop breakdown: the flow's own cost plus each direct input's FULL
    # propagated cost (fixed and variable separately), weighted by this flow's
    # share of the source node's total output. Inputs therefore appear under
    # their own label (e.g. a storage output flow) instead of being dissolved
    # into their own upstream origins.
    contrib = _own_contrib(f, f_all)
    for fi in usable_inputs:
        fi_df = f_all[fi]["flow_df"]
        label = f"{fi[0].label}->{fi[1].label}"
        contrib[(label, "fix")] = fi_df["fix_c_tot_p"] * weight
        contrib[(label, "var")] = fi_df["var_c_tot_p"] * weight
    f_all[f]["contrib"] = _sum_columns_by_level(contrib, [0, 1])

    f_all[f]["calculated"] = True


def _propagate_until_complete(f_all: dict, flows_from: dict, storage_content,
                              internal_flows: set, cycle_inflows: set,
                              cycle_outflows: set) -> None:
    """Iteratively propagate cost through the network until all flows are done.

    Repeatedly sweep over all flows; a flow is calculated as soon as the flows
    it depends on are ready. The loop terminates when a full sweep makes no
    further progress.
    """
    progress = True
    # Storage discharges that are also cycle inflows are settled by the
    # storage logic (not by the block); their cost feeds the block afterwards.
    storage_inflows = {fi for fi in cycle_inflows
                       if f_all[fi]["type"] == FROM_STORAGE}
    storage_sources = {fi[0] for fi in storage_inflows}
    while progress:
        progress = False
        for f, rec in f_all.items():
            if rec["calculated"]:
                continue
            ftype = rec["type"]

            # Internal cycle flows keep only their own (already-zeroed) cost.
            if ftype == CIRCULAR_INTERNAL:
                rec["contrib"] = _own_contrib(f, f_all)
                rec["calculated"] = True
                progress = True
                continue

            # Outflows leaving a cycle: distribute the cycle's internal cost.
            # Storage charge flows only wait for the non-storage inflows since
            # they can never be active while their own discharge is.
            if ftype == CIRCULAR_OUTFLOW:
                required = ((cycle_inflows - storage_inflows)
                            if f[1] in storage_sources else cycle_inflows)
                if _propagate_circular_outflow(f, f_all, internal_flows,
                                               cycle_inflows, cycle_outflows,
                                               required):
                    progress = True
                # FIX: never fall through to generic propagation, which would
                # otherwise overwrite the cycle-specific result.
                continue

            if not _inputs_ready(f, f_all):
                continue

            if ftype == FROM_STORAGE:
                if _propagate_storage_outflow(f, f_all, storage_content):
                    progress = True
            else:
                _propagate_generic_flow(f, f_all, flows_from)
                progress = True

    for f, rec in f_all.items():
        if not rec["calculated"]:
            logging.warning("Cost calculation did not converge for %s->%s",
                            f[0].label, f[1].label)


def calculate_costs_of_all_flows(results) -> dict:
    """Compute the propagated cost of every flow in the optimised system.

    Every flow receives a fixed cost (€/kWh, constant over the year) and a
    variable cost (€/kWh, varying per timestep). These propagated costs make it
    possible to derive LCOE/LCOH since every flow then carries a cost.

    The propagated fixed cost is built from the investment and fixed operation
    cost of a component plus the fixed cost of all flows feeding into it,
    proportional to their actual usage; the propagated variable cost is built
    analogously from the dispatch costs.

    If a component (directly or indirectly) receives its own output as input,
    the cost calculation becomes non-linear; the circular region is then treated
    as a single block with no further internal cost distribution. The costs of
    the block (own costs of its internal flows plus the propagated costs of all
    flows entering the cycle) are shared among the flows leaving the cycle
    proportionally to their energy.

    Returns
    -------
    f_all : dict
        Nested dictionary, one record per flow of the optimised system. The
        outer keys are the flow tuples ``(source, target)`` of the two oemof
        node objects connected by the flow (``source.label -> target.label``
        identifies a flow). Each record has exactly the following structure::

            f_all[(source, target)] = {
                # Per-timestep data of this flow, indexed by the timestep
                # DatetimeIndex:
                "flow_df": pd.DataFrame(columns=[
                    "flow_v",       # energy flow per timestep [kWh]
                    "var_c_tot",    # own absolute variable cost [EUR]
                    "var_c_spec",   # own specific variable cost [EUR/kWh]
                    "fix_c_tot_p",  # propagated absolute fixed cost [EUR]
                    "fix_c_spec_p", # propagated specific fixed cost [EUR/kWh]
                    "var_c_tot_p",  # propagated absolute variable cost [EUR]
                    "var_c_spec_p", # propagated specific variable cost [EUR/kWh]
                ]),
                # Own specific fixed cost of the flow, derived from the
                # investment cost of the connected component [EUR/kWh],
                # constant over the year.
                "fix_c_spec": float,

                # Total energy carried by the flow over the whole year [kWh].
                "tot_flow": float,

                # Flow classification: "from_source", "to_storage",
                # "from_storage" or "normal"; overwritten to
                # "circular_internal", "circular_inflow" or "circular_outflow"
                # for flows that take part in an energy cycle.
                "type": str,
                # Direct upstream flows: every flow whose target is this
                # flow's source node, as a list of the same (source, target)
                # tuple keys used in f_all.
                "inputs": list[tuple[Node, Node]],
                # True once the propagated cost columns of "flow_df" are
                # final; False while the flow is still waiting on upstream
                # flows (and always False for flows that never get settled).
                "calculated": bool,
                # Cost breakdown per timestep: DataFrame indexed like
                # "flow_df" with a MultiIndex column (names ["origin",
                # "type"]) holding how much of this flow's propagated cost
                # comes from each directly contributing flow. "origin" is the
                # "source->target" label of the contributing flow (including
                # the flow itself), "type" is "fix" or "var". Empty (no
                # columns) before the flow is calculated.
                "contrib": pd.DataFrame,
            }

        Notes on the values: all ``*_p`` columns start as NaN and are reset to
        0 wherever ``flow_v`` is 0; the propagated specific costs relate to the
        propagated absolute costs via ``*_c_spec_p = *_c_tot_p / flow_v``.
        ``contrib`` sums (over all origins, fix + var) to the corresponding
        propagated absolute cost columns. For a storage's discharge flow,
        ``fix_c_spec_p``/``var_c_spec_p`` are per DELIVERED unit, i.e. the
        stored energy's price level divided by the storage's
        ``outflow_conversion_factor``.
    """
    flow_v = results.to_df("flow")
    abs_var_cost_values = results.to_df("variable_costs")
    invest_costs_df = (results.to_df("investment_costs")
                       if "investment_costs" in results.keys() else pd.DataFrame())

    # Detect circular energy paths on the per-timestep flow graph.
    graph = build_graph_timestep(flow_v)
    cycles = list(nx.simple_cycles(graph))
    logging.info("Detected cycles: %s", cycles)

    # Index which flows leave / enter each node.
    flows_from = defaultdict(list)
    flows_to = defaultdict(list)
    for f in flow_v.columns:
        source, target = f
        flows_from[source].append(f)
        flows_to[target].append(f)

    storage_content, storage_nodes = _extract_storage(results)

    # Build per-flow records and remove simultaneous storage charge/discharge.
    f_all = _init_flow_records(flow_v, abs_var_cost_values, invest_costs_df,
                               storage_nodes, flows_to)
    f_all = fix_simultaneous_storage_flows(f_all, storage_nodes)

    # Tag flows that take part in a (non-storage) cycle.
    circular_nodes, internal_flows = find_circular_nodes(f_all, cycles)
    cycle_inflows, cycle_outflows = get_cycle_inflows_outflows(
        f_all, circular_nodes, internal_flows)
    for f in f_all:
        if f in internal_flows:
            f_all[f]["type"] = CIRCULAR_INTERNAL
        elif f in cycle_outflows:
            f_all[f]["type"] = CIRCULAR_OUTFLOW
        elif f in cycle_inflows and f_all[f]["type"] != FROM_STORAGE:
            f_all[f]["type"] = CIRCULAR_INFLOW

    _validate_no_simultaneous_storage(f_all, storage_nodes)

    # Seed source flows, then propagate cost through the whole network.
    _seed_source_flows(f_all)
    _propagate_until_complete(f_all, flows_from, storage_content,
                              internal_flows, cycle_inflows, cycle_outflows)

    # Validate that every breakdown reproduces the propagated cost columns.
    for f, rec in f_all.items():
        df = rec["flow_df"]
        if rec["contrib"].empty:
            continue
        if not isinstance(rec["contrib"].columns, pd.MultiIndex):
            logging.warning("Breakdown columns not a MultiIndex for %s->%s: %r",
                            f[0].label, f[1].label, rec["contrib"].columns)
            continue
        for ctype, col in (("fix", "fix_c_tot_p"), ("var", "var_c_tot_p")):
            if df[col].isna().any():
                continue
            if ctype not in rec["contrib"].columns.get_level_values("type"):
                continue
            total = rec["contrib"].xs(ctype, level="type", axis=1).sum(axis=1)
            if not np.allclose(total, df[col], rtol=1e-6, atol=1e-6):
                logging.warning(
                    "Breakdown mismatch for %s->%s (%s cost): max diff %.6f",
                    f[0].label, f[1].label, ctype,
                    float((total - df[col]).abs().max()))

    for f, rec in f_all.items():
        logging.debug("%s->%s: fix_c_spec=%.6f",
                      f[0].label, f[1].label, rec["fix_c_spec"])

    return f_all


