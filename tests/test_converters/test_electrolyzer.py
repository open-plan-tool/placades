import math
from typing import Any

import pandas as pd
import pytest

from oemof.eesyplan import Project
from oemof.eesyplan.components.converters.electrolyzer import Electrolyzer
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
def electricity_bus() -> Bus:
    """Create an electricity bus."""
    return Bus(label="electricity_bus")


@pytest.fixture
def h2_bus() -> Bus:
    """Create a hydrogen bus."""
    return Bus(label="h2_bus")


@pytest.fixture
def heat_bus() -> Bus:
    """Create a heat bus."""
    return Bus(label="heat_bus")


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


def test_electrolyzer_initializes_with_default_values(
    project: Project,
    electricity_bus: Bus,
    h2_bus: Bus,
) -> None:
    """Test initialization with default parameter values."""
    electrolyzer = Electrolyzer(
        name="electrolyzer",
        bus_in_electricity=electricity_bus,
        bus_out_h2=h2_bus,
        project_data=project,
    )

    assert electrolyzer.label == "electrolyzer"
    assert electrolyzer.name == "electrolyzer"
    assert electrolyzer.age_installed == 0
    assert electrolyzer.installed_capacity == 0
    assert electrolyzer.capex_var == 1000
    assert electrolyzer.capex_fix == 0
    assert electrolyzer.opex_fix == 10
    assert electrolyzer.opex_var == 0
    assert electrolyzer.lifetime == 20
    assert electrolyzer.maximum_capacity == math.inf
    assert electrolyzer.efficiency == 0.3
    assert electrolyzer.efficiency_heat == 0.6


def test_electrolyzer_initializes_with_custom_values(
    project: Project,
    electricity_bus: Bus,
    h2_bus: Bus,
    heat_bus: Bus,
) -> None:
    """Test initialization with custom parameter values."""
    electrolyzer = Electrolyzer(
        name="custom_electrolyzer",
        bus_in_electricity=electricity_bus,
        bus_out_h2=h2_bus,
        bus_out_heat=heat_bus,
        project_data=project,
        age_installed=4,
        installed_capacity=6,
        capex_var=1300,
        capex_fix=200,
        opex_fix=30,
        opex_var=5,
        lifetime=18,
        efficiency=0.72,
        efficiency_heat=0.2,
        maximum_capacity=40,
        optimize_cap=False,
    )

    assert electrolyzer.label == "custom_electrolyzer"
    assert electrolyzer.name == "custom_electrolyzer"
    assert electrolyzer.age_installed == 4
    assert electrolyzer.installed_capacity == 6
    assert electrolyzer.capex_var == 1300
    assert electrolyzer.capex_fix == 200
    assert electrolyzer.opex_fix == 30
    assert electrolyzer.opex_var == 5
    assert electrolyzer.lifetime == 18
    assert electrolyzer.efficiency == 0.72
    assert electrolyzer.efficiency_heat == 0.2
    assert electrolyzer.maximum_capacity == 40


def test_electrolyzer_without_heat_sets_no_none_keys(
    project,
    electricity_bus,
    h2_bus,
):
    electrolyzer = Electrolyzer(
        name="electrolyzer",
        bus_in_electricity=electricity_bus,
        bus_out_h2=h2_bus,
        project_data=project,
        bus_out_heat=None,
    )

    assert None not in electrolyzer.outputs
    assert None not in electrolyzer.conversion_factors
    assert h2_bus in electrolyzer.outputs
    assert h2_bus in electrolyzer.conversion_factors


def test_electrolyzer_without_heat_sets_inputs_outputs_and_conversion_factor(
    project: Project,
    electricity_bus: Bus,
    h2_bus: Bus,
) -> None:
    """Test mathematical interface without heat output."""
    electrolyzer = Electrolyzer(
        name="electrolyzer",
        bus_in_electricity=electricity_bus,
        bus_out_h2=h2_bus,
        project_data=project,
        installed_capacity=6,
        optimize_cap=False,
        efficiency=0.7,
        opex_var=4,
    )

    h2_output_flow = electrolyzer.outputs[h2_bus]

    assert electricity_bus in electrolyzer.inputs
    assert h2_bus in electrolyzer.outputs
    assert len(electrolyzer.inputs) == 1
    assert len(electrolyzer.outputs) == 1

    assert _scalar_value(
        electrolyzer.conversion_factors[h2_bus]
    ) == pytest.approx(0.7)
    assert _scalar_value(h2_output_flow.variable_costs) == pytest.approx(4)
    assert _scalar_value(_nominal_capacity(h2_output_flow)) == pytest.approx(6)


def test_electrolyzer_with_heat_sets_inputs_outputs_and_conversion_factors(
    project: Project,
    electricity_bus: Bus,
    h2_bus: Bus,
    heat_bus: Bus,
) -> None:
    """Test mathematical interface with heat output."""
    electrolyzer = Electrolyzer(
        name="electrolyzer",
        bus_in_electricity=electricity_bus,
        bus_out_h2=h2_bus,
        bus_out_heat=heat_bus,
        project_data=project,
        installed_capacity=5,
        optimize_cap=False,
        efficiency=0.7,
        efficiency_heat=0.2,
        opex_var=3,
    )

    h2_output_flow = electrolyzer.outputs[h2_bus]

    assert electricity_bus in electrolyzer.inputs
    assert h2_bus in electrolyzer.outputs
    assert heat_bus in electrolyzer.outputs
    assert len(electrolyzer.inputs) == 1
    assert len(electrolyzer.outputs) == 2

    assert _scalar_value(
        electrolyzer.conversion_factors[h2_bus]
    ) == pytest.approx(0.7)
    assert _scalar_value(
        electrolyzer.conversion_factors[heat_bus]
    ) == pytest.approx(0.2)

    assert _scalar_value(h2_output_flow.variable_costs) == pytest.approx(3)
    assert _scalar_value(_nominal_capacity(h2_output_flow)) == pytest.approx(5)


def test_electrolyzer_uses_fixed_capacity_when_not_optimized(
    project: Project,
    electricity_bus: Bus,
    h2_bus: Bus,
) -> None:
    """Test fixed installed capacity when capacity optimization is disabled."""
    electrolyzer = Electrolyzer(
        name="electrolyzer",
        bus_in_electricity=electricity_bus,
        bus_out_h2=h2_bus,
        project_data=project,
        installed_capacity=8,
        optimize_cap=False,
    )

    h2_output_flow = electrolyzer.outputs[h2_bus]

    assert _scalar_value(_nominal_capacity(h2_output_flow)) == pytest.approx(8)


def test_electrolyzer_uses_investment_when_capacity_is_optimized(
    project: Project,
    electricity_bus: Bus,
    h2_bus: Bus,
) -> None:
    """Test investment object when capacity optimization is enabled."""
    electrolyzer = Electrolyzer(
        name="electrolyzer",
        bus_in_electricity=electricity_bus,
        bus_out_h2=h2_bus,
        project_data=project,
        installed_capacity=2,
        maximum_capacity=25,
        optimize_cap=True,
    )

    h2_output_flow = electrolyzer.outputs[h2_bus]
    investment = _investment(h2_output_flow)

    assert investment is not None
    assert investment.__class__.__name__ == "Investment"

    if hasattr(investment, "existing"):
        assert _scalar_value(investment.existing) == pytest.approx(2)

    if hasattr(investment, "maximum"):
        assert _scalar_value(investment.maximum) == pytest.approx(25)


def test_electrolyzer_without_heat_builds_minimal_energy_system(
    project: Project,
    electricity_bus: Bus,
    h2_bus: Bus,
) -> None:
    """Test model creation without heat output."""
    timeindex = pd.date_range("2024-01-01", periods=3, freq="h")
    energy_system = EnergySystem(
        timeindex=timeindex,
        infer_last_interval=True,
    )

    electricity_source = Source(
        label="electricity_source",
        outputs={electricity_bus: Flow(variable_costs=0)},
    )
    h2_demand = Sink(
        label="h2_demand",
        inputs={
            h2_bus: Flow(
                fix=[1, 1, 1],
                nominal_capacity=2,
            )
        },
    )
    electrolyzer = Electrolyzer(
        name="electrolyzer",
        bus_in_electricity=electricity_bus,
        bus_out_h2=h2_bus,
        project_data=project,
        installed_capacity=10,
        optimize_cap=False,
        efficiency=0.7,
    )

    energy_system.add(
        electricity_bus,
        h2_bus,
        electricity_source,
        h2_demand,
        electrolyzer,
    )

    model = Model(energy_system)

    assert model is not None


def test_electrolyzer_with_heat_builds_minimal_energy_system(
    project: Project,
    electricity_bus: Bus,
    h2_bus: Bus,
    heat_bus: Bus,
) -> None:
    """Test model creation with heat output."""
    timeindex = pd.date_range("2024-01-01", periods=3, freq="h")
    energy_system = EnergySystem(
        timeindex=timeindex,
        infer_last_interval=True,
    )

    electricity_source = Source(
        label="electricity_source",
        outputs={electricity_bus: Flow(variable_costs=0)},
    )
    h2_demand = Sink(
        label="h2_demand",
        inputs={
            h2_bus: Flow(
                fix=[1, 1, 1],
                nominal_capacity=2,
            )
        },
    )
    heat_excess = Sink(
        label="heat_excess",
        inputs={heat_bus: Flow(variable_costs=0)},
    )
    electrolyzer = Electrolyzer(
        name="electrolyzer",
        bus_in_electricity=electricity_bus,
        bus_out_h2=h2_bus,
        bus_out_heat=heat_bus,
        project_data=project,
        installed_capacity=10,
        optimize_cap=False,
        efficiency=0.7,
        efficiency_heat=0.2,
    )

    energy_system.add(
        electricity_bus,
        h2_bus,
        heat_bus,
        electricity_source,
        h2_demand,
        heat_excess,
        electrolyzer,
    )

    model = Model(energy_system)

    assert model is not None
