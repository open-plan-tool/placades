import pandas as pd
import plotly.graph_objects as go

from oemof.eesyplan import CarrierBus
from oemof.eesyplan import EnergySystem


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
