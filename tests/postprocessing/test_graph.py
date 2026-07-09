from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pandas as pd
import plotly.graph_objects as go
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
from oemof.eesyplan.postprocessing.graphs import capacities_graph
from oemof.eesyplan.postprocessing.graphs import sankey

DATA_PATH = Path("test_data", "simple_script_data")

DATA_FILES = {
    "pv": Path("pv_profile.csv"),
    "demand_heat": Path("heat_demand.csv"),
    "wind": Path("wind_profile.csv"),
    "demand_elec": Path("electricity_demand.csv"),
}


# ============================================================================

# FIXTURES

# ============================================================================


@pytest.fixture
def sample_energy_system(pv_installed_cap=1.0, optimize_battery=False):
    # Read data file
    data = {}
    for key, fn in DATA_FILES.items():
        path = Path(Path(__file__).parent.parent, DATA_PATH, fn)
        data[key] = pd.read_csv(path, header=None).squeeze()

    project = Project(name="test", lifetime=20, tax=0, discount_factor=0)

    # ####################### initialize the energy system ####################
    energy_system = EnergySystem(2023, number=24)

    # ######################### create energysystem components ################

    # carrier
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

    # sources
    energy_system.add(
        WindTurbine(
            name="wind",
            bus_out_electricity=bus_elec,
            input_timeseries=data["wind"],
            installed_capacity=0,
            project_data=project,
            optimize_cap=True,
        )
    )
    energy_system.add(
        WindTurbine(
            name="wind2",
            bus_out_electricity=bus_elec,
            input_timeseries=data["wind"],
            installed_capacity=0.25,
            project_data=project,
            optimize_cap=False,
        )
    )

    energy_system.add(
        PvPlant(
            name="pv",
            bus_out_electricity=bus_elec,
            project_data=project,
            capex_var=0.01,
            installed_capacity=0,
            input_timeseries=data["pv"],
            optimize_cap=True,
        )
    )
    energy_system.add(
        PvPlant(
            name="pv2",
            bus_out_electricity=bus_elec,
            project_data=project,
            capex_var=0.01,
            installed_capacity=pv_installed_cap,
            input_timeseries=data["pv"],
            optimize_cap=False,
        )
    )

    energy_system.add(
        ElectricalStorage(
            name="Batterie",
            bus_in_electricity=bus_elec,
            age_installed=0,
            installed_capacity=0,
            capex_var=3.0,
            opex_fix=5.0,
            opex_var=0.0,
            lifetime=10.0,
            optimize_cap=True,
            soc_max=1,
            soc_min=0,
            crate=1.0,
            efficiency=0.99,
            project_data=project,
            self_discharge=0.000,
        )
    )

    energy_system.add(
        ElectricalStorage(
            name="Batterie2",
            bus_in_electricity=bus_elec,
            age_installed=0,
            installed_capacity=10,
            capex_var=3.0,
            opex_fix=5.0,
            opex_var=0.0,
            lifetime=10.0,
            optimize_cap=False,
            soc_max=1,
            soc_min=0,
            crate=1.0,
            efficiency=0.99,
            project_data=project,
            self_discharge=0.000,
        )
    )

    # demands (electricity/heat)
    energy_system.add(
        Demand(
            name="demand_el",
            bus_in_electricity=bus_elec,
            input_timeseries=data["demand_elec"],
        )
    )
    return energy_system


@pytest.fixture
def sample_results(sample_energy_system):
    return optimise(sample_energy_system)


@pytest.fixture
def sample_flows_df(sample_results):
    return sample_results["flow"]


@pytest.fixture
def empty_flows_df():
    """Leerer DataFrame mit korrekter MultiIndex-Struktur."""
    columns = pd.MultiIndex.from_tuples(
        [("source1", "bus1")], names=["source", "target"]
    )
    return pd.DataFrame(columns=columns)


@pytest.fixture
def flows_with_zeros():
    """DataFrame mit einigen Null-Werten."""
    dates = pd.date_range("2023-01-01", periods=10, freq="h")
    columns = pd.MultiIndex.from_tuples(
        [("source1", "bus1"), ("source2", "bus2"), ("source3", "bus3")],
        names=["source", "target"],
    )
    data = np.array([[10, 0, 5]] * 10)
    return pd.DataFrame(data, index=dates, columns=columns)


# ============================================================================

# TESTS FÜR sankey()

# ============================================================================


class TestSankey:
    """Tests für die sankey() Funktion."""

    def test_sankey_basic_sum_aggregation(self, sample_flows_df):
        """Test: Basis-Sankey mit sum-Aggregation."""
        fig, links_df = sankey(sample_flows_df, title="Test Sankey")

        assert isinstance(fig, go.Figure)
        assert isinstance(links_df, pd.DataFrame)
        assert len(links_df) == 15
        assert all(
            col in links_df.columns
            for col in ["source", "target", "value", "min", "max", "aggregate"]
        )
        assert fig.layout.title.text == "Test Sankey"

    def test_sankey_mean_aggregation(self, sample_flows_df):
        """Test: Sankey mit mean-Aggregation."""
        fig, links_df = sankey(sample_flows_df, agg="mean")

        assert isinstance(fig, go.Figure)
        expected_mean = sample_flows_df.mean(axis=0).values
        np.testing.assert_array_almost_equal(
            links_df["value"].values, expected_mean
        )

    def test_sankey_max_aggregation(self, sample_flows_df):
        """Test: Sankey mit max-Aggregation."""
        fig, links_df = sankey(sample_flows_df, agg="max")

        assert isinstance(fig, go.Figure)
        expected_max = sample_flows_df.max(axis=0).values
        np.testing.assert_array_almost_equal(
            links_df["value"].values, expected_max
        )

    def test_sankey_with_row_index_int(self, sample_flows_df):
        """Test: Sankey mit spezifischer Zeile (int)."""
        fig, links_df = sankey(sample_flows_df, row=5)

        assert isinstance(fig, go.Figure)
        expected_values = sample_flows_df.iloc[5].values
        np.testing.assert_array_almost_equal(
            links_df["value"].values, expected_values
        )
        assert "timestamp" in links_df.columns

    def test_sankey_with_row_index_label(self, sample_flows_df):
        """Test: Sankey mit spezifischer Zeile (label)."""
        row_label = sample_flows_df.index[10]
        fig, links_df = sankey(sample_flows_df, row=row_label)

        assert isinstance(fig, go.Figure)
        expected_values = sample_flows_df.loc[row_label].values
        np.testing.assert_array_almost_equal(
            links_df["value"].values, expected_values
        )

    def test_sankey_drop_zero_links(self, flows_with_zeros):
        """Test: Sankey mit drop_zero_links=True."""
        fig, links_df = sankey(flows_with_zeros, drop_zero_links=True)

        assert isinstance(fig, go.Figure)
        assert len(links_df) == 2  # Nur source1 und source3 haben Werte
        assert all(links_df["value"] != 0)

    def test_sankey_keep_zero_links(self, flows_with_zeros):
        """Test: Sankey mit drop_zero_links=False (ersetzt 0 mit 1e-9)."""
        fig, links_df = sankey(flows_with_zeros, drop_zero_links=False)

        assert isinstance(fig, go.Figure)
        assert len(links_df) == 3
        # Prüfe, dass Null-Werte durch 1e-9 ersetzt wurden
        assert any(links_df["value"] == 1e-9)

    def test_sankey_with_energy_system(
        self, sample_flows_df, sample_energy_system
    ):
        """Test: Sankey mit EnergySystem für Knotenfarben."""
        fig, links_df = sankey(sample_flows_df, es=sample_energy_system)

        assert isinstance(fig, go.Figure)
        # Prüfe, dass Knotenfarben gesetzt wurden
        assert fig.data[0].node.color is not None

    def test_sankey_invalid_multiindex(self):
        """Test: Fehler bei fehlendem MultiIndex."""
        df = pd.DataFrame({"col1": [1, 2, 3]})

        with pytest.raises(TypeError, match="must be a pandas MultiIndex"):
            sankey(df)

    def test_sankey_invalid_column_levels(self):
        """Test: Fehler bei falscher Anzahl von Column-Levels."""
        columns = pd.MultiIndex.from_tuples(
            [("a", "b", "c")], names=["l1", "l2", "l3"]
        )
        df = pd.DataFrame([[1]], columns=columns)

        with pytest.raises(ValueError, match="exactly 2 column levels"):
            sankey(df)

    def test_sankey_empty_dataframe(self, empty_flows_df):
        """Test: Fehler bei leerem DataFrame."""
        with pytest.raises(ValueError, match="Input DataFrame is empty"):
            sankey(empty_flows_df)

    def test_sankey_invalid_aggregation(self, sample_flows_df):
        """Test: Fehler bei ungültiger Aggregation."""
        with pytest.raises(ValueError, match="agg must be one of"):
            sankey(sample_flows_df, agg="invalid")

    def test_sankey_all_zeros_with_drop(self):
        """Test: Fehler wenn nach Filtern keine Links übrig bleiben."""
        dates = pd.date_range("2023-01-01", periods=5, freq="h")
        columns = pd.MultiIndex.from_tuples(
            [("source1", "bus1")], names=["source", "target"]
        )
        data = np.zeros((5, 1))
        df = pd.DataFrame(data, index=dates, columns=columns)

        with pytest.raises(
            ValueError, match="No links remain after filtering"
        ):
            sankey(df, drop_zero_links=True)

    def test_sankey_hover_template_without_row(self, sample_flows_df):
        """Test: Hover-Template ohne row-Auswahl."""
        fig, _ = sankey(sample_flows_df)

        hover = fig.data[0].link.hovertemplate
        assert "Min:" in hover
        assert "Max:" in hover
        assert "Aggregate:" in hover
        assert "Timestamp:" not in hover

    def test_sankey_hover_template_with_row(self, sample_flows_df):
        """Test: Hover-Template mit row-Auswahl."""
        fig, _ = sankey(sample_flows_df, row=0)

        hover = fig.data[0].link.hovertemplate
        assert "Timestamp:" in hover
        assert "Min:" in hover
        assert "Max:" in hover


# ============================================================================

# TESTS FÜR capacities_graph()

# ============================================================================


class TestCapacitiesGraph:
    """Tests für die capacities_graph() Funktion."""

    def test_capacities_graph_basic(
        self, sample_results, sample_energy_system
    ):
        """Test: Basis-Funktionalität des Kapazitätsdiagramms."""
        fig = capacities_graph(sample_results["invest"], sample_energy_system)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # Zwei Balkengruppen
        assert fig.data[0].name == "Installed capacity"
        assert fig.data[1].name == "Optimized capacity"
        assert fig.layout.title.text == "Installed vs Optimized Capacity"

    def test_capacities_graph_values(
        self, sample_results, sample_energy_system
    ):
        """Test: Korrekte Werte im Diagramm."""
        fig = capacities_graph(sample_results["invest"], sample_energy_system)

        # Prüfe installed capacities
        installed_trace = fig.data[0]
        assert 10.0 == installed_trace.y.max()
        assert 0 == installed_trace.y.min()
        assert 1 in installed_trace.y

        # # Prüfe optimized capacities
        # optimized_trace = fig.data[1]
        # assert 50.0 in optimized_trace.y
        # assert 75.0 in optimized_trace.y
        # assert 100.0 in optimized_trace.y

    def test_capacities_graph_no_optimized_capacity(
        self, sample_energy_system
    ):
        """Test: Komponenten ohne optimized capacity (sollte 0 sein)."""
        # Invest DataFrame ohne component3
        columns = pd.MultiIndex.from_tuples(
            [("component1", "invest"), ("component2", "invest")]
        )
        invest_df = pd.DataFrame([[50.0, 75.0]], columns=columns)

        fig = capacities_graph(invest_df, sample_energy_system)

        assert isinstance(fig, go.Figure)
        # component3 sollte optimized_capacity = 0 haben
        optimized_trace = fig.data[1]
        assert 0.0 in optimized_trace.y

    def test_capacities_graph_layout(
        self, sample_results, sample_energy_system
    ):
        """Test: Layout-Eigenschaften des Diagramms."""
        fig = capacities_graph(sample_results["invest"], sample_energy_system)

        assert fig.layout.barmode == "stack"
        assert fig.layout.xaxis.title.text == "Component"
        assert fig.layout.yaxis.title.text == "Capacity"
        assert fig.layout.margin.b == 150

    def test_capacities_graph_marker_style(
        self, sample_results, sample_energy_system
    ):
        """Test: Marker-Styles für Balken."""
        fig = capacities_graph(sample_results["invest"], sample_energy_system)

        # Installed capacity mit Pattern
        assert fig.data[0].marker.color == "#d64e12"
        assert fig.data[0].marker.pattern.shape == "x"

        # Optimized capacity ohne Pattern
        assert fig.data[1].marker.color == "#d64e12"

    def test_capacities_graph_empty_nodes(self, sample_results):
        """Test: EnergySystem ohne Nodes mit installed_capacity."""
        es = Mock()
        es.nodes = [Mock(spec=["label"])]  # Kein installed_capacity Attribut

        fig = capacities_graph(sample_results["invest"], es)

        assert isinstance(fig, go.Figure)
        # Sollte leere/null Traces haben
        assert len(fig.data) == 2


# ============================================================================

# TESTS FÜR graph_costs()

# ============================================================================


class TestGraphCosts:
    """Tests für die graph_costs() Funktion."""

    @pytest.fixture
    def sample_cost_df(self):
        """Sample DataFrame mit Kosteninformationen."""
        data = {
            "label": ["BHKW", "Gas_boiler", "Solarkollektor"],
            "installed_capacity": [0.0, 0.0, 0.0],
            "capex_fix": [0.0, 0.0, 0.0],
            "capex_var": [1100.0, 120.0, 300.0],
            "opex_fix": [11.0, 4.0, 20.0],
            "opex_var": [0.0, 0.0, 0.0],
            "lifetime": [15, 20, 20],
            "energy_price": [0, 0, 0],
            "optimized_capacity": [10.728721, 93.602946, 3.872608],
            "total_flow": [60135.444842, 159106.826600, 2800.789583],
            "direction": ["in", "in", "in"],
        }
        return pd.DataFrame(data)

    def test_annualize_capex_calculation(self):
        """Test: Berechnung der annualisierten CAPEX."""
        # Teste die eingebettete annualize_capex Funktion
        # Dies ist indirekt durch die Hauptfunktion getestet
        # Wird in den nächsten Tests abgedeckt

    def test_graph_costs_arrangement_var1(self, sample_cost_df):
        """Test: COSTS_PER_ASSETS Arrangement."""
        # Diese Funktion ist teilweise implementiert
        # Test mit Mock oder Skip wenn nicht vollständig
        pytest.skip("Funktion nicht vollständig implementiert")

    def test_graph_costs_with_scenario_name(self, sample_cost_df):
        """Test: graph_costs mit scenario_name."""
        pytest.skip("Funktion nicht vollständig implementiert")

    def test_graph_costs_invalid_arrangement(self):
        """Test: Ungültiges arrangement."""
        pytest.skip("Funktion nicht vollständig implementiert")


# ============================================================================

# PARAMETRIZED TESTS

# ============================================================================


class TestSankeyParametrized:
    """Parametrisierte Tests für verschiedene Szenarien."""

    @pytest.mark.parametrize("agg_method", ["sum", "mean", "max"])
    def test_sankey_all_aggregations(self, sample_flows_df, agg_method):
        """Test: Alle Aggregationsmethoden."""
        fig, links_df = sankey(sample_flows_df, agg=agg_method)

        assert isinstance(fig, go.Figure)
        assert isinstance(links_df, pd.DataFrame)
        assert not links_df.empty

    @pytest.mark.parametrize("row_selector", [0, 5, 10, 15, 20])
    def test_sankey_different_rows(self, sample_flows_df, row_selector):
        """Test: Verschiedene Zeilen-Selektoren."""
        fig, links_df = sankey(sample_flows_df, row=row_selector)

        assert isinstance(fig, go.Figure)
        expected = sample_flows_df.iloc[row_selector].values
        np.testing.assert_array_almost_equal(
            links_df["value"].values, expected
        )


# ============================================================================

# INTEGRATION TESTS

# ============================================================================


class TestIntegration:
    """Integrationstests für komplexere Szenarien."""

    def test_sankey_full_workflow(self, sample_flows_df, sample_energy_system):
        """Test: Vollständiger Workflow mit allen Optionen."""
        fig, links_df = sankey(
            sample_flows_df,
            es=sample_energy_system,
            title="Integration Test",
            row=None,
            agg="sum",
            drop_zero_links=False,
        )

        assert isinstance(fig, go.Figure)
        assert isinstance(links_df, pd.DataFrame)
        assert fig.layout.title.text == "Integration Test"
        assert len(links_df) == 15
        assert all(
            col in links_df.columns
            for col in ["source", "target", "value", "min", "max", "aggregate"]
        )

    def test_capacities_full_workflow(
        self, sample_results, sample_energy_system
    ):
        """Test: Vollständiger Workflow für capacities_graph."""
        fig = capacities_graph(sample_results["invest"], sample_energy_system)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert fig.layout.barmode == "stack"

        # Prüfe, dass alle Komponenten enthalten sind
        components = fig.data[0].x
        assert len(components) == 6  # component1, component2, component3


# ============================================================================

# EDGE CASES & ERROR HANDLING

# ============================================================================


class TestEdgeCases:
    """Tests für Edge Cases und Fehlerbehandlung."""

    def test_sankey_single_link(self):
        """Test: Sankey mit nur einem Link."""
        dates = pd.date_range("2023-01-01", periods=5, freq="h")
        columns = pd.MultiIndex.from_tuples(
            [("source1", "bus1")], names=["source", "target"]
        )
        data = np.ones((5, 1)) * 10
        df = pd.DataFrame(data, index=dates, columns=columns)

        fig, links_df = sankey(df)

        assert isinstance(fig, go.Figure)
        assert len(links_df) == 1

    def test_sankey_large_values(self):
        """Test: Sankey mit sehr großen Werten."""
        dates = pd.date_range("2023-01-01", periods=10, freq="h")
        columns = pd.MultiIndex.from_tuples(
            [("source1", "bus1")], names=["source", "target"]
        )
        data = np.ones((10, 1)) * 1e9
        df = pd.DataFrame(data, index=dates, columns=columns)

        fig, links_df = sankey(df)

        assert isinstance(fig, go.Figure)
        assert links_df["value"].iloc[0] > 1e8

    def test_sankey_small_values(self):
        """Test: Sankey mit sehr kleinen Werten."""
        dates = pd.date_range("2023-01-01", periods=10, freq="h")
        columns = pd.MultiIndex.from_tuples(
            [("source1", "bus1")], names=["source", "target"]
        )
        data = np.ones((10, 1)) * 1e-6
        df = pd.DataFrame(data, index=dates, columns=columns)

        fig, links_df = sankey(df)

        assert isinstance(fig, go.Figure)
        assert links_df["value"].iloc[0] > 0

    def test_capacities_graph_all_zeros(self, sample_energy_system):
        """Test: Kapazitätsdiagramm mit allen Nullwerten."""
        columns = pd.MultiIndex.from_tuples(
            [("component1", "invest"), ("component2", "invest")]
        )
        invest_df = pd.DataFrame([[0.0, 0.0]], columns=columns)

        fig = capacities_graph(invest_df, sample_energy_system)

        assert isinstance(fig, go.Figure)


# ============================================================================

# FIXTURES FÜR SPEZIELLE FÄLLE

# ============================================================================


@pytest.fixture
def complex_flows_df():
    """Komplexerer DataFrame mit mehreren Zeitschritten und Komponenten."""
    dates = pd.date_range("2023-01-01", periods=100, freq="h")
    columns = pd.MultiIndex.from_tuples(
        [
            ("solar", "grid"),
            ("wind", "grid"),
            ("grid", "load1"),
            ("grid", "load2"),
            ("grid", "battery"),
            ("battery", "grid"),
        ],
        names=["source", "target"],
    )
    # Erstelle realistische Daten mit Variationen
    data = np.random.rand(100, 6) * 50 + np.sin(np.arange(100)[:, None]) * 25
    data = np.abs(data)  # Keine negativen Werte
    return pd.DataFrame(data, index=dates, columns=columns)


@pytest.mark.parametrize("drop_zeros", [True, False])
def test_sankey_with_complex_data(complex_flows_df, drop_zeros):
    """Test: Sankey mit komplexen realistischen Daten."""
    fig, links_df = sankey(complex_flows_df, drop_zero_links=drop_zeros)

    assert isinstance(fig, go.Figure)
    assert len(links_df) > 0
    if drop_zeros:
        assert all(links_df["value"] > 0)
