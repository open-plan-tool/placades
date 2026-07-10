import math
from typing import Any

import pandas as pd
import pytest

from oemof.eesyplan import Project
from oemof.eesyplan.components.converters.ElectricalTransformator import (
    ElectricalTransformator,
)
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
def electricity_bus_in() -> Bus:
    """Create an input electricity bus."""
    return Bus(label="electricity_bus_in")


@pytest.fixture
def electricity_bus_out() -> Bus:
    """Create an output electricity bus."""
    return Bus(label="electricity_bus_out")


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


def test_electrical_transformator_initializes_with_default_values(
    project: Project,
    electricity_bus_in: Bus,
    electricity_bus_out: Bus,
) -> None:
    """Test initialization with default parameter values."""
    transformator = ElectricalTransformator(
        name="transformator",
        bus_in_electricity=electricity_bus_in,
        bus_out_electricity=electricity_bus_out,
        project_data=project,
    )

    assert transformator.label == "transformator"
    assert transformator.name == "transformator"
    assert transformator.age_installed == 0
    assert transformator.installed_capacity == 0
    assert transformator.capex_var == 1000
    assert transformator.capex_fix == 0
    assert transformator.opex_fix == 10
    assert transformator.opex_var == 0
    assert transformator.lifetime == 20
    assert transformator.efficiency == 0.3
    assert transformator.maximum_capacity == math.inf


def test_electrical_transformator_initializes_with_custom_values(
    project: Project,
    electricity_bus_in: Bus,
    electricity_bus_out: Bus,
) -> None:
    """Test initialization with custom parameter values."""
    transformator = ElectricalTransformator(
        name="custom_transformator",
        bus_in_electricity=electricity_bus_in,
        bus_out_electricity=electricity_bus_out,
        project_data=project,
        age_installed=3,
        installed_capacity=5,
        capex_var=1200,
        capex_fix=100,
        opex_fix=25,
        opex_var=4,
        lifetime=15,
        efficiency=0.95,
        maximum_capacity=30,
        optimize_cap=False,
    )

    assert transformator.label == "custom_transformator"
    assert transformator.name == "custom_transformator"
    assert transformator.age_installed == 3
    assert transformator.installed_capacity == 5
    assert transformator.capex_var == 1200
    assert transformator.capex_fix == 100
    assert transformator.opex_fix == 25
    assert transformator.opex_var == 4
    assert transformator.lifetime == 15
    assert transformator.efficiency == 0.95
    assert transformator.maximum_capacity == 30


def test_electrical_transformator_sets_inputs_and_outputs(
    project: Project,
    electricity_bus_in: Bus,
    electricity_bus_out: Bus,
) -> None:
    """Test input and output bus setup."""
    transformator = ElectricalTransformator(
        name="transformator",
        bus_in_electricity=electricity_bus_in,
        bus_out_electricity=electricity_bus_out,
        project_data=project,
    )

    assert electricity_bus_in in transformator.inputs
    assert electricity_bus_out in transformator.outputs
    assert len(transformator.inputs) == 1
    assert len(transformator.outputs) == 1


def test_electrical_transformator_sets_conversion_factor_and_variable_costs(
    project: Project,
    electricity_bus_in: Bus,
    electricity_bus_out: Bus,
) -> None:
    """Test conversion factor and variable output costs."""
    transformator = ElectricalTransformator(
        name="transformator",
        bus_in_electricity=electricity_bus_in,
        bus_out_electricity=electricity_bus_out,
        project_data=project,
        efficiency=0.91,
        opex_var=7,
        installed_capacity=10,
        optimize_cap=False,
    )

    output_flow = transformator.outputs[electricity_bus_out]

    assert _scalar_value(
        transformator.conversion_factors[electricity_bus_out]
    ) == pytest.approx(0.91)
    assert _scalar_value(output_flow.variable_costs) == pytest.approx(7)


def test_electrical_transformator_uses_fixed_capacity_when_not_optimized(
    project: Project,
    electricity_bus_in: Bus,
    electricity_bus_out: Bus,
) -> None:
    """Test fixed installed capacity when capacity optimization is disabled."""
    transformator = ElectricalTransformator(
        name="transformator",
        bus_in_electricity=electricity_bus_in,
        bus_out_electricity=electricity_bus_out,
        project_data=project,
        installed_capacity=7,
        optimize_cap=False,
    )

    output_flow = transformator.outputs[electricity_bus_out]

    assert _scalar_value(_nominal_capacity(output_flow)) == pytest.approx(7)


def test_electrical_transformator_uses_investment_when_capacity_is_optimized(
    project: Project,
    electricity_bus_in: Bus,
    electricity_bus_out: Bus,
) -> None:
    """Test investment object when capacity optimization is enabled."""
    transformator = ElectricalTransformator(
        name="transformator",
        bus_in_electricity=electricity_bus_in,
        bus_out_electricity=electricity_bus_out,
        project_data=project,
        installed_capacity=3,
        maximum_capacity=30,
        optimize_cap=True,
    )

    output_flow = transformator.outputs[electricity_bus_out]
    investment = _investment(output_flow)

    assert investment is not None
    assert investment.__class__.__name__ == "Investment"

    if hasattr(investment, "existing"):
        assert _scalar_value(investment.existing) == pytest.approx(3)

    if hasattr(investment, "maximum"):
        assert _scalar_value(investment.maximum) == pytest.approx(30)


def test_electrical_transformator_builds_minimal_energy_system(
    project: Project,
    electricity_bus_in: Bus,
    electricity_bus_out: Bus,
) -> None:
    """Test that the component can be used in a minimal solph model."""
    timeindex = pd.date_range("2024-01-01", periods=3, freq="h")
    energy_system = EnergySystem(
        timeindex=timeindex,
        infer_last_interval=True,
    )

    electricity_source = Source(
        label="electricity_source",
        outputs={electricity_bus_in: Flow(variable_costs=0)},
    )
    electricity_demand = Sink(
        label="electricity_demand",
        inputs={
            electricity_bus_out: Flow(
                fix=[1, 1, 1],
                nominal_capacity=2,
            )
        },
    )
    transformator = ElectricalTransformator(
        name="transformator",
        bus_in_electricity=electricity_bus_in,
        bus_out_electricity=electricity_bus_out,
        project_data=project,
        installed_capacity=10,
        optimize_cap=False,
        efficiency=0.9,
    )

    energy_system.add(
        electricity_bus_in,
        electricity_bus_out,
        electricity_source,
        electricity_demand,
        transformator,
    )

    model = Model(energy_system)

    assert model is not None
