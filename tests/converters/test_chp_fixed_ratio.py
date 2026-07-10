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
from oemof.eesyplan.components.converters.ChpFixedRatio import ChpFixedRatio

CONVERSION_FACTOR_TO_ELECTRICITY = 0.33
CONVERSION_FACTOR_TO_HEAT = 0.52
INSTALLED_CAPACITY = 120.0
MAXIMUM_CAPACITY = 300.0
VARIABLE_COSTS = 9.0
CAPEX_VAR = 1000.0


@pytest.fixture
def fuel_bus() -> solph.Bus:
    return solph.Bus(label="fuel")


@pytest.fixture
def electricity_bus() -> solph.Bus:
    return solph.Bus(label="electricity")


@pytest.fixture
def heat_bus() -> solph.Bus:
    return solph.Bus(label="heat")


@pytest.fixture
def project_data() -> DummyProjectData:
    return DummyProjectData()


def _chp_fixed_ratio_kwargs(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
    **overrides: Any,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "name": "chp_fixed_ratio_test",
        "bus_in_fuel": fuel_bus,
        "bus_out_electricity": electricity_bus,
        "bus_out_heat": heat_bus,
        "conversion_factor_to_electricity": CONVERSION_FACTOR_TO_ELECTRICITY,
        "conversion_factor_to_heat": CONVERSION_FACTOR_TO_HEAT,
        "project_data": project_data,
        "installed_capacity": INSTALLED_CAPACITY,
        "maximum_capacity": MAXIMUM_CAPACITY,
        "optimize_cap": False,
        "capex_var": CAPEX_VAR,
        "opex_var": VARIABLE_COSTS,
    }
    kwargs.update(overrides)
    return kwargs


def test_chp_fixed_ratio_initializes_with_expected_buses(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    chp = ChpFixedRatio(
        **_chp_fixed_ratio_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            heat_bus=heat_bus,
            project_data=project_data,
        ),
    )

    assert "chp_fixed_ratio_test" in str(chp.label)
    assert fuel_bus in chp.inputs
    assert electricity_bus in chp.outputs
    assert heat_bus in chp.outputs
    assert_no_none_keys(chp)


def test_chp_fixed_ratio_conversion_factors_and_variable_costs(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    chp = ChpFixedRatio(
        **_chp_fixed_ratio_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            heat_bus=heat_bus,
            project_data=project_data,
        ),
    )

    assert_conversion_factor(
        component=chp,
        bus=electricity_bus,
        expected=CONVERSION_FACTOR_TO_ELECTRICITY,
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


def test_chp_fixed_ratio_has_physically_valid_total_efficiency() -> None:
    total_efficiency = (
        CONVERSION_FACTOR_TO_ELECTRICITY + CONVERSION_FACTOR_TO_HEAT
    )

    assert total_efficiency == pytest.approx(0.85)
    assert total_efficiency <= 1.0


def test_chp_fixed_ratio_has_expected_heat_to_power_ratio() -> None:
    heat_to_power_ratio = (
        CONVERSION_FACTOR_TO_HEAT / CONVERSION_FACTOR_TO_ELECTRICITY
    )

    assert heat_to_power_ratio == pytest.approx(1.5757575758)


def test_chp_fixed_ratio_static_capacity_is_set_on_a_flow(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    chp = ChpFixedRatio(
        **_chp_fixed_ratio_kwargs(
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


def test_chp_fixed_ratio_investment_capacity_logic(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    chp = ChpFixedRatio(
        **_chp_fixed_ratio_kwargs(
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
def test_chp_fixed_ratio_rejects_invalid_electricity_conversion_factor(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
    invalid_conversion_factor: Any,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        ChpFixedRatio(
            **_chp_fixed_ratio_kwargs(
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
def test_chp_fixed_ratio_rejects_invalid_heat_conversion_factor(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
    invalid_conversion_factor: Any,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        ChpFixedRatio(
            **_chp_fixed_ratio_kwargs(
                fuel_bus=fuel_bus,
                electricity_bus=electricity_bus,
                heat_bus=heat_bus,
                project_data=project_data,
                conversion_factor_to_heat=invalid_conversion_factor,
            ),
        )


def test_chp_fixed_ratio_rejects_total_efficiency_above_one(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"(?i)(total efficiency|sum.*conversion.*factors).*(1|one)",
    ):
        ChpFixedRatio(
            **_chp_fixed_ratio_kwargs(
                fuel_bus=fuel_bus,
                electricity_bus=electricity_bus,
                heat_bus=heat_bus,
                project_data=project_data,
                conversion_factor_to_electricity=0.7,
                conversion_factor_to_heat=0.6,
            ),
        )


def test_chp_fixed_ratio_rejects_invalid_fuel_bus(
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(TypeError):
        ChpFixedRatio(
            **_chp_fixed_ratio_kwargs(
                fuel_bus="not-a-bus",
                electricity_bus=electricity_bus,
                heat_bus=heat_bus,
                project_data=project_data,
            ),
        )


def test_chp_fixed_ratio_rejects_invalid_optimize_cap(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(TypeError):
        ChpFixedRatio(
            **_chp_fixed_ratio_kwargs(
                fuel_bus=fuel_bus,
                electricity_bus=electricity_bus,
                heat_bus=heat_bus,
                project_data=project_data,
                optimize_cap="yes",
            ),
        )


def test_chp_fixed_ratio_rejects_maximum_capacity_below_installed_capacity(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"maximum_capacity.*installed_capacity|installed_capacity.*maximum_capacity",
    ):
        ChpFixedRatio(
            **_chp_fixed_ratio_kwargs(
                fuel_bus=fuel_bus,
                electricity_bus=electricity_bus,
                heat_bus=heat_bus,
                project_data=project_data,
                optimize_cap=True,
                installed_capacity=100.0,
                maximum_capacity=50.0,
            ),
        )


def test_chp_fixed_ratio_can_be_added_to_minimal_solph_model(
    fuel_bus: solph.Bus,
    electricity_bus: solph.Bus,
    heat_bus: solph.Bus,
    project_data: Any,
) -> None:
    chp = ChpFixedRatio(
        **_chp_fixed_ratio_kwargs(
            fuel_bus=fuel_bus,
            electricity_bus=electricity_bus,
            heat_bus=heat_bus,
            project_data=project_data,
        ),
    )

    assert_model_builds(chp)
