import pytest
from oemof.solph import EnergySystem
from oemof.solph import create_time_index
from oemof.solph.buses import Bus
from oemof.solph.components import Source

from placades import PV


class TestPV:
    """Test suite for the PV facade class."""

    @pytest.fixture
    def pv_params(self):
        """Standard parameters for PV initialization."""
        return {
            "label": "test_pv",
            "el_bus": Bus(label="TestBus"),
            "peak_capacity": 100,
            "normalised_output": [0.1, 0.5, 0.8, 0.3],
        }

    @pytest.fixture
    def energysystem(self):
        """Standard parameters for PV initialization."""
        return EnergySystem(
            timeindex=create_time_index(2012, number=4),
            infer_last_interval=False,
        )

    def test_add_function(self, energysystem, pv_params):
        energysystem.add(PV(**pv_params))
        test_flows = energysystem.flows()
        assert list(test_flows[list(test_flows.keys())[0]].fix) == [
            0.1,
            0.5,
            0.8,
            0.3,
        ]
        assert len(energysystem.flows()) == 1
        nodes = [type(n) for n in energysystem.nodes]
        assert PV in nodes
        assert Source in nodes

    def test_init_basic(self, pv_params):
        """Test basic initialization of PV class."""
        pv = PV(**pv_params)

        assert pv.label.label == "test_pv"
        assert pv.el_bus == pv_params["el_bus"]
        assert pv.el_bus.label == "TestBus"
        assert pv.peak_capacity == 100
        assert pv.normalised_output == [0.1, 0.5, 0.8, 0.3]

    def test_init_facade_type(self, pv_params):
        """Test that facade_type is set correctly."""
        pv = PV(**pv_params)
        assert pv.facade_type == PV

    def test_peak_capacity_zero(self):
        """Test initialization with zero peak capacity."""
        el_bus = Bus(label="ZeroBus")
        pv = PV(
            label="zero_pv",
            el_bus=el_bus,
            peak_capacity=0,
            normalised_output=[0.0, 0.0],
        )
        assert pv.peak_capacity == 0
        assert pv.el_bus.label == "ZeroBus"

    def test_empty_normalised_output(self):
        """Test initialization with empty normalised output."""
        el_bus = Bus(label="EmptyBus")
        pv = PV(
            label="empty_pv",
            el_bus=el_bus,
            peak_capacity=100,
            normalised_output=[],
        )
        assert pv.normalised_output == []
        assert pv.el_bus.label == "EmptyBus"

    def test_single_value_normalised_output(self):
        """Test initialization with single value normalised output."""
        el_bus = Bus(label="SingleBus")
        pv = PV(
            label="single_pv",
            el_bus=el_bus,
            peak_capacity=50,
            normalised_output=[0.7],
        )
        assert pv.normalised_output == [0.7]
        assert pv.el_bus.label == "SingleBus"

    @pytest.mark.parametrize(
        "peak_capacity,normalised_output,bus_label",
        [
            (100, [0.1, 0.5, 0.8], "Bus1"),
            (250, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0], "Bus2"),
            (75, [0.3], "Bus3"),
            (0, [], "Bus4"),
        ],
    )
    def test_various_parameter_combinations(
        self, peak_capacity, normalised_output, bus_label
    ):
        """Test various combinations of parameters."""
        el_bus = Bus(label=bus_label)
        pv = PV(
            label="param_test",
            el_bus=el_bus,
            peak_capacity=peak_capacity,
            normalised_output=normalised_output,
        )

        assert pv.peak_capacity == peak_capacity
        assert pv.normalised_output == normalised_output
        assert pv.el_bus.label == bus_label

    def test_negative_peak_capacity(self):
        """Test behavior with negative peak capacity."""
        el_bus = Bus(label="NegativeBus")
        pv = PV(
            label="negative_pv",
            el_bus=el_bus,
            peak_capacity=-100,
            normalised_output=[0.1, 0.2],
        )
        assert pv.peak_capacity == -100
        assert pv.el_bus.label == "NegativeBus"

    def test_inheritance_from_facade(self, pv_params):
        """Test that PV correctly inherits from Facade."""
        from oemof.solph import Facade

        pv = PV(**pv_params)
        assert isinstance(pv, Facade)

    def test_bus_object_properties(self, pv_params):
        """Test that the bus object is correctly handled."""
        pv = PV(
            label="bus_test",
            el_bus=pv_params["el_bus"],
            peak_capacity=120,
            normalised_output=[0.2, 0.4, 0.6],
        )

        # Test bus is correctly assigned
        assert pv.el_bus is pv_params["el_bus"]
        assert isinstance(pv.el_bus, Bus)
        assert pv.el_bus.label == "TestBus"


class TestPVIntegration:
    """Integration tests for PV class."""

    @pytest.fixture
    def complete_pv_setup(self):
        """Complete PV setup for integration testing."""
        bus = Bus(label="IntegrationBus")
        pv = PV(
            label="integration_pv",
            el_bus=bus,
            peak_capacity=150,
            normalised_output=[0.0, 0.3, 0.7, 0.5, 0.1],
        )
        return pv, bus

    def test_multiple_pv_instances_different_buses(self):
        """Test creating multiple PV instances with different buses."""
        bus1 = Bus(label="Bus1")
        bus2 = Bus(label="Bus2")

        pv1 = PV(
            label="pv1",
            el_bus=bus1,
            peak_capacity=100,
            normalised_output=[0.1, 0.2],
        )

        pv2 = PV(
            label="pv2",
            el_bus=bus2,
            peak_capacity=200,
            normalised_output=[0.3, 0.4],
        )

        # Verify they are independent
        assert pv1.el_bus is not pv2.el_bus
        assert pv1.el_bus.label == "Bus1"
        assert pv2.el_bus.label == "Bus2"
        assert pv1.peak_capacity != pv2.peak_capacity

    def test_same_bus_multiple_pv_instances(self):
        """Test creating multiple PV instances with the same bus."""
        shared_bus = Bus(label="SharedBus")

        pv1 = PV(
            label="pv1",
            el_bus=shared_bus,
            peak_capacity=100,
            normalised_output=[0.1, 0.2],
        )

        pv2 = PV(
            label="pv2",
            el_bus=shared_bus,
            peak_capacity=150,
            normalised_output=[0.3, 0.4],
        )

        # Verify they share the same bus
        assert pv1.el_bus is pv2.el_bus
        assert pv1.el_bus.label == "SharedBus"
        assert pv2.el_bus.label == "SharedBus"
