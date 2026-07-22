from __future__ import annotations

from typing import Any

import pytest

from oemof import solph
from oemof.eesyplan.components.converters.boiler import Boiler

from ._helpers import DummyProjectData
from ._helpers import assert_any_flow_has_variable_costs
from ._helpers import assert_conversion_factor
from ._helpers import assert_model_builds
from ._helpers import assert_no_none_keys
from ._helpers import assert_output_flow_capacity
from ._helpers import assert_output_flow_investment_capacity

EFFICIENCY = 0.9
INSTALLED_CAPACITY = 100.0
MAXIMUM_CAPACITY = 250.0
VARIABLE_COSTS = 7.5
CAPEX_VAR = 1000.0


@pytest.fixture
def project_data() -> DummyProjectData:
    return DummyProjectData()


@pytest.fixture
def fuel_bus() -> solph.Bus:
    return solph.Bus(label="fuel")


@pytest.fixture
def heat_bus() -> solph.Bus:
    return solph.Bus(label="heat")


def _boiler_kwargs(
    fuel_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
    **overrides: Any,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "name": "boiler_test",
        "bus_in_fuel": fuel_bus,
        "bus_out_heat": heat_bus,
        "project_data": project_data,
        "efficiency": EFFICIENCY,
        "installed_capacity": INSTALLED_CAPACITY,
        "maximum_capacity": MAXIMUM_CAPACITY,
        "optimize_cap": False,
        "capex_var": CAPEX_VAR,
        "opex_var": VARIABLE_COSTS,
    }
    kwargs.update(overrides)
    return kwargs


def test_boiler_initializes_with_expected_buses(
    fuel_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    boiler = Boiler(
        **_boiler_kwargs(
            fuel_bus=fuel_bus,
            heat_bus=heat_bus,
            project_data=project_data,
        ),
    )

    assert "boiler_test" in str(boiler.label)
    assert fuel_bus in boiler.inputs
    assert heat_bus in boiler.outputs
    assert_no_none_keys(boiler)


def test_boiler_has_expected_conversion_factor_and_variable_costs(
    fuel_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    boiler = Boiler(
        **_boiler_kwargs(
            fuel_bus=fuel_bus,
            heat_bus=heat_bus,
            project_data=project_data,
        ),
    )

    assert_conversion_factor(
        component=boiler,
        bus=heat_bus,
        expected=EFFICIENCY,
    )
    assert_any_flow_has_variable_costs(
        component=boiler,
        expected=VARIABLE_COSTS,
    )


def test_boiler_static_capacity_is_set_on_heat_output(
    fuel_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    boiler = Boiler(
        **_boiler_kwargs(
            fuel_bus=fuel_bus,
            heat_bus=heat_bus,
            project_data=project_data,
        ),
    )

    assert_output_flow_capacity(
        component=boiler,
        bus=heat_bus,
        expected=INSTALLED_CAPACITY,
    )


def test_boiler_investment_capacity_logic(
    fuel_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    boiler = Boiler(
        **_boiler_kwargs(
            fuel_bus=fuel_bus,
            heat_bus=heat_bus,
            project_data=project_data,
            optimize_cap=True,
            installed_capacity=INSTALLED_CAPACITY,
            maximum_capacity=MAXIMUM_CAPACITY,
        ),
    )

    assert_output_flow_investment_capacity(
        component=boiler,
        bus=heat_bus,
        existing=INSTALLED_CAPACITY,
        maximum=MAXIMUM_CAPACITY,
    )


@pytest.mark.parametrize(
    "invalid_efficiency",
    [-0.1, 0.0, 1.1],
)
def test_boiler_rejects_invalid_efficiency(
    fuel_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
    invalid_efficiency: Any,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        Boiler(
            **_boiler_kwargs(
                fuel_bus=fuel_bus,
                heat_bus=heat_bus,
                project_data=project_data,
                efficiency=invalid_efficiency,
            ),
        )


def test_boiler_rejects_invalid_fuel_bus(
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(TypeError):
        Boiler(
            **_boiler_kwargs(
                fuel_bus="not-a-bus",
                heat_bus=heat_bus,
                project_data=project_data,
            ),
        )


def test_boiler_rejects_invalid_optimize_cap(
    fuel_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(TypeError):
        Boiler(
            **_boiler_kwargs(
                fuel_bus=fuel_bus,
                heat_bus=heat_bus,
                project_data=project_data,
                optimize_cap="yes",
            ),
        )


def test_boiler_rejects_maximum_capacity_below_installed_capacity(
    fuel_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"maximum_capacity.*installed_capacity|installed_capacity.*maximum_capacity",
    ):
        Boiler(
            **_boiler_kwargs(
                fuel_bus=fuel_bus,
                heat_bus=heat_bus,
                project_data=project_data,
                optimize_cap=True,
                installed_capacity=100.0,
                maximum_capacity=50.0,
            ),
        )


def test_boiler_allows_none_maximum_capacity_without_none_keys(
    fuel_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    boiler = Boiler(
        **_boiler_kwargs(
            fuel_bus=fuel_bus,
            heat_bus=heat_bus,
            project_data=project_data,
            maximum_capacity=None,
        ),
    )

    assert_no_none_keys(boiler)


def test_boiler_can_be_added_to_minimal_solph_model(
    fuel_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    boiler = Boiler(
        **_boiler_kwargs(
            fuel_bus=fuel_bus,
            heat_bus=heat_bus,
            project_data=project_data,
        ),
    )

    assert_model_builds(boiler)
