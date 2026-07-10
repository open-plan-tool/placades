import math
from typing import Any

import pandas as pd
import pytest

from oemof.eesyplan import Project
from oemof.eesyplan.components.converters.FuelCell import FuelCell
from oemof.solph import Bus
from oemof.solph import EnergySystem
from oemof.solph import Flow
from oemof.solph import Model
from oemof.solph.components import Sink
from oemof.solph.components import Source


@pytest.fixture
def project() -> Project:
    """Create a minimal project fixture."""
    return Project(
        name="test_project",
        lifetime=20,
        tax=0,
        discount_factor=0.01,
    )


@pytest.fixture
def h2_bus() -> Bus:
    """Create a hydrogen bus."""
    return Bus(label="h2_bus")


@pytest.fixture
def electricity_bus() -> Bus:
    """Create an electricity bus."""
    return Bus(label="electricity_bus")


def _investment(flow: Flow) -> Any:
    """Return investment object independent of solph version."""
    investment = getattr(flow, "investment", None)

    if investment is not None:
        return investment

    nominal_capacity = _nominal_capacity(flow)

    if nominal_capacity.__class__.__name__ == "Investment":
        return nominal_capacity

    return None


def _scalar_value(value: Any) -> Any:
    """Return a scalar value from solph sequence-like objects."""
    if hasattr(value, "_value"):
        return value._value

    if hasattr(value, "value") and not callable(value.value):
        return value.value

    try:
        return value[0]
    except (TypeError, KeyError, IndexError):
        return value


def _nominal_capacity(flow: Flow) -> Any:
    """Return nominal capacity independent of solph version."""
    if hasattr(flow, "nominal_capacity"):
        return flow.nominal_capacity

    return flow.nominal_value


def test_fuel_cell_initializes_with_default_values(
    project: Project,
    h2_bus: Bus,
    electricity_bus: Bus,
) -> None:
    """Test initialization with default parameter values."""
    fuel_cell = FuelCell(
        name="fuel_cell",
        bus_in_h2=h2_bus,
        bus_out_electricity=electricity_bus,
        project_data=project,
    )

    assert fuel_cell.label == "fuel_cell"
    assert fuel_cell.name == "fuel_cell"
    assert fuel_cell.age_installed == 0
    assert fuel_cell.installed_capacity == 0
    assert fuel_cell.capex_var == 1000
    assert fuel_cell.capex_fix == 0
    assert fuel_cell.opex_fix == 10
    assert fuel_cell.opex_var == 0
    assert fuel_cell.lifetime == 20
    assert fuel_cell.efficiency == 0.8
    assert fuel_cell.maximum_capacity == math.inf


def test_fuel_cell_initializes_with_custom_values(
    project: Project,
    h2_bus: Bus,
    electricity_bus: Bus,
) -> None:
    """Test initialization with custom parameter values."""
    fuel_cell = FuelCell(
        name="custom_fuel_cell",
        bus_in_h2=h2_bus,
        bus_out_electricity=electricity_bus,
        project_data=project,
        age_installed=5,
        installed_capacity=9,
        capex_var=1400,
        capex_fix=300,
        opex_fix=35,
        opex_var=6,
        lifetime=16,
        efficiency=0.55,
        maximum_capacity=50,
        optimize_cap=False,
    )

    assert fuel_cell.label == "custom_fuel_cell"
    assert fuel_cell.name == "custom_fuel_cell"
    assert fuel_cell.age_installed == 5
    assert fuel_cell.installed_capacity == 9
    assert fuel_cell.capex_var == 1400
    assert fuel_cell.capex_fix == 300
    assert fuel_cell.opex_fix == 35
    assert fuel_cell.opex_var == 6
    assert fuel_cell.lifetime == 16
    assert fuel_cell.efficiency == 0.55
    assert fuel_cell.maximum_capacity == 50


def test_fuel_cell_sets_inputs_and_outputs(
    project: Project,
    h2_bus: Bus,
    electricity_bus: Bus,
) -> None:
    """Test input and output bus setup."""
    fuel_cell = FuelCell(
        name="fuel_cell",
        bus_in_h2=h2_bus,
        bus_out_electricity=electricity_bus,
        project_data=project,
    )

    assert h2_bus in fuel_cell.inputs
    assert electricity_bus in fuel_cell.outputs
    assert len(fuel_cell.inputs) == 1
    assert len(fuel_cell.outputs) == 1


def test_fuel_cell_sets_conversion_factor_and_variable_costs(
    project: Project,
    h2_bus: Bus,
    electricity_bus: Bus,
) -> None:
    """Test conversion factor and variable output costs."""
    fuel_cell = FuelCell(
        name="fuel_cell",
        bus_in_h2=h2_bus,
        bus_out_electricity=electricity_bus,
        project_data=project,
        installed_capacity=10,
        optimize_cap=False,
        efficiency=0.58,
        opex_var=4,
    )

    electricity_output_flow = fuel_cell.outputs[electricity_bus]

    assert _scalar_value(
        fuel_cell.conversion_factors[electricity_bus]
    ) == pytest.approx(0.58)
    assert _scalar_value(
        electricity_output_flow.variable_costs
    ) == pytest.approx(4)


def test_fuel_cell_uses_fixed_capacity_when_not_optimized(
    project: Project,
    h2_bus: Bus,
    electricity_bus: Bus,
) -> None:
    """Test fixed installed capacity when capacity optimization is disabled."""
    fuel_cell = FuelCell(
        name="fuel_cell",
        bus_in_h2=h2_bus,
        bus_out_electricity=electricity_bus,
        project_data=project,
        installed_capacity=5,
        optimize_cap=False,
    )

    electricity_output_flow = fuel_cell.outputs[electricity_bus]

    assert _scalar_value(
        _nominal_capacity(electricity_output_flow)
    ) == pytest.approx(5)


def test_fuel_cell_uses_investment_when_capacity_is_optimized(
    project: Project,
    h2_bus: Bus,
    electricity_bus: Bus,
) -> None:
    """Test investment object when capacity optimization is enabled."""
    fuel_cell = FuelCell(
        name="fuel_cell",
        bus_in_h2=h2_bus,
        bus_out_electricity=electricity_bus,
        project_data=project,
        installed_capacity=2,
        maximum_capacity=20,
        optimize_cap=True,
    )

    electricity_output_flow = fuel_cell.outputs[electricity_bus]
    investment = _investment(electricity_output_flow)

    assert investment is not None
    assert investment.__class__.__name__ == "Investment"

    if hasattr(investment, "existing"):
        assert _scalar_value(investment.existing) == pytest.approx(2)

    if hasattr(investment, "maximum"):
        assert _scalar_value(investment.maximum) == pytest.approx(20)


def test_fuel_cell_builds_minimal_energy_system(
    project: Project,
    h2_bus: Bus,
    electricity_bus: Bus,
) -> None:
    """Test that the component can be used in a minimal solph model."""
    timeindex = pd.date_range("2024-01-01", periods=3, freq="h")
    energy_system = EnergySystem(
        timeindex=timeindex,
        infer_last_interval=True,
    )

    h2_source = Source(
        label="h2_source",
        outputs={h2_bus: Flow(variable_costs=0)},
    )
    electricity_demand = Sink(
        label="electricity_demand",
        inputs={
            electricity_bus: Flow(
                fix=[1, 1, 1],
                nominal_capacity=2,
            )
        },
    )
    fuel_cell = FuelCell(
        name="fuel_cell",
        bus_in_h2=h2_bus,
        bus_out_electricity=electricity_bus,
        project_data=project,
        installed_capacity=10,
        optimize_cap=False,
        efficiency=0.5,
    )

    energy_system.add(
        h2_bus,
        electricity_bus,
        h2_source,
        electricity_demand,
        fuel_cell,
    )

    model = Model(energy_system)

    assert model is not None
