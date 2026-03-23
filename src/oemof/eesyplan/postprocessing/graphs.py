import numpy as np
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
    Create a Plotly Sankey diagram from a DataFrame whose columns are a 2-level MultiIndex:
        columns = MultiIndex[(source, target), ...]

    Parameters
    ----------
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

    # TODO here the nodes need to hide the level behind the atomic components (this should be done by filtering at the results level)
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
            else:
                color = "yellow"
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
    return fig


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


def stacked_timeseries(flows, energy_system, scenario_name=None):
    """
      go through each busses of a different carrier type and flag the components belonging to the different carriers
     flow coming into a "storage", "heat_pump", "chp_fixed_ratio" or "chp" are flagged as "demand" for the `group`
     attribute of the stacked graph. Any component of type sink will also be flagged as "demand", all other components
     will belong to the "production" group. The value into the `mode` attribute will be 'lines' for `group="demand"` and 'none'
     The value into the `fill` attribute will be 'none' for the demand group and 'tonexty' for the production group
     One needs also to sort the timeseries according to this rule: first demand, then storages and finally dsos, the
     other types come then next
     Here we shouldn't a priori see the flows internal to subnetworks

    if scenario_name is provided, then the label of the traces should have it as a prefix (useful when producing a
    comparison figure of several simulations)

    """


def graph_timeseries(
    flows, energy_system, y_variables=None, scenario_name=None
):
    """
    prepare a graph with all timeseries of the components of the energy_system with
    a positive sign for the "production" (going into a bus) and a negative sign for "demand" (going outside a bus)

    if y_variables is provided (list of strings), then only the component label within this list will be graphed

    if scenario_name is provided, then the label of the traces should have it as a prefix (useful when producing a
    comparison figure of several simulations)
    """


def graph_costs(arrangement, scenario_name=None):
    """
    Compute capex_total, opex_fix_total, opex_var_total, fuel_costs_total from the following information one need to
    gather for each component:
    Example:
    >                         label  installed_capacity  capex_fix  capex_var  opex_fix  opex_var  lifetime energy_price   optimized_capacity     total_flow direction
    0                        BHKW                 0.0        0.0     1100.0      11.0   0.00000        15            0     10.728721             60135.444842        in
    1                  Gas_boiler                 0.0        0.0      120.0       4.0   0.00000        20            0     93.602946            159106.826600        in
    2              Solarkollektor                 0.0        0.0      300.0      20.0   0.00000        20            0     3.872608               2800.789583        in

    Maybe those calculation are already provided by the Results object and the first part of this fonction is obsolete

    if scenario_name is provided, then the label of the traces should have it as a prefix (useful when producing a
    comparison figure of several simulations)

    """

    # 4 variant of the cost graph, to be chosen by the user within arrangement argument
    COSTS_PER_ASSETS = "var1"  # currently this one is plotted on the result page in OpenPlan GUI
    COSTS_PER_CATEGORY = "var2"
    COSTS_PER_CATEGORY_STACKED = "var3"
    COSTS_PER_ASSETS_STACKED = "var4"

    wacc = 0.1  # should come from `discount_factor` value within project.csv resource
    df = pd.DataFrame()  # should contain the above

    def annualize_capex(capex, wacc, lifetime):
        ann_capex = (
            capex
            * (wacc * (1 + wacc) ** lifetime)
            / ((1 + wacc) ** lifetime - 1)
        )
        return ann_capex

    # TODO costs for batteries are skewed as battery capacity does not exists in fancy results
    # TODO costs for dso not implemented yet
    df["capex_total"] = df.apply(
        lambda x: annualize_capex(
            ((x.installed_capacity + x.optimized_capacity) * x.capex_var),
            wacc,
            x.lifetime,
        ),
        axis=1,
    )

    df["opex_fix_total"] = df.apply(
        lambda x: (x.installed_capacity + x.optimized_capacity) * x.opex_fix,
        axis=1,
    )
    df["opex_var_total"] = df.apply(
        lambda x: x.total_flow * x.opex_var, axis=1
    )

    # nur für dso ...
    df["fuel_costs_total"] = df.apply(
        lambda x: x.total_flow * x.energy_price, axis=1
    )

    if arrangement in [COSTS_PER_ASSETS_STACKED, COSTS_PER_CATEGORY_STACKED]:
        x_values = [
            # x
            # for x in Scenario.objects.filter(simulation__in=simulations).values_list(
            #     "name", flat=True
            # )
        ]  # need to be understood from OpenPlan context
        y_values = []

    # This is the current arrangement within OpenPlan GUI
    if arrangement == COSTS_PER_ASSETS:
        x_values = df.index.values.tolist()
        y_values = []
        for i in range(len(df.columns)):
            name = df.iloc[:, i].name.replace("_total", "")
            y = df.iloc[:, i].values.tolist()
            y_values.append(
                {
                    "base": (
                        df.iloc[:, :i].sum(axis=1).values.tolist()
                        if i > 0
                        else None
                    ),
                    "value": y,
                    "text": [name for j in range(len(x_values))],
                    "name": (
                        name
                        if scenario_name is None
                        else f"{name} {scenario_name}"
                    ),
                    "hover": "<b>%{text}, </b><br><br>Block value: %{customdata:.2f}$<br>Stacked value: %{y:.2f}$<extra> %{x}</extra>",
                    "customdata": y,
                    # https://stackoverflow.com/questions/59057881/python-plotly-how-to-customize-hover-template-on-with-what-information-to-show
                }
            )

    elif arrangement == COSTS_PER_CATEGORY:
        x_values = df.columns.tolist()
        y_values = []
        for i in range(len(df.index)):
            name = df.iloc[i, :].name
            y = df.iloc[i, :].values.tolist()
            y_values.append(
                {
                    "base": (
                        df.iloc[:i, :].sum(axis=0).values.tolist()
                        if i > 0
                        else None
                    ),
                    "value": y,
                    "text": [name for j in range(len(x_values))],
                    "name": (
                        name
                        if scenario_name is None
                        else f"{name} {scenario_name}"
                    ),
                    "hover": "<b>%{text}</b><br><br>Block value: %{customdata:.2f}$<br>Stacked value: %{y:.2f}$",
                    "customdata": y,
                }
            )

    elif arrangement == COSTS_PER_CATEGORY_STACKED:
        y_values.append(df.sum(axis=1))
    elif arrangement == COSTS_PER_ASSETS_STACKED:
        y_values.append(df.sum(axis=0))

    def graph_load_duration(flows, es, energy_carrier):
        """Was drafted within FlowResults.load_duration_figure within OpenPlan. but wasn't implemented"""
        df_consumption = pd.DataFrame()  # collect all flows which go out of buses with given energy_carrier and have the component as column
        df_production = pd.Dataframe()  # collect all flows which go inside of buses with given energy_carrier and have the component as column

        percentage = np.linspace(0, 100, df_production.index.size)
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=percentage.tolist(),
                    y=df_production.loc[:, col]
                    .sort_values(ascending=False)
                    .values.tolist(),
                    name=col,
                    stackgroup="production",
                )
                for col in df_production.columns
            ]
            + [
                go.Scatter(
                    x=percentage.tolist(),
                    y=df_consumption.sort_values(
                        ascending=False
                    ).values.tolist(),
                    name="demand",
                )
            ],
            layout={
                "title": f"Load duration curve for {energy_carrier}",
                "hovermode": "x unified",
            },
        )

        return fig
