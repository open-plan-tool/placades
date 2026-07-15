from __future__ import annotations

from typing import Any

import pytest
from _helpers import DummyProjectData
from _helpers import assert_any_flow_has_variable_costs
from _helpers import assert_conversion_factor
from _helpers import assert_model_builds
from _helpers import assert_no_none_keys
from _helpers import assert_output_flow_capacity
from _helpers import assert_output_flow_investment_capacity

from oemof import solph
from oemof.eesyplan.components.converters.DieselGenerator import (
    DieselGenerator,
)

EFFICIENCY = 0.38
INSTALLED_CAPACITY = 80.0
MAXIMUM_CAPACITY = 200.0
VARIABLE_COSTS = 12.0
CAPEX_VAR = 1000.0


@pytest.fixture
def project_data() -> DummyProjectData:
    return DummyProjectData()


@pytest.fixture
def fuel_bus() -> solph.Bus:
    return solph.Bus(label="diesel")


@pytest.fixture
def electricity_bus() -> solph.Bus:
    return solph.Bus(label="electricity")


def _diesel_generator_kwargs(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    project_data: Any,
    **overrides: Any,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "name": "diesel_generator_test",
        "bus_in_fuel": fuel_bus,
        "bus_out_electricity": electricity_bus,
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


def test_diesel_generator_initializes_with_expected_buses(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    project_data: Any,
) -> None:
    diesel_generator = DieselGenerator(
        **_diesel_generator_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            project_data=project_data,
        ),
    )

    assert "diesel_generator_test" in str(diesel_generator.label)
    assert fuel_bus in diesel_generator.inputs
    assert electricity_bus in diesel_generator.outputs
    assert_no_none_keys(diesel_generator)


def test_diesel_generator_has_expected_conversion_factor_and_variable_costs(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    project_data: Any,
) -> None:
    diesel_generator = DieselGenerator(
        **_diesel_generator_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            project_data=project_data,
        ),
    )

    assert_conversion_factor(
        component=diesel_generator,
        bus=electricity_bus,
        expected=EFFICIENCY,
    )
    assert_any_flow_has_variable_costs(
        component=diesel_generator,
        expected=VARIABLE_COSTS,
    )


def test_diesel_generator_static_capacity_is_set_on_electricity_output(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    project_data: Any,
) -> None:
    diesel_generator = DieselGenerator(
        **_diesel_generator_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            project_data=project_data,
        ),
    )

    assert_output_flow_capacity(
        component=diesel_generator,
        bus=electricity_bus,
        expected=INSTALLED_CAPACITY,
    )


def test_diesel_generator_investment_capacity_logic(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    project_data: Any,
) -> None:
    diesel_generator = DieselGenerator(
        **_diesel_generator_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            project_data=project_data,
            optimize_cap=True,
            installed_capacity=INSTALLED_CAPACITY,
            maximum_capacity=MAXIMUM_CAPACITY,
        ),
    )

    assert_output_flow_investment_capacity(
        component=diesel_generator,
        bus=electricity_bus,
        existing=INSTALLED_CAPACITY,
        maximum=MAXIMUM_CAPACITY,
    )


@pytest.mark.parametrize(
    "invalid_efficiency",
    [-0.1, 0.0, 1.1],
)
def test_diesel_generator_rejects_invalid_efficiency(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    project_data: Any,
    invalid_efficiency: Any,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        DieselGenerator(
            **_diesel_generator_kwargs(
                fuel_bus=fuel_bus,
                electricity_bus=electricity_bus,
                project_data=project_data,
                efficiency=invalid_efficiency,
            ),
        )


def test_diesel_generator_rejects_invalid_fuel_bus(
    electricity_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(TypeError):
        DieselGenerator(
            **_diesel_generator_kwargs(
                fuel_bus="not-a-bus",
                electricity_bus=electricity_bus,
                project_data=project_data,
            ),
        )


def test_diesel_generator_rejects_invalid_optimize_cap(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(TypeError):
        DieselGenerator(
            **_diesel_generator_kwargs(
                fuel_bus=fuel_bus,
                electricity_bus=electricity_bus,
                project_data=project_data,
                optimize_cap="yes",
            ),
        )


def test_diesel_generator_rejects_maximum_capacity_below_installed_capacity(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"maximum_capacity.*installed_capacity|installed_capacity.*maximum_capacity",
    ):
        DieselGenerator(
            **_diesel_generator_kwargs(
                fuel_bus=fuel_bus,
                electricity_bus=electricity_bus,
                project_data=project_data,
                optimize_cap=True,
                installed_capacity=100.0,
                maximum_capacity=50.0,
            ),
        )


def test_diesel_generator_can_be_added_to_minimal_solph_model(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    project_data: Any,
) -> None:
    diesel_generator = DieselGenerator(
        **_diesel_generator_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            project_data=project_data,
        ),
    )

    assert_model_builds(diesel_generator)
