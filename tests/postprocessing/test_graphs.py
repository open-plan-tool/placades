import warnings
from pathlib import Path

import pandas as pd
import pytest

from oemof.datapackage import datapackage  # noqa
from oemof.eesyplan import CarrierBus
from oemof.eesyplan import Demand
from oemof.eesyplan import DsoElectricity
from oemof.eesyplan import ElectricalStorage
from oemof.eesyplan import EnergySystem
from oemof.eesyplan import Project
from oemof.eesyplan import PvPlant
from oemof.eesyplan import WindTurbine
from oemof.eesyplan import optimise
from oemof.eesyplan.datapackage import energy_system as es
from oemof.eesyplan.postprocessing.graphs import capacities_graph
from oemof.eesyplan.postprocessing.graphs import sankey
from oemof.tools.debugging import ExperimentalFeatureWarning

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)

DATA_PATH = Path("../test_data", "simple_script_data")

DATA_FILES = {
    "pv": Path("pv_profile.csv"),
    "demand_heat": Path("heat_demand.csv"),
    "wind": Path("wind_profile.csv"),
    "demand_elec": Path("electricity_demand.csv"),
}


def simple_script(pv_installed_cap=1.0, optimize_battery=False):
    # ... unverändert ...
    data = {}
    for key, fn in DATA_FILES.items():
        path = Path(Path(__file__).parent, DATA_PATH, fn)
        data[key] = pd.read_csv(path, header=None).squeeze()

    project = Project(name="test", lifetime=20, tax=0, discount_factor=0)
    energy_system = EnergySystem(2023, number=10)
    bus_elec = CarrierBus(name="electricity")
    energy_system.add(bus_elec)
    energy_system.add(
        DsoElectricity(
            name="My_DSO",
            bus_electricity=bus_elec,
            energy_price=5,
            feedin_tariff=0.04,
        )
    )
    energy_system.add(
        WindTurbine(
            name="wind",
            bus_out_electricity=bus_elec,
            input_timeseries=data["wind"],
            installed_capacity=0.25,
            project_data=project,
            optimize_cap=True,
        )
    )
    energy_system.add(
        PvPlant(
            name="pv",
            bus_out_electricity=bus_elec,
            project_data=project,
            capex_var=0.01,
            installed_capacity=pv_installed_cap,
            input_timeseries=data["pv"],
            optimize_cap=True,
        )
    )
    energy_system.add(
        ElectricalStorage(
            name="Batterie",
            bus_in_electricity=bus_elec,
            age_installed=0,
            installed_capacity=10,
            capex_var=3.0,
            opex_fix=5.0,
            opex_var=0.0,
            lifetime=10.0,
            optimize_cap=optimize_battery,
            soc_max=1,
            soc_min=0,
            c_rate_charge=1.0,
            efficiency_charge=0.99,
            project_data=project,
            self_discharge=0.000,
        )
    )
    energy_system.add(
        Demand(
            name="demand_el",
            bus_in=bus_elec,
            input_timeseries=data["demand_elec"],
        )
    )
    return optimise(energy_system), energy_system


def test_graph_capacities():
    res, esys = simple_script()
    capacities_graph(res["invest"], esys)


# --------------------------------------------------------------------------- #
# Sankey-Tests
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def sankey_result():
    """Baut das Energiesystem einmal und liefert (fig, links_df)."""
    path = Path(Path(__file__).parent, "../test_data", "openPlan_package")
    energy_system = es.create_energy_system_from_dp(path)
    results = optimise(energy_system)
    fig, links_df = sankey(results["flow"], es=energy_system)
    return fig, links_df


def test_sankey_returns_figure_and_df(sankey_result):
    fig, links_df = sankey_result
    assert fig.data[0].type == "sankey"
    assert list(links_df.columns) == [
        "source",
        "target",
        "value",
        "min",
        "max",
        "aggregate",
    ]


def test_sankey_nodes(sankey_result):
    """Alle erwarteten Knoten sind vorhanden."""
    fig, _ = sankey_result
    labels = list(fig.data[0].node.label)

    expected = {
        "electricity",
        "lithium_battery_system",
        "pv",
        "wind",
        "('internal_bus', 'My_DSO')",
        "('feedin_converter', 'My_DSO')",
        "('consumption_converter', 'My_DSO')",
        "('consumption_source', 'My_DSO')",
        "('excess', 'electricity')",
        "demand_el",
        "('feedin_sink', 'My_DSO')",
    }
    assert set(labels) == expected


def test_sankey_node_colors(sankey_result):
    """Farb-Logik: Bus=grey, Source=blue, Sink=red, sonst green."""
    fig, _ = sankey_result
    node = fig.data[0].node
    color_by_label = dict(zip(node.label, node.color, strict=False))

    assert color_by_label["electricity"] == "grey"  # CarrierBus
    assert color_by_label["pv"] == "blue"  # nur outputs
    assert color_by_label["wind"] == "blue"
    assert color_by_label["demand_el"] == "red"  # nur inputs
    assert color_by_label["('excess', 'electricity')"] == "red"
    assert color_by_label["lithium_battery_system"] == "green"


def test_sankey_link_structure(sankey_result):
    """Jede Link-ID zeigt auf einen gültigen Knoten, Längen passen."""
    fig, links_df = sankey_result
    link = fig.data[0].link
    n_nodes = len(fig.data[0].node.label)

    assert len(link.source) == len(link.target) == len(link.value)
    assert len(link.value) == len(links_df)
    assert all(0 <= i < n_nodes for i in link.source)
    assert all(0 <= i < n_nodes for i in link.target)


def test_sankey_values(sankey_result):
    """Prüft die aggregierten Flow-Werte gegen erwartete Zahlen."""
    _, links_df = sankey_result

    def value(src, tgt):
        mask = (links_df["source"] == src) & (links_df["target"] == tgt)
        return links_df.loc[mask, "value"].iloc[0]

    # pv speist ins electricity-Bus ein
    assert value("pv", "electricity") == pytest.approx(46.8717, rel=1e-4)

    # electricity deckt den Bedarf demand_el
    assert value("electricity", "demand_el") == pytest.approx(
        104.0765, rel=1e-4
    )

    # electricity -> feedin_converter des DSO
    assert value(
        "electricity", "('feedin_converter', 'My_DSO')"
    ) == pytest.approx(151.4288, rel=1e-4)

    # consumption_converter speist ins electricity-Bus
    assert value(
        "('consumption_converter', 'My_DSO')", "electricity"
    ) == pytest.approx(1e-09, rel=1e-4)


def test_sankey_zero_links_replaced(sankey_result):
    """Ohne drop_zero_links werden 0-Werte durch 1e-9 ersetzt."""
    _, links_df = sankey_result
    assert (links_df["value"] > 0).all()


def test_sankey_drop_zero_links():
    """Mit drop_zero_links werden 0-Flows entfernt."""
    path = Path(Path(__file__).parent, "../test_data", "openPlan_package")
    energy_system = es.create_energy_system_from_dp(path)
    results = optimise(energy_system)

    _, full = sankey(results["flow"], es=energy_system)
    _, dropped = sankey(
        results["flow"], es=energy_system, drop_zero_links=True
    )
    # es gibt echte 0-Flows -> weniger Links
    assert len(dropped) < len(full)
    assert (dropped["value"] != 0).all()


# --------------------------------------------------------------------------- #
# Fehler-/Randfälle
# --------------------------------------------------------------------------- #
def test_sankey_requires_multiindex():
    df = pd.DataFrame({"a": [1, 2]})
    with pytest.raises(
        TypeError, match=r"flows.columns must be a pandas MultiIndex."
    ):
        sankey(df)


def test_sankey_rejects_empty():
    cols = pd.MultiIndex.from_tuples([("a", "b")])
    df = pd.DataFrame(columns=cols)
    with pytest.raises(ValueError, match=r"Input DataFrame is empty."):
        sankey(df)


def test_sankey_invalid_agg():
    cols = pd.MultiIndex.from_tuples([("a", "b")])
    df = pd.DataFrame([[1.0]], columns=cols)
    with pytest.raises(
        ValueError, match="agg must be one of: 'sum', 'mean', or 'max'"
    ):
        sankey(df, agg="median")
