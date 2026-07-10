from __future__ import annotations

from typing import Any

import pytest
from _helpers import DummyProjectData
from _helpers import assert_any_flow_has_capacity
from _helpers import assert_any_flow_has_investment_capacity
from _helpers import assert_any_flow_has_variable_costs
from _helpers import assert_conversion_factor
from _helpers import assert_model_builds
from _helpers import assert_no_none_keys

from oemof import solph
from oemof.eesyplan.components.converters.ChpVariableRatio import (
    ChpVariableRatio,
)

CONVERSION_FACTOR_TO_ELECTRICITY = 0.36
CONVERSION_FACTOR_TO_HEAT = 0.5
BETA = 0.2
INSTALLED_CAPACITY = 150.0
MAXIMUM_CAPACITY = 350.0
VARIABLE_COSTS = 10.0
CAPEX_VAR = 1000.0

EXPECTED_ELECTRICITY_CONVERSION_FACTOR = (
    CONVERSION_FACTOR_TO_ELECTRICITY - BETA * CONVERSION_FACTOR_TO_HEAT
)


@pytest.fixture
def project_data() -> DummyProjectData:
    return DummyProjectData()


@pytest.fixture
def fuel_bus() -> solph.Bus:
    return solph.Bus(label="fuel")


@pytest.fixture
def electricity_bus() -> solph.Bus:
    return solph.Bus(label="electricity")


@pytest.fixture
def heat_bus() -> solph.Bus:
    return solph.Bus(label="heat")


def _chp_variable_ratio_kwargs(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
    **overrides: Any,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "name": "chp_variable_ratio_test",
        "bus_in_fuel": fuel_bus,
        "bus_out_electricity": electricity_bus,
        "bus_out_heat": heat_bus,
        "conversion_factor_to_electricity": CONVERSION_FACTOR_TO_ELECTRICITY,
        "conversion_factor_to_heat": CONVERSION_FACTOR_TO_HEAT,
        "beta": BETA,
        "project_data": project_data,
        "installed_capacity": INSTALLED_CAPACITY,
        "maximum_capacity": MAXIMUM_CAPACITY,
        "optimize_cap": False,
        "capex_var": CAPEX_VAR,
        "opex_var": VARIABLE_COSTS,
    }
    kwargs.update(overrides)
    return kwargs


def test_chp_variable_ratio_initializes_with_expected_buses(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    chp = ChpVariableRatio(
        **_chp_variable_ratio_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            heat_bus=heat_bus,
            project_data=project_data,
        ),
    )

    assert "chp_variable_ratio_test" in str(chp.label)
    assert fuel_bus in chp.inputs
    assert electricity_bus in chp.outputs
    assert heat_bus in chp.outputs
    assert_no_none_keys(chp)


def test_chp_variable_ratio_conversion_factors_and_variable_costs(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    chp = ChpVariableRatio(
        **_chp_variable_ratio_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            heat_bus=heat_bus,
            project_data=project_data,
        ),
    )

    assert_conversion_factor(
        component=chp,
        bus=electricity_bus,
        expected=EXPECTED_ELECTRICITY_CONVERSION_FACTOR,
    )
    assert_conversion_factor(
        component=chp,
        bus=heat_bus,
        expected=CONVERSION_FACTOR_TO_HEAT,
    )
    assert_any_flow_has_variable_costs(
        component=chp,
        expected=VARIABLE_COSTS,
    )


def test_chp_variable_ratio_fuel_demand_math_is_consistent() -> None:
    fuel_per_mwh_electricity = 1 / CONVERSION_FACTOR_TO_ELECTRICITY
    fuel_per_mwh_heat = 1 / CONVERSION_FACTOR_TO_HEAT

    assert fuel_per_mwh_electricity == pytest.approx(2.7777777778)
    assert fuel_per_mwh_heat == pytest.approx(2.0)


def test_chp_variable_ratio_static_capacity_is_set_on_a_flow(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    chp = ChpVariableRatio(
        **_chp_variable_ratio_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            heat_bus=heat_bus,
            project_data=project_data,
        ),
    )

    assert_any_flow_has_capacity(
        component=chp,
        expected=INSTALLED_CAPACITY,
    )


def test_chp_variable_ratio_investment_capacity_logic(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    chp = ChpVariableRatio(
        **_chp_variable_ratio_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            heat_bus=heat_bus,
            project_data=project_data,
            optimize_cap=True,
            installed_capacity=INSTALLED_CAPACITY,
            maximum_capacity=MAXIMUM_CAPACITY,
        ),
    )

    assert_any_flow_has_investment_capacity(
        component=chp,
        existing=INSTALLED_CAPACITY,
        maximum=MAXIMUM_CAPACITY,
    )


@pytest.mark.parametrize(
    "invalid_conversion_factor",
    [-0.1, 0.0, 1.1],
)
def test_chp_variable_ratio_rejects_invalid_electricity_conversion_factor(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
    invalid_conversion_factor: Any,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        ChpVariableRatio(
            **_chp_variable_ratio_kwargs(
                fuel_bus=fuel_bus,
                electricity_bus=electricity_bus,
                heat_bus=heat_bus,
                project_data=project_data,
                conversion_factor_to_electricity=invalid_conversion_factor,
            ),
        )


@pytest.mark.parametrize(
    "invalid_conversion_factor",
    [-0.1, 0.0, 1.1],
)
def test_chp_variable_ratio_rejects_invalid_heat_conversion_factor(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
    invalid_conversion_factor: Any,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        ChpVariableRatio(
            **_chp_variable_ratio_kwargs(
                fuel_bus=fuel_bus,
                electricity_bus=electricity_bus,
                heat_bus=heat_bus,
                project_data=project_data,
                conversion_factor_to_heat=invalid_conversion_factor,
            ),
        )


def test_chp_variable_ratio_rejects_invalid_fuel_bus(
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(TypeError):
        ChpVariableRatio(
            **_chp_variable_ratio_kwargs(
                fuel_bus="not-a-bus",
                electricity_bus=electricity_bus,
                heat_bus=heat_bus,
                project_data=project_data,
            ),
        )


def test_chp_variable_ratio_rejects_invalid_optimize_cap(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(TypeError):
        ChpVariableRatio(
            **_chp_variable_ratio_kwargs(
                fuel_bus=fuel_bus,
                electricity_bus=electricity_bus,
                heat_bus=heat_bus,
                project_data=project_data,
                optimize_cap="yes",
            ),
        )


def test_chp_variable_ratio_rejects_maximum_capacity_below_installed_capacity(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"maximum_capacity.*installed_capacity|installed_capacity.*maximum_capacity",
    ):
        ChpVariableRatio(
            **_chp_variable_ratio_kwargs(
                fuel_bus=fuel_bus,
                electricity_bus=electricity_bus,
                heat_bus=heat_bus,
                project_data=project_data,
                optimize_cap=True,
                installed_capacity=100.0,
                maximum_capacity=50.0,
            ),
        )


def test_chp_variable_ratio_can_be_added_to_minimal_solph_model(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    chp = ChpVariableRatio(
        **_chp_variable_ratio_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            heat_bus=heat_bus,
            project_data=project_data,
        ),
    )

    assert_model_builds(chp)
