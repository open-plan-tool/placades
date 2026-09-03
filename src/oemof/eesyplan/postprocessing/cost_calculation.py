import logging
from collections import defaultdict

import networkx as nx
import numpy as np
import pandas as pd

from oemof.solph.components import Source

FLOW_COLUMNS = [
    "flow_v",
    "var_c_tot",
    "var_c_spec",
    "fix_c_tot_p",
    "fix_c_spec_p",
    "var_c_tot_p",
    "var_c_spec_p",
]

ZERO_WHEN_NO_FLOW = [
    "var_c_tot",
    "var_c_spec",
    "fix_c_tot_p",
    "fix_c_spec_p",
    "var_c_tot_p",
    "var_c_spec_p",
]

FROM_SOURCE = "from_source"
TO_STORAGE = "to_storage"
FROM_STORAGE = "from_storage"
NORMAL = "normal"
CIRCULAR_INTERNAL = "circular_internal"
CIRCULAR_INFLOW = "circular_inflow"
CIRCULAR_OUTFLOW = "circular_outflow"

#todo: Implement Fix costs into the calculations

def calculate_costs_of_all_flows(results) -> dict:
    flow_v = results.to_df("flow")
    abs_var_cost_values = results.to_df("variable_costs")
    invest_costs_df = (
        results.to_df("investment_costs")
        if "investment_costs" in results.keys()
        else pd.DataFrame()
    )

    graph = build_graph_timestep(flow_v)
    cycles = list(nx.simple_cycles(graph))
    logging.info("Detected cycles: %s", cycles)

    flows_from = defaultdict(list)
    flows_to = defaultdict(list)
    for f in flow_v.columns:
        source, target = f
        flows_from[source].append(f)
        flows_to[target].append(f)

    storage_content, storage_nodes = _extract_storage(results)

    f_all = _init_flow_records(
        flow_v, abs_var_cost_values, invest_costs_df, storage_nodes, flows_to
    )
    f_all = fix_simultaneous_storage_flows(f_all, storage_nodes)

    circular_nodes, internal_flows = find_circular_nodes(f_all, cycles)
    cycle_inflows, cycle_outflows = get_cycle_inflows_outflows(
        f_all, circular_nodes, internal_flows
    )
    for f in f_all:
        if f in internal_flows:
            f_all[f]["type"] = CIRCULAR_INTERNAL
        elif f in cycle_outflows:
            f_all[f]["type"] = CIRCULAR_OUTFLOW
        elif f in cycle_inflows and f_all[f]["type"] != FROM_STORAGE:
            f_all[f]["type"] = CIRCULAR_INFLOW

    _validate_no_simultaneous_storage(f_all, storage_nodes)

    _seed_source_flows(f_all)
    _propagate_until_complete(
        f_all,
        flows_from,
        storage_content,
        internal_flows,
        cycle_inflows,
        cycle_outflows,
    )

    for f, rec in f_all.items():
        df = rec["flow_df"]
        if rec["contrib"].empty:
            continue
        if not isinstance(rec["contrib"].columns, pd.MultiIndex):
            logging.warning(
                "Breakdown columns not a MultiIndex for %s->%s: %r",
                f[0].label,
                f[1].label,
                rec["contrib"].columns,
            )
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
                    f[0].label,
                    f[1].label,
                    ctype,
                    float((total - df[col]).abs().max()),
                )

    for f, rec in f_all.items():
        logging.debug(
            "%s->%s: fix_c_spec=%.6f",
            f[0].label,
            f[1].label,
            rec["fix_c_spec"],
        )

    return f_all

def _sum_columns_by_level(df: pd.DataFrame, level) -> pd.DataFrame:
    return df.T.groupby(level=level).sum().T


def fix_simultaneous_storage_flows(f_all: dict, storage_nodes: set) -> dict:
    for storage in storage_nodes:
        f_in_key = None
        f_out_key = None
        for f in f_all:
            source, target = f
            if target == storage:
                f_in_key = f
            if source == storage:
                f_out_key = f

        if f_in_key is None or f_out_key is None:
            logging.warning("No flow pair found for storage %s", storage)
            continue

        in_flow = f_all[f_in_key]["flow_df"]["flow_v"]
        out_flow = f_all[f_out_key]["flow_df"]["flow_v"]

        both_active = (in_flow > 0) & (out_flow > 0)
        n_conflicts = int(both_active.sum())
        if n_conflicts == 0:
            continue

        logging.info(
            "Storage %s: fixing %d simultaneous charge/discharge timesteps",
            storage,
            n_conflicts,
        )

        net = in_flow - out_flow

        load_mask = both_active & (net >= 0)
        f_all[f_in_key]["flow_df"].loc[load_mask, "flow_v"] = net[load_mask]
        f_all[f_out_key]["flow_df"].loc[load_mask, "flow_v"] = 0.0

        discharge_mask = both_active & (net < 0)
        f_all[f_out_key]["flow_df"].loc[discharge_mask, "flow_v"] = (-net)[
            discharge_mask
        ]
        f_all[f_in_key]["flow_df"].loc[discharge_mask, "flow_v"] = 0.0

        for f_key, mask, new_flow, old_flow in [
            (f_in_key, load_mask, net[load_mask], in_flow[load_mask]),
            (
                f_out_key,
                discharge_mask,
                (-net)[discharge_mask],
                out_flow[discharge_mask],
            ),
        ]:
            scale = new_flow / old_flow.replace(0, np.nan)
            f_all[f_key]["flow_df"].loc[mask, "var_c_tot"] *= scale.fillna(0)
            fv = f_all[f_key]["flow_df"]["flow_v"]
            vc = f_all[f_key]["flow_df"]["var_c_tot"]
            f_all[f_key]["flow_df"]["var_c_spec"] = np.where(
                fv == 0, 0, vc / fv
            )

        for f_key in [f_in_key, f_out_key]:
            zero_mask = f_all[f_key]["flow_df"]["flow_v"] == 0
            f_all[f_key]["flow_df"].loc[zero_mask, ZERO_WHEN_NO_FLOW] = 0.0

    return f_all


def find_circular_nodes(f_all: dict, cycles: list) -> tuple:
    circular_nodes = set()
    internal_flows = set()

    for cycle in cycles:
        cycle_set = set(cycle)

        contains_storage = any(
            isinstance(node_obj, type(f[0]).__mro__[0])
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


def get_cycle_inflows_outflows(
    f_all: dict, circular_nodes: set, internal_flows: set
) -> tuple:
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
    try:
        storage_content = results.to_df("storage_content").clip(lower=0)
        storage_nodes = set(storage_content.columns)
    except KeyError:
        storage_content = None
        storage_nodes = set()
    logging.info("Storage nodes: %s", storage_nodes)
    return storage_content, storage_nodes


def _build_flow_frame(
    flow_series: pd.Series, var_cost_series: pd.Series, timeindex: pd.Index
) -> pd.DataFrame:
    frame = pd.DataFrame(np.nan, index=timeindex, columns=FLOW_COLUMNS)
    frame["flow_v"] = flow_series.values.clip(min=0)
    frame["var_c_tot"] = var_cost_series
    frame["var_c_spec"] = np.where(
        frame["flow_v"] == 0, 0, frame["var_c_tot"] / frame["flow_v"]
    )
    frame.loc[frame["flow_v"] == 0, ZERO_WHEN_NO_FLOW] = 0
    return frame


def _classify_flow_type(source, target, storage_nodes: set) -> str:
    if source in storage_nodes:
        return FROM_STORAGE
    if target in storage_nodes:
        return TO_STORAGE
    if isinstance(source, Source):
        return FROM_SOURCE
    return NORMAL


def _init_flow_records(
    flow_v: pd.DataFrame,
    abs_var_cost_values: pd.DataFrame,
    invest_costs_df: pd.DataFrame,
    storage_nodes: set,
    flows_to: dict,
) -> dict:
    timeindex = flow_v.index
    f_all = {}
    for f in flow_v.columns:
        source, target = f
        frame = _build_flow_frame(flow_v[f], abs_var_cost_values[f], timeindex)
        total_flow = frame["flow_v"].sum()

        has_invest = f in invest_costs_df.columns
        fix_c_spec = (
            invest_costs_df[f].iloc[0] / total_flow
            if has_invest and total_flow != 0
            else 0
        )

        f_all[f] = {
            "flow_df": frame,
            "fix_c_spec": fix_c_spec,
            "tot_flow": total_flow,
            "type": _classify_flow_type(source, target, storage_nodes),
            "inputs": flows_to[source],
            "calculated": False,
            "contrib": pd.DataFrame(
                0.0,
                index=timeindex,
                columns=pd.MultiIndex.from_arrays(
                    [[], []], names=["origin", "type"]
                ),
            ),
        }
    return f_all


def _own_contrib(f, f_all: dict) -> pd.DataFrame:
    df = f_all[f]["flow_df"]
    self_label = f"{f[0].label}->{f[1].label}"
    own = pd.DataFrame(
        0.0,
        index=df.index,
        columns=pd.MultiIndex.from_arrays([[], []], names=["origin", "type"]),
    )
    own[(self_label, "fix")] = f_all[f]["fix_c_spec"] * df["flow_v"]
    own[(self_label, "var")] = df["var_c_tot"]
    return own


def _validate_no_simultaneous_storage(f_all: dict, storage_nodes: set) -> None:
    for storage in storage_nodes:
        f_in = next(f for f in f_all if f[1] == storage)
        f_out = next(f for f in f_all if f[0] == storage)
        both = (f_all[f_in]["flow_df"]["flow_v"] > 0) & (
            f_all[f_out]["flow_df"]["flow_v"] > 0
        )
        logging.debug(
            "Storage %s: %d simultaneous timesteps remain",
            storage,
            int(both.sum()),
        )


def _seed_source_flows(f_all: dict) -> None:
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
    if not rec_in["calculated"]:
        return False
    active = rec_in["flow_df"]["flow_v"] != 0
    return not rec_in["flow_df"].loc[active, "fix_c_tot_p"].isna().any()


def _inputs_ready(f, f_all: dict) -> bool:
    for f_in in f_all[f]["inputs"]:
        rec_in = f_all[f_in]

        if rec_in["calculated"]:
            if not _input_is_usable(rec_in):
                return False
            continue

        if (
            f_all[f]["type"] == TO_STORAGE
            and rec_in["type"] == FROM_STORAGE
            and f_in[1] == f[0]
        ):
            continue

        both_active = (f_all[f]["flow_df"]["flow_v"] != 0) & (
            rec_in["flow_df"]["flow_v"] != 0
        )
        if both_active.any():
            return False

    return True


def _propagate_circular_outflow(
    f,
    f_all: dict,
    internal_flows: set,
    cycle_inflows: set,
    cycle_outflows: set,
    required_inflows: set | None = None,
) -> bool:
    if required_inflows is None:
        required_inflows = cycle_inflows
    if not all(
        f_all[fi]["calculated"] for fi in internal_flows | required_inflows
    ):
        return False

    df = f_all[f]["flow_df"]

    internal_own_fix = sum(
        f_all[fi]["fix_c_spec"] * f_all[fi]["flow_df"]["flow_v"]
        for fi in internal_flows
    )
    internal_own_var = sum(
        f_all[fi]["flow_df"]["var_c_tot"] for fi in internal_flows
    )

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

    block_fix = internal_own_fix + inflow_fix
    block_var = internal_own_var + inflow_var
    df["fix_c_tot_p"] = (
        f_all[f]["fix_c_spec"] * df["flow_v"] + block_fix * weight
    )
    df["var_c_tot_p"] = df["var_c_tot"] + block_var * weight

    active = df["flow_v"] != 0
    df.loc[active, "fix_c_spec_p"] = (
        df.loc[active, "fix_c_tot_p"] / df.loc[active, "flow_v"]
    )
    df.loc[active, "var_c_spec_p"] = (
        df.loc[active, "var_c_tot_p"] / df.loc[active, "flow_v"]
    )

    contrib = _own_contrib(f, f_all)
    internal_own = pd.DataFrame(
        0.0,
        index=df.index,
        columns=pd.MultiIndex.from_arrays([[], []], names=["origin", "type"]),
    )
    for fi in internal_flows:
        fi_df = f_all[fi]["flow_df"]
        label = f"{fi[0].label}->{fi[1].label}"
        internal_own[(label, "fix")] = (
            f_all[fi]["fix_c_spec"] * fi_df["flow_v"]
        )
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
    soc = storage_content[storage]
    n = len(index)
    if len(soc) == n + 1:
        soc_start = pd.Series(soc.values[:-1], index=index)
        soc_after = pd.Series(soc.values[1:], index=index)
    else:
        soc_start = soc.reindex(index)
        soc_after = soc_start.shift(-1)
        soc_after.iloc[-1] = soc_start.iloc[-1]
        logging.warning(
            "Unexpected storage_content length %d for %d timesteps; using fallback alignment",
            len(soc),
            n,
        )
    return soc_start, soc_after


def _propagate_storage_outflow(f, f_all: dict, storage_content) -> bool:
    storage = f[0]
    f_in = f_all[f]["inputs"][0]
    if not f_all[f_in]["calculated"]:
        return False
    if storage_content is None or storage not in storage_content.columns:
        logging.warning("No storage_content for %s", storage.label)
        return False

    df = f_all[f]["flow_df"]
    soc_start, soc_after = _storage_soc_bounds(
        storage_content, storage, df.index
    )

    out_v = df["flow_v"].to_numpy()
    ss = soc_start.to_numpy()
    sa = soc_after.to_numpy()
    n = len(df)

    start = int(np.argmin(ss))

    fix_spec = np.zeros(n)
    var_spec = np.zeros(n)
    fix_tot = np.zeros(n)
    var_tot = np.zeros(n)

    charge_fix = f_all[f_in]["flow_df"]["fix_c_tot_p"].to_numpy()
    charge_var = f_all[f_in]["flow_df"]["var_c_tot_p"].to_numpy()
    charge_label = f"{f_in[0].label}->{f_in[1].label}"
    running_fix = 0.0
    running_var = 0.0
    rel_fix = np.zeros(n)
    rel_var = np.zeros(n)

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

        running_fix += charge_fix[t]
        running_var += charge_var[t]

        out = out_v[t]
        if out > 0:
            denom = ss[t]
            spec_fix = running_fix / denom if denom > 0 else 0
            spec_var = running_var / denom if denom > 0 else 0
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
    source = f[0]
    df = f_all[f]["flow_df"]

    tot_f_out = sum(
        f_all[fo]["flow_df"]["flow_v"] for fo in flows_from[source]
    )

    usable_inputs = [
        fi for fi in f_all[f]["inputs"] if _input_is_usable(f_all[fi])
    ]
    f_in_var_sum = sum(
        f_all[fi]["flow_df"]["var_c_tot_p"] for fi in usable_inputs
    )
    f_in_fix_sum = sum(
        f_all[fi]["flow_df"]["fix_c_tot_p"] for fi in usable_inputs
    )

    weight = pd.Series(
        np.where(tot_f_out != 0, df["flow_v"] / tot_f_out, 0),
        index=df.index,
    )

    df["var_c_tot_p"] = f_in_var_sum * weight + df["var_c_tot"]
    df["fix_c_tot_p"] = (
        f_in_fix_sum * weight + f_all[f]["fix_c_spec"] * df["flow_v"]
    )

    active = df["flow_v"] != 0
    df.loc[active, "var_c_spec_p"] = (
        df.loc[active, "var_c_tot_p"] / df.loc[active, "flow_v"]
    )
    df.loc[active, "fix_c_spec_p"] = (
        df.loc[active, "fix_c_tot_p"] / df.loc[active, "flow_v"]
    )

    contrib = _own_contrib(f, f_all)
    for fi in usable_inputs:
        fi_df = f_all[fi]["flow_df"]
        label = f"{fi[0].label}->{fi[1].label}"
        contrib[(label, "fix")] = fi_df["fix_c_tot_p"] * weight
        contrib[(label, "var")] = fi_df["var_c_tot_p"] * weight
    f_all[f]["contrib"] = _sum_columns_by_level(contrib, [0, 1])

    f_all[f]["calculated"] = True


def _propagate_until_complete(
    f_all: dict,
    flows_from: dict,
    storage_content,
    internal_flows: set,
    cycle_inflows: set,
    cycle_outflows: set,
) -> None:
    progress = True
    storage_inflows = {
        fi for fi in cycle_inflows if f_all[fi]["type"] == FROM_STORAGE
    }
    storage_sources = {fi[0] for fi in storage_inflows}
    while progress:
        progress = False
        for f, rec in f_all.items():
            if rec["calculated"]:
                continue
            ftype = rec["type"]

            if ftype == CIRCULAR_INTERNAL:
                rec["contrib"] = _own_contrib(f, f_all)
                rec["calculated"] = True
                progress = True
                continue

            if ftype == CIRCULAR_OUTFLOW:
                required = (
                    (cycle_inflows - storage_inflows)
                    if f[1] in storage_sources
                    else cycle_inflows
                )
                if _propagate_circular_outflow(
                    f,
                    f_all,
                    internal_flows,
                    cycle_inflows,
                    cycle_outflows,
                    required,
                ):
                    progress = True
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
            logging.warning(
                "Cost calculation did not converge for %s->%s",
                f[0].label,
                f[1].label,
            )


def build_graph_timestep(
    flow_df: pd.DataFrame, threshold: float = 1e-6
) -> nx.DiGraph:
    G = nx.DiGraph()
    for source, target in flow_df.columns:
        series = flow_df[(source, target)]
        if series.sum() > threshold:
            G.add_edge(source.label, target.label)
    return G



