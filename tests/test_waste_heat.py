"""Tests for the direct waste heat component."""

from __future__ import annotations

from typing import Any

import pytest

from oemof.eesyplan import Project
from oemof.eesyplan.components.converters.waste_heat import WasteHeatDirect
from oemof.solph import Bus
from oemof.solph import EnergySystem
from oemof.solph import Flow
from oemof.solph import Investment
from oemof.solph import Model
from oemof.solph.components import Sink
from oemof.solph.components import Source


def _nominal_capacity(flow: Flow) -> Any:
    """Return nominal capacity of a solph flow."""
    return flow.nominal_capacity


def _first(value: Any) -> float:
    """Return first scalar value from scalar or sequence-like solph data."""
    try:
        return float(value[0])
    except TypeError:
        return float(value)


def _values(value: Any, length: int) -> list[float]:
    """Return values from scalar or sequence-like solph data."""
    try:
        return [float(value[index]) for index in range(length)]
    except TypeError:
        return [float(value)] * length


@pytest.fixture
def project() -> Project:
    """Return minimal eesyplan project data."""
    return Project(
        name="Project_X",
        lifetime=20,
        tax=0,
        discount_factor=0.01,
    )


def test_initialization_sets_attributes_types_and_scaling(
    project: Project,
) -> None:
    """Test attributes, types and profile scaling."""
    raw_heat_bus = Bus(label="raw_waste_heat")
    heat_bus = Bus(label="heat")

    component = WasteHeatDirect(
        name="waste_heat",
        bus_in_heat=raw_heat_bus,
        bus_out_heat=heat_bus,
        project_data=project,
        heat_profile=[5.0, 10.0, 20.0],
        age_installed=0,
        installed_capacity=0.0,
        capex_fix=100.0,
        capex_var=500.0,
        opex_var=0.004,
        opex_fix=10.0,
        lifetime=20,
        optimize_cap=True,
        maximum_capacity=None,
        heat_cost=0.015,
        efficiency_hex=0.8,
    )

    assert str(component.label) == "waste_heat"
    assert component.name == "waste_heat"
    assert component.bus_in_heat is raw_heat_bus
    assert component.bus_out_heat is heat_bus
    assert component.project_data is project

    assert component.heat_profile == (5.0, 10.0, 20.0)
    assert component.normalized_heat_profile == pytest.approx([0.25, 0.5, 1.0])

    assert component.age_installed == 0
    assert component.installed_capacity == pytest.approx(0.0)
    assert component.capex_fix == pytest.approx(100.0)
    assert component.capex_var == pytest.approx(500.0)
    assert component.opex_var == pytest.approx(0.004)
    assert component.opex_fix == pytest.approx(10.0)
    assert component.lifetime == 20
    assert component.optimize_cap is True
    assert component.maximum_capacity is None
    assert component.heat_cost == pytest.approx(0.015)
    assert component.efficiency_hex == pytest.approx(0.8)

    assert component.raw_heat_nominal_capacity == pytest.approx(20.0)
    assert component.useful_heat_available_capacity == pytest.approx(16.0)
    assert component.investment_maximum_capacity == pytest.approx(16.0)

    input_flow = component.inputs[raw_heat_bus]
    output_flow = component.outputs[heat_bus]

    assert isinstance(input_flow, Flow)
    assert isinstance(output_flow, Flow)
    assert isinstance(output_flow.investment, Investment)


def test_solph_interfaces_match_physical_expectation(
    project: Project,
) -> None:
    """Validate nominal capacities, availability and conversion factors."""
    raw_heat_bus = Bus(label="raw_waste_heat")
    heat_bus = Bus(label="heat")

    heat_profile = [10.0, 20.0, 30.0]
    efficiency_hex = 0.75
    expected_raw_nominal_capacity = 30.0
    expected_useful_capacity = 22.5

    component = WasteHeatDirect(
        name="waste_heat",
        bus_in_heat=raw_heat_bus,
        bus_out_heat=heat_bus,
        project_data=project,
        heat_profile=heat_profile,
        installed_capacity=expected_useful_capacity,
        optimize_cap=False,
        heat_cost=0.02,
        efficiency_hex=efficiency_hex,
        opex_var=0.003,
    )

    input_flow = component.inputs[raw_heat_bus]
    output_flow = component.outputs[heat_bus]

    assert _nominal_capacity(input_flow) == pytest.approx(
        expected_raw_nominal_capacity
    )
    assert _values(input_flow.maximum, len(heat_profile)) == pytest.approx(
        [1.0 / 3.0, 2.0 / 3.0, 1.0]
    )
    assert _first(input_flow.variable_costs) == pytest.approx(0.02)

    assert _nominal_capacity(output_flow) == pytest.approx(
        expected_useful_capacity
    )
    assert _first(output_flow.variable_costs) == pytest.approx(0.003)

    available_useful_heat = [
        expected_raw_nominal_capacity * availability * efficiency_hex
        for availability in _values(input_flow.maximum, len(heat_profile))
    ]
    assert available_useful_heat == pytest.approx([7.5, 15.0, 22.5])

    conversion_factors = component.conversion_factors
    assert _first(conversion_factors[heat_bus]) == pytest.approx(
        efficiency_hex
    )


def test_component_compiles_in_minimal_solph_model(
    project: Project,
) -> None:
    """Test integration in a minimal solph energy system."""
    pd = pytest.importorskip("pandas")

    raw_heat_profile = [10.0, 20.0, 30.0]
    efficiency_hex = 0.8

    demand_profile = [4.0, 8.0, 12.0]
    demand_nominal_capacity = max(demand_profile)
    demand_fix = [value / demand_nominal_capacity for value in demand_profile]

    timeindex = pd.date_range(
        "2026-01-01",
        periods=len(raw_heat_profile),
        freq="h",
    )

    energy_system = EnergySystem(
        timeindex=timeindex,
        infer_last_interval=True,
    )

    raw_heat_bus = Bus(label="raw_waste_heat")
    heat_bus = Bus(label="heat")

    raw_heat_source = Source(
        label="raw_waste_heat_source",
        outputs={
            raw_heat_bus: Flow(
                nominal_capacity=max(raw_heat_profile),
            )
        },
    )

    waste_heat = WasteHeatDirect(
        name="waste_heat",
        bus_in_heat=raw_heat_bus,
        bus_out_heat=heat_bus,
        project_data=project,
        heat_profile=raw_heat_profile,
        installed_capacity=0.0,
        capex_var=500.0,
        opex_var=0.001,
        opex_fix=5.0,
        lifetime=20,
        optimize_cap=True,
        maximum_capacity=None,
        heat_cost=0.0,
        efficiency_hex=efficiency_hex,
    )

    heat_demand = Sink(
        label="heat_demand",
        inputs={
            heat_bus: Flow(
                fix=demand_fix,
                nominal_capacity=demand_nominal_capacity,
            )
        },
    )

    energy_system.add(
        raw_heat_bus,
        heat_bus,
        raw_heat_source,
        waste_heat,
        heat_demand,
    )

    model = Model(energy_system)

    assert isinstance(model, Model)
    assert hasattr(model, "objective")
