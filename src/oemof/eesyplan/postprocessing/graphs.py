import colorsys
from collections import defaultdict

import pandas as pd
import plotly.graph_objects as go

from oemof.eesyplan import CarrierBus
from oemof.eesyplan import EnergySystem
from oemof.eesyplan.postprocessing.cost_calculation import CIRCULAR_INTERNAL
from oemof.eesyplan.postprocessing.cost_calculation import (
    calculate_costs_of_all_flows,
)


def sankey_from_results(
    results,
    title: str = "Sankey Diagram",
    row: int | str | pd.Timestamp | None = None,
    agg: str = "sum",
    drop_zero_links: bool = False,
) -> tuple[go.Figure, pd.DataFrame]:
    """
    Create a Plotly Sankey diagram directly from an oemof.solph Result object.

    This is a convenience wrapper around ``graphs.sankey`` that extracts the
    flow DataFrame and the energy system from the result object so the caller
    does not have to do so manually.

    Parameters
    ----------
    results : oemof.solph.Results
        Result object obtained from ``Results(model)`` after solving.
    title : str
        Figure title.
    row : int | str | pd.Timestamp | None
        If None, aggregate across rows using *agg*.
        If provided, use only that row (by integer position or index label).
    agg : str
        Aggregation across rows when *row* is None.
        One of: ``"sum"``, ``"mean"``, ``"max"``.
    drop_zero_links : bool
        Whether to remove links with value == 0.

    Returns
    -------
    fig : plotly.graph_objects.Figure
        Plotly Sankey figure.
    links_df : pandas.DataFrame
        Parsed links table with columns: source, target, value.
    """
    flows: pd.DataFrame = results.to_df("flow")

    es: EnergySystem | None = None
    if hasattr(results, "_model") and hasattr(results._model, "es"):
        es = results._model.es

    return sankey(
        flows,
        es=es,
        title=title,
        row=row,
        agg=agg,
        drop_zero_links=drop_zero_links,
    )

def sankey(
    flows: pd.DataFrame,
    es: EnergySystem = None,
    title: str = "Sankey Diagram",
    row: int | str | pd.Timestamp | None = None,
    agg: str = "sum",
    drop_zero_links: bool = False,
) -> tuple[go.Figure, pd.DataFrame]:
    """
    Create a Plotly Sankey diagram from a DataFrame whose columns are a
    2-level MultiIndex:
        columns = MultiIndex[(source, target), ...]

    Parameters
    ----------
    es : EnergySystem
        Energy system object from eesyplan.EnergySystem.
    flows : pd.DataFrame
        Result.get("flow") of an oemof.solph Result object
    title : str
        Figure title.
    row : int | str | pd.Timestamp | None
        If None, aggregate across rows using `agg`.
        If provided, use only that row (by integer position or index label).
    agg : str
        Aggregation across rows when row is None. One of: "sum", "mean", "max".
    drop_zero_links : bool
        Whether to remove links with value == 0.

    Returns
    -------
    fig : go.Figure
        Plotly Sankey figure.
    links_df : pd.DataFrame
        Parsed links table with columns: source, target, value.
    """
    if not isinstance(flows.columns, pd.MultiIndex):
        raise TypeError("flows.columns must be a pandas MultiIndex.")

    if flows.columns.nlevels != 2:
        raise ValueError(
            "This function expects exactly 2 column levels: (source, target)."
        )

    if flows.empty:
        raise ValueError("Input DataFrame is empty.")

    numeric_df = flows

    # Statistics over the full time series
    ts_min = numeric_df.min(axis=0)
    ts_max = numeric_df.max(axis=0)

    if agg == "sum":
        ts_agg = numeric_df.sum(axis=0)
    elif agg == "mean":
        ts_agg = numeric_df.mean(axis=0)
    elif agg == "max":
        ts_agg = numeric_df.max(axis=0)
    else:
        raise ValueError("agg must be one of: 'sum', 'mean', or 'max'")

    selected_label = None

    # Value actually plotted
    if row is None:
        plotted_values = ts_agg.copy()
    else:
        if isinstance(row, int):
            plotted_values = flows.iloc[row]
            selected_label = flows.index[row]
        else:
            plotted_values = flows.loc[row]
            selected_label = row

    # Build link table
    links_df = pd.DataFrame(
        {
            "source": [str(src) for src, tgt in plotted_values.index],
            "target": [str(tgt) for src, tgt in plotted_values.index],
            "value": plotted_values.values,
            "min": ts_min.values,
            "max": ts_max.values,
            "aggregate": ts_agg.values,
        }
    )

    if drop_zero_links:
        links_df = links_df[links_df["value"] != 0].copy()
    else:
        links_df["value"] = links_df["value"].replace(0, 1e-9)

    if links_df.empty:
        raise ValueError("No links remain after filtering.")

    # TODO here the nodes need to hide the level behind the atomic components
    #  (this should be done by filtering at the results level)
    # Build node mapping
    nodes = (
        pd.Index(links_df["source"])
        .append(pd.Index(links_df["target"]))
        .unique()
    )
    node_map = {node: i for i, node in enumerate(nodes)}

    if row is None:
        customdata = links_df[["min", "max", "aggregate"]].to_numpy()
        hovertemplate = (
            "Source: %{source.label}<br>"
            "Target: %{target.label}<br>"
            "Plotted value: %{value}<br>"
            "Min: %{customdata[0]}<br>"
            "Max: %{customdata[1]}<br>"
            "Aggregate: %{customdata[2]}"
            "<extra></extra>"
        )
    else:
        links_df["timestamp"] = str(selected_label)
        customdata = links_df[
            ["min", "max", "aggregate", "timestamp"]
        ].to_numpy()
        hovertemplate = (
            "Source: %{source.label}<br>"
            "Target: %{target.label}<br>"
            "Timestamp: %{customdata[3]}<br>"
            "Plotted value: %{value}<br>"
            "Min: %{customdata[0]}<br>"
            "Max: %{customdata[1]}<br>"
            "Aggregate: %{customdata[2]}"
            "<extra></extra>"
        )

    node_colors = None
    if es is not None:
        node_colors = []
        es_nodes = list(es.nodes)
        es_node_labels = [str(n.label) for n in es.nodes]
        for n in nodes:
            if n in es_node_labels:
                node_idx = es_node_labels.index(n)
                es_node = es_nodes[node_idx]
                if isinstance(es_node, CarrierBus):
                    color = "grey"
                else:
                    if len(es_node.inputs) == 0:
                        color = "blue"
                    elif len(es_node.outputs) == 0:
                        color = "red"
                    else:
                        color = "green"
                node_colors.append(color)

    fig = go.Figure(
        go.Sankey(
            node={
                "pad": 15,
                "thickness": 20,
                "line": {"color": "black", "width": 0.5},
                "label": nodes.tolist(),
                "color": node_colors,
            },
            link={
                "source": links_df["source"].map(node_map).tolist(),
                "target": links_df["target"].map(node_map).tolist(),
                "value": links_df["value"].tolist(),
                "customdata": customdata,
                "hovertemplate": hovertemplate,
            },
        )
    )

    fig.update_layout(title_text=title, font_size=12)
    return fig, links_df


def capacities_graph(
    invest: pd.DataFrame, energy_system: EnergySystem
) -> go.Figure:
    """
    Create a grouped bar chart comparing installed and optimized capacities
    for energy system components.

    The function extracts installed capacities from nodes in ``energy_system``
    that provide an ``installed_capacity`` attribute and matches them against
    optimized capacities from ``invest``.

    Parameters
    ----------
    invest : pandas.DataFrame
        Obtained from oemof.solph.Result object accessing the 'invest' key
    energy_system : oemof.eesyplan.model.EnergySystem

    Returns
    -------
    plotly.graph_objects.Figure
        Plotly figure containing a grouped bar chart with installed and
        optimized capacities for each component.
    """

    optimized_map = pd.Series(
        invest.iloc[0].values,
        index=invest.columns.get_level_values(0).astype(str),
    ).to_dict()

    components = []
    installed_capacities = []
    for n in energy_system.nodes:
        if hasattr(n, "installed_capacity"):
            components.append(n.label)
            installed_capacities.append(n.installed_capacity)

    df = pd.DataFrame(
        {"component": components, "installed_capacity": installed_capacities}
    )

    df["optimized_capacity"] = df["component"].map(optimized_map).fillna(0)

    fig = go.Figure()

    fig.add_bar(
        x=df["component"].astype(str),
        y=df["installed_capacity"],
        name="Installed capacity",
        marker={
            "color": "#d64e12",
            "pattern": {
                "shape": "x",
                "fgcolor": "#d64e12",
                "bgcolor": "rgba(0,0,0,0)",
            },
        },
    )

    fig.add_bar(
        x=df["component"].astype(str),
        y=df["optimized_capacity"],
        name="Optimized capacity",
        marker={"color": "#d64e12"},
    )

    fig.update_layout(
        barmode="stack",
        xaxis_title="Component",
        yaxis_title="Capacity",
        margin={"b": 150},
        title="Installed vs Optimized Capacity",
    )

    return fig


def sankey_for_flow_costs(
    results,
    title: str = "Flow Cost Sankey",
) -> tuple[go.Figure, pd.DataFrame]:
    """
    Create a Sankey diagram showing the costs carried by each physical flow.

    Nodes are the actual components/buses of the energy system (e.g.
    ``"wind"``, ``"electricity"``, ``"demand_el"``).  Each physical flow
    between two components is split into one link per cost contribution that
    makes up its propagated costs, i.e. the fix/var breakdown of
    :func:`calculate_costs_of_all_flows`.  Links are coloured by their cost
    origin (lighter = fix, darker = var), so costs can be traced as they
    propagate: wind costs start at ``wind``, enter ``electricity`` and
    continue, still in wind colour, as part of every flow that contains wind
    costs in its propagated breakdown.

    Internal circular flows are not drawn.  Each circular network is
    collapsed into a single node named after all its components; costs that
    originate inside the cycle are shown in grey.

    Link thickness uses ``abs(value)`` because Plotly cannot render negative
    link widths.  Negative contributions (revenues) are tinted towards red
    with a red outline, and the exact signed value is shown in the hover
    tooltip.

    Parameters
    ----------
    results : oemof.solph.Results
        Solved oemof.solph result object.
    title : str
        Figure title.

    Returns
    -------
    fig : plotly.graph_objects.Figure
        Plotly Sankey figure.
    links_df : pandas.DataFrame
        Table with columns: source, target, cost_type, value, color.  The
        ``value`` column holds the signed cost contribution; the link widths
        in the figure use ``abs(value)``.
    """
    all_f = calculate_costs_of_all_flows(results)

    # ---- circular networks collapse into a single node ------------------
    # Internal flows of a circular network are not drawn; instead the whole
    # cycle becomes one node named after all its components.
    internal_flows = {
        f for f, rec in all_f.items() if rec["type"] == CIRCULAR_INTERNAL
    }

    adj = defaultdict(set)
    for f in internal_flows:
        adj[f[0].label].add(f[1].label)
        adj[f[1].label].add(f[0].label)

    circ_super_labels = set()
    comp_to_super = {}
    for start in adj:
        if start in comp_to_super:
            continue
        group = set()
        stack = [start]
        while stack:
            c = stack.pop()
            if c in group:
                continue
            group.add(c)
            stack.extend(adj.get(c, ()))
        super_label = " - ".join(sorted(group))
        circ_super_labels.add(super_label)
        for c in group:
            comp_to_super[c] = super_label

    def _node_of(component_label: str) -> str:
        return comp_to_super.get(component_label, component_label)

    # ---- colour helpers -------------------------------------------------
    def _hsv_to_hex(h, s, v):
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    def _lighten(rgb_hex, factor=0.4):
        r, g, b = (
            int(rgb_hex[1:3], 16),
            int(rgb_hex[3:5], 16),
            int(rgb_hex[5:7], 16),
        )
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"rgb({r},{g},{b})"

    def _darken(rgb_hex, factor=0.3):
        r, g, b = (
            int(rgb_hex[1:3], 16),
            int(rgb_hex[3:5], 16),
            int(rgb_hex[5:7], 16),
        )
        return f"rgb({int(r * (1 - factor))},{int(g * (1 - factor))},{int(b * (1 - factor))})"

    def _tint_towards_red(rgb_value, factor=0.4):
        if rgb_value.startswith("#"):
            r, g, b = (
                int(rgb_value[1:3], 16),
                int(rgb_value[3:5], 16),
                int(rgb_value[5:7], 16),
            )
        elif rgb_value.startswith("rgb("):
            parts = rgb_value[4:-1].split(",")
            r, g, b = (int(p.strip()) for p in parts)
        else:
            return "rgb(220,60,60)"
        r = int(r + (255 - r) * factor)
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        return f"rgb({r},{g},{b})"

    # ---- cost breakdown per flow -> one link per (origin, fix/var) ------
    # Each physical flow is split into one link per cost contribution that
    # makes up its propagated costs, so the origins stay traceable by colour.
    internal_origin_labels = {
        f"{f[0].label}->{f[1].label}" for f in internal_flows
    }
    link_rows = []  # (source node, target node, origin label, ctype, signed value)
    for f, rec in all_f.items():
        if f in internal_flows:
            continue
        src = _node_of(f[0].label)
        tgt = _node_of(f[1].label)
        if src == tgt:
            continue
        contrib = rec["contrib"]
        for col in contrib.columns:
            origin, ctype = col
            val = float(contrib[col].sum())
            if val == 0:
                continue
            link_rows.append((src, tgt, origin, ctype, val))

    # ---- colour by cost origin (internal origins -> grey) ---------------
    all_origins = sorted({o for _, _, o, _, _ in link_rows})
    external_origins = [
        o for o in all_origins if o not in internal_origin_labels
    ]
    n_ext = len(external_origins)
    base_colours = {}
    for i, origin in enumerate(external_origins):
        base_colours[origin] = _hsv_to_hex(i / max(n_ext, 1), 0.65, 0.95)
    for origin in internal_origin_labels:
        base_colours[origin] = "#9E9E9E"

    node_labels = sorted({lbl for s, t, _, _, _ in link_rows for lbl in (s, t)})
    node_index = {n: i for i, n in enumerate(node_labels)}

    sources, targets, values, colours, labels, signed_values = [], [], [], [], [], []
    cost_types = []
    link_lines = []

    for src, tgt, origin, ctype, val in link_rows:
        base = (
            _lighten(base_colours[origin])
            if ctype == "fix"
            else _darken(base_colours[origin])
        )
        sources.append(node_index[src])
        targets.append(node_index[tgt])
        values.append(abs(val))
        signed_values.append(val)
        labels.append(f"{origin} | {src} -> {tgt} ({ctype})")
        cost_types.append(f"{origin} {ctype}")
        if val < 0:
            colours.append(_tint_towards_red(base))
            link_lines.append("rgb(180,0,0)")
        else:
            colours.append(base)
            link_lines.append("rgba(0,0,0,0)")

    # ---- node colours ---------------------------------------------------
    node_colors = []
    for node in node_labels:
        if node in circ_super_labels:
            node_colors.append("#9E9E9E")
        else:
            node_colors.append("lightgrey")

    # ---- build figure ---------------------------------------------------
    fig = go.Figure(
        go.Sankey(
            node={
                "pad": 15,
                "thickness": 20,
                "line": {"color": "black", "width": 0.5},
                "label": node_labels,
                "color": node_colors,
            },
            link={
                "source": sources,
                "target": targets,
                "value": values,
                "color": colours,
                "line": {"color": link_lines, "width": 1.5},
                "customdata": list(
                    zip(labels, signed_values, strict=True)
                ),
                "hovertemplate": (
                    "%{customdata[0]}<br>"
                    "Value: %{customdata[1]:,.2f} EUR"
                    "<extra></extra>"
                ),
            },
        )
    )

    fig.update_layout(title_text=title, font_size=12)

    links_df = pd.DataFrame(
        {
            "source": [node_labels[s] for s in sources],
            "target": [node_labels[t] for t in targets],
            "cost_type": cost_types,
            "value": signed_values,
            "color": colours,
        }
    )
    links_df["value"] = pd.to_numeric(links_df["value"], errors="coerce")

    return fig, links_df
