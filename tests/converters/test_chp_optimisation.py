from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest
from pyomo.environ import SolverFactory

from oemof.eesyplan import Project
from oemof.eesyplan.components.converters.ChpFixedRatio import ChpFixedRatio
from oemof.eesyplan.components.converters.ChpVariableRatio import (
    ChpVariableRatio,
)
from oemof.solph import Bus
from oemof.solph import EnergySystem
from oemof.solph import Flow
from oemof.solph import Model
from oemof.solph import processing
from oemof.solph.components import Sink
from oemof.solph.components import Source


def _skip_if_solver_missing(solver: str = "cbc") -> None:
    if not SolverFactory(solver).available(exception_flag=False):
        pytest.skip(f"Solver {solver!r} is not available.")


def _is_nan(value: Any) -> bool:
    try:
        return value != value
    except TypeError:
        return False


def _raw_flow_sequence(
    results: dict[Any, Any],
    from_node: Any,
    to_node: Any,
) -> list[Any]:
    return list(results[(from_node, to_node)]["sequences"]["flow"])


def _trim_trailing_nans(values: list[Any]) -> list[Any]:
    trimmed = list(values)
    while trimmed and _is_nan(trimmed[-1]):
        trimmed.pop()
    return trimmed


def _result_flow(
    results: dict[Any, Any],
    from_node: Any,
    to_node: Any,
) -> list[float]:
    values = _trim_trailing_nans(
        _raw_flow_sequence(results, from_node, to_node)
    )

    if any(_is_nan(v) for v in values):
        raise AssertionError(
            f"Flow contains NaN inside optimisation horizon for "
            f"({from_node}, {to_node}): {values!r}"
        )

    return [float(v) for v in values]


def _result_horizon(
    results: dict[Any, Any],
    from_node: Any,
    to_node: Any,
) -> int:
    return len(_result_flow(results, from_node, to_node))


def _result_scalar(
    results: dict[Any, Any],
    from_node: Any,
    to_node: Any,
    name: str,
) -> float | None:
    edge_results = results[(from_node, to_node)]
    scalars = edge_results.get("scalars")
    if scalars is None:
        return None

    for key, value in scalars.items():
        if name in str(key):
            return float(value)

    return None


def _assert_non_negative(values: Sequence[float], tol: float = 1e-8) -> None:
    for value in values:
        assert value >= -tol


def _assert_all_close(
    actual: Sequence[float],
    expected: Sequence[float],
) -> None:
    assert list(actual) == pytest.approx(list(expected))


@pytest.fixture
def project() -> Project:
    return Project(
        name="test_project",
        lifetime=20,
        tax=0,
        discount_factor=0.01,
    )


def _solve_model(es: EnergySystem) -> dict[Any, Any]:
    _skip_if_solver_missing("cbc")
    model = Model(es)
    model.solve(solver="cbc")
    return processing.results(model)


def _build_common_buses() -> tuple[Bus, Bus, Bus]:
    fuel_bus = Bus(label="fuel")
    electricity_bus = Bus(label="electricity")
    heat_bus = Bus(label="heat")
    return fuel_bus, electricity_bus, heat_bus


def _add_common_market_components(
    es: EnergySystem,
    fuel_bus: Bus,
    electricity_bus: Bus,
    heat_bus: Bus,
    electricity_demand_profile: Sequence[float] | None = None,
    heat_demand_profile: Sequence[float] | None = None,
) -> None:
    es.add(
        Source(
            label="fuel_source",
            outputs={fuel_bus: Flow(variable_costs=0.0)},
        )
    )

    if electricity_demand_profile is not None:
        es.add(
            Sink(
                label="electricity_demand",
                inputs={
                    electricity_bus: Flow(
                        fix=list(electricity_demand_profile),
                        nominal_capacity=1.0,
                    )
                },
            )
        )

    if heat_demand_profile is not None:
        es.add(
            Sink(
                label="heat_demand",
                inputs={
                    heat_bus: Flow(
                        fix=list(heat_demand_profile),
                        nominal_capacity=1.0,
                    )
                },
            )
        )

    es.add(
        Sink(
            label="electricity_excess",
            inputs={electricity_bus: Flow(variable_costs=0.0)},
        )
    )
    es.add(
        Sink(
            label="heat_excess",
            inputs={heat_bus: Flow(variable_costs=0.0)},
        )
    )


def _build_fixed_ratio_system(
    project: Project,
    *,
    conversion_factor_to_electricity: float = 0.4,
    conversion_factor_to_heat: float = 0.4,
    installed_capacity: float = 100.0,
    number: int = 4,
    opex_var: float = 0.0,
    electricity_demand_profile: Sequence[float] | None = None,
    heat_demand_profile: Sequence[float] | None = None,
) -> tuple[EnergySystem, Bus, Bus, Bus, ChpFixedRatio]:
    es = EnergySystem(timeindex=range(number))
    fuel_bus, electricity_bus, heat_bus = _build_common_buses()
    es.add(fuel_bus, electricity_bus, heat_bus)

    chp = ChpFixedRatio(
        name="fixed_chp",
        bus_in_fuel=fuel_bus,
        bus_out_electricity=electricity_bus,
        bus_out_heat=heat_bus,
        conversion_factor_to_electricity=conversion_factor_to_electricity,
        conversion_factor_to_heat=conversion_factor_to_heat,
        project_data=project,
        age_installed=0,
        installed_capacity=installed_capacity,
        capex_var=1000.0,
        capex_fix=0.0,
        opex_fix=0.0,
        opex_var=opex_var,
        lifetime=20,
        optimize_cap=False,
        maximum_capacity=installed_capacity,
    )
    es.add(chp)

    _add_common_market_components(
        es,
        fuel_bus,
        electricity_bus,
        heat_bus,
        electricity_demand_profile=electricity_demand_profile,
        heat_demand_profile=heat_demand_profile,
    )
    return es, fuel_bus, electricity_bus, heat_bus, chp


def _build_variable_ratio_system(
    project: Project,
    *,
    conversion_factor_to_electricity: float = 0.5,
    conversion_factor_to_heat: float = 0.3,
    beta: float = 0.4,
    installed_capacity: float = 100.0,
    number: int = 4,
    opex_var: float = 0.0,
    electricity_demand_profile: Sequence[float] | None = None,
    heat_demand_profile: Sequence[float] | None = None,
) -> tuple[EnergySystem, Bus, Bus, Bus, ChpVariableRatio]:
    es = EnergySystem(timeindex=range(number))
    fuel_bus, electricity_bus, heat_bus = _build_common_buses()
    es.add(fuel_bus, electricity_bus, heat_bus)

    chp = ChpVariableRatio(
        name="variable_chp",
        bus_in_fuel=fuel_bus,
        bus_out_electricity=electricity_bus,
        bus_out_heat=heat_bus,
        conversion_factor_to_electricity=conversion_factor_to_electricity,
        conversion_factor_to_heat=conversion_factor_to_heat,
        beta=beta,
        project_data=project,
        age_installed=0,
        installed_capacity=installed_capacity,
        capex_var=1000.0,
        capex_fix=0.0,
        opex_fix=0.0,
        opex_var=opex_var,
        lifetime=20,
        optimize_cap=False,
        maximum_capacity=installed_capacity,
    )
    es.add(chp)

    _add_common_market_components(
        es,
        fuel_bus,
        electricity_bus,
        heat_bus,
        electricity_demand_profile=electricity_demand_profile,
        heat_demand_profile=heat_demand_profile,
    )
    return es, fuel_bus, electricity_bus, heat_bus, chp


def _build_investment_system(
    project: Project,
    chp_class: type[ChpFixedRatio] | type[ChpVariableRatio],
    *,
    conversion_factor_to_electricity: float,
    conversion_factor_to_heat: float,
    beta: float | None = None,
) -> tuple[EnergySystem, Bus, ChpFixedRatio | ChpVariableRatio]:
    es = EnergySystem(timeindex=range(4))
    fuel_bus, electricity_bus, heat_bus = _build_common_buses()
    es.add(fuel_bus, electricity_bus, heat_bus)

    kwargs: dict[str, Any] = {
        "name": "test_chp",
        "bus_in_fuel": fuel_bus,
        "bus_out_electricity": electricity_bus,
        "bus_out_heat": heat_bus,
        "conversion_factor_to_electricity": conversion_factor_to_electricity,
        "conversion_factor_to_heat": conversion_factor_to_heat,
        "project_data": project,
        "installed_capacity": 25.0,
        "capex_var": 1000.0,
        "capex_fix": 0.0,
        "opex_fix": 0.0,
        "opex_var": 0.0,
        "lifetime": 20,
        "optimize_cap": True,
        "maximum_capacity": 60.0,
    }
    if beta is not None:
        kwargs["beta"] = beta

    chp = chp_class(**kwargs)
    es.add(chp)

    _add_common_market_components(
        es,
        fuel_bus,
        electricity_bus,
        heat_bus,
        electricity_demand_profile=[10.0, 10.0, 10.0, 10.0],
    )

    return es, electricity_bus, chp


class TestChpFixedRatioDispatch:
    def test_exact_input_output_relations_for_electricity_demand(
        self,
        project: Project,
    ) -> None:
        eta_el = 0.3
        eta_heat = 0.5
        demand = [20.0, 30.0, 40.0, 50.0]

        es, fuel_bus, electricity_bus, heat_bus, chp = (
            _build_fixed_ratio_system(
                project,
                conversion_factor_to_electricity=eta_el,
                conversion_factor_to_heat=eta_heat,
                number=len(demand),
                electricity_demand_profile=demand,
            )
        )
        results = _solve_model(es)

        horizon = _result_horizon(results, chp, electricity_bus)
        expected_el = demand[:horizon]
        expected_fuel = [d / eta_el for d in expected_el]
        expected_heat = [f * eta_heat for f in expected_fuel]

        _assert_all_close(
            _result_flow(results, chp, electricity_bus), expected_el
        )
        _assert_all_close(_result_flow(results, fuel_bus, chp), expected_fuel)
        _assert_all_close(_result_flow(results, chp, heat_bus), expected_heat)

    def test_constant_heat_to_power_ratio(
        self,
        project: Project,
    ) -> None:
        eta_el = 0.4
        eta_heat = 0.2
        demand = [10.0, 20.0, 30.0, 40.0]
        ratio = eta_heat / eta_el

        es, _, electricity_bus, heat_bus, chp = _build_fixed_ratio_system(
            project,
            conversion_factor_to_electricity=eta_el,
            conversion_factor_to_heat=eta_heat,
            number=len(demand),
            electricity_demand_profile=demand,
        )
        results = _solve_model(es)

        electricity = _result_flow(results, chp, electricity_bus)
        heat = _result_flow(results, chp, heat_bus)

        for el, th in zip(electricity, heat, strict=True):
            assert th == pytest.approx(el * ratio)

    def test_no_dispatch_without_demand(
        self,
        project: Project,
    ) -> None:
        es, fuel_bus, electricity_bus, heat_bus, chp = (
            _build_fixed_ratio_system(
                project,
                number=4,
            )
        )
        results = _solve_model(es)

        _assert_all_close(
            _result_flow(results, fuel_bus, chp), [0.0, 0.0, 0.0]
        )
        _assert_all_close(
            _result_flow(results, chp, electricity_bus), [0.0, 0.0, 0.0]
        )
        _assert_all_close(
            _result_flow(results, chp, heat_bus), [0.0, 0.0, 0.0]
        )

    def test_dispatch_matches_electricity_demand_when_heat_can_be_dumped(
        self,
        project: Project,
    ) -> None:
        eta_el = 0.4
        eta_heat = 0.4
        demand = [10.0, 20.0, 30.0, 40.0]

        es, fuel_bus, electricity_bus, heat_bus, chp = (
            _build_fixed_ratio_system(
                project,
                conversion_factor_to_electricity=eta_el,
                conversion_factor_to_heat=eta_heat,
                number=len(demand),
                electricity_demand_profile=demand,
            )
        )
        results = _solve_model(es)

        horizon = _result_horizon(results, chp, electricity_bus)
        expected_el = demand[:horizon]
        expected_fuel = [d / eta_el for d in expected_el]
        expected_heat = [f * eta_heat for f in expected_fuel]

        _assert_all_close(
            _result_flow(results, chp, electricity_bus), expected_el
        )
        _assert_all_close(_result_flow(results, fuel_bus, chp), expected_fuel)
        _assert_all_close(_result_flow(results, chp, heat_bus), expected_heat)

    def test_heat_output_follows_fixed_ratio_for_heat_demand_case(
        self,
        project: Project,
    ) -> None:
        eta_el = 0.4
        eta_heat = 0.2
        heat_demand = [5.0, 10.0, 15.0, 20.0]

        es, _, electricity_bus, heat_bus, chp = _build_fixed_ratio_system(
            project,
            conversion_factor_to_electricity=eta_el,
            conversion_factor_to_heat=eta_heat,
            number=len(heat_demand),
            heat_demand_profile=heat_demand,
        )
        results = _solve_model(es)

        horizon = _result_horizon(results, chp, heat_bus)
        expected_heat = heat_demand[:horizon]
        expected_el = [h * eta_el / eta_heat for h in expected_heat]

        _assert_all_close(_result_flow(results, chp, heat_bus), expected_heat)
        _assert_all_close(
            _result_flow(results, chp, electricity_bus), expected_el
        )

    def test_all_flows_are_non_negative(
        self,
        project: Project,
    ) -> None:
        es, fuel_bus, electricity_bus, heat_bus, chp = (
            _build_fixed_ratio_system(
                project,
                number=4,
                electricity_demand_profile=[10.0, 20.0, 30.0, 40.0],
            )
        )
        results = _solve_model(es)

        _assert_non_negative(_result_flow(results, fuel_bus, chp))
        _assert_non_negative(_result_flow(results, chp, electricity_bus))
        _assert_non_negative(_result_flow(results, chp, heat_bus))

    def test_higher_electricity_demand_leads_to_more_dispatch(
        self,
        project: Project,
    ) -> None:
        es_low, _, electricity_bus_low, _, chp_low = _build_fixed_ratio_system(
            project,
            number=4,
            electricity_demand_profile=[5.0, 5.0, 5.0, 5.0],
        )
        es_high, _, electricity_bus_high, _, chp_high = (
            _build_fixed_ratio_system(
                project,
                number=4,
                electricity_demand_profile=[20.0, 20.0, 20.0, 20.0],
            )
        )

        low_results = _solve_model(es_low)
        high_results = _solve_model(es_high)

        assert sum(
            _result_flow(high_results, chp_high, electricity_bus_high)
        ) > sum(_result_flow(low_results, chp_low, electricity_bus_low))


class TestChpVariableRatioDispatch:
    def test_without_heat_demand_heat_is_zero_and_flows_are_feasible(
        self,
        project: Project,
    ) -> None:
        eta_el = 0.5
        demand = [20.0, 40.0, 60.0, 80.0]

        es, fuel_bus, electricity_bus, heat_bus, chp = (
            _build_variable_ratio_system(
                project,
                conversion_factor_to_electricity=eta_el,
                conversion_factor_to_heat=0.3,
                beta=0.4,
                number=len(demand),
                electricity_demand_profile=demand,
            )
        )
        results = _solve_model(es)

        fuel = _result_flow(results, fuel_bus, chp)
        electricity = _result_flow(results, chp, electricity_bus)
        heat = _result_flow(results, chp, heat_bus)

        _assert_non_negative(fuel)
        _assert_non_negative(electricity)
        _assert_non_negative(heat)
        _assert_all_close(heat, [0.0] * len(heat))

        for f, el in zip(fuel, electricity, strict=True):
            assert el <= f * eta_el + 1e-8

    def test_with_heat_demand_produces_requested_heat(
        self,
        project: Project,
    ) -> None:
        heat_demand = [5.0, 10.0, 7.0, 3.0]

        es, _, _, heat_bus, chp = _build_variable_ratio_system(
            project,
            conversion_factor_to_electricity=0.5,
            conversion_factor_to_heat=0.3,
            beta=0.4,
            number=len(heat_demand),
            heat_demand_profile=heat_demand,
        )
        results = _solve_model(es)

        horizon = _result_horizon(results, chp, heat_bus)
        _assert_all_close(
            _result_flow(results, chp, heat_bus), heat_demand[:horizon]
        )

    def test_heat_demand_reduces_electricity_compared_to_no_heat_case(
        self,
        project: Project,
    ) -> None:
        common = {
            "project": project,
            "conversion_factor_to_electricity": 0.5,
            "conversion_factor_to_heat": 0.3,
            "beta": 0.4,
            "installed_capacity": 100.0,
            "number": 4,
        }

        es_no_heat, _, electricity_bus_no_heat, _, chp_no_heat = (
            _build_variable_ratio_system(
                **common,
                electricity_demand_profile=[50.0, 50.0, 50.0, 50.0],
            )
        )
        es_heat, _, electricity_bus_heat, heat_bus_heat, chp_heat = (
            _build_variable_ratio_system(
                **common,
                electricity_demand_profile=[50.0, 50.0, 50.0, 50.0],
                heat_demand_profile=[5.0, 5.0, 5.0, 5.0],
            )
        )

        no_heat_results = _solve_model(es_no_heat)
        heat_results = _solve_model(es_heat)

        assert sum(_result_flow(heat_results, chp_heat, heat_bus_heat)) > 0.0
        assert sum(
            _result_flow(heat_results, chp_heat, electricity_bus_heat)
        ) <= (
            sum(
                _result_flow(
                    no_heat_results, chp_no_heat, electricity_bus_no_heat
                )
            )
            + 1e-8
        )

    def test_higher_beta_reduces_electricity_for_same_heat_demand(
        self,
        project: Project,
    ) -> None:
        common = {
            "project": project,
            "conversion_factor_to_electricity": 0.5,
            "conversion_factor_to_heat": 0.25,
            "installed_capacity": 100.0,
            "number": 4,
            "electricity_demand_profile": [50.0, 50.0, 50.0, 50.0],
            "heat_demand_profile": [5.0, 5.0, 5.0, 5.0],
        }

        es_low_beta, _, electricity_bus_low_beta, _, chp_low_beta = (
            _build_variable_ratio_system(**common, beta=0.1)
        )
        es_high_beta, _, electricity_bus_high_beta, _, chp_high_beta = (
            _build_variable_ratio_system(**common, beta=0.8)
        )

        low_beta_results = _solve_model(es_low_beta)
        high_beta_results = _solve_model(es_high_beta)

        assert sum(
            _result_flow(
                high_beta_results, chp_high_beta, electricity_bus_high_beta
            )
        ) <= (
            sum(
                _result_flow(
                    low_beta_results,
                    chp_low_beta,
                    electricity_bus_low_beta,
                )
            )
            + 1e-8
        )

    def test_dispatch_without_demand_remains_non_negative(
        self,
        project: Project,
    ) -> None:
        es, fuel_bus, electricity_bus, heat_bus, chp = (
            _build_variable_ratio_system(
                project,
                number=4,
            )
        )
        results = _solve_model(es)

        _assert_non_negative(_result_flow(results, fuel_bus, chp))
        _assert_non_negative(_result_flow(results, chp, electricity_bus))
        _assert_non_negative(_result_flow(results, chp, heat_bus))

    def test_all_flows_are_non_negative(
        self,
        project: Project,
    ) -> None:
        es, fuel_bus, electricity_bus, heat_bus, chp = (
            _build_variable_ratio_system(
                project,
                number=4,
                electricity_demand_profile=[40.0, 40.0, 40.0, 40.0],
                heat_demand_profile=[5.0, 10.0, 0.0, 8.0],
            )
        )
        results = _solve_model(es)

        _assert_non_negative(_result_flow(results, fuel_bus, chp))
        _assert_non_negative(_result_flow(results, chp, electricity_bus))
        _assert_non_negative(_result_flow(results, chp, heat_bus))

    def test_higher_electricity_demand_does_not_reduce_dispatch_without_heat_demand(
        self,
        project: Project,
    ) -> None:
        es_low, _, electricity_bus_low, _, chp_low = (
            _build_variable_ratio_system(
                project,
                number=4,
                electricity_demand_profile=[10.0, 10.0, 10.0, 10.0],
            )
        )
        es_high, _, electricity_bus_high, _, chp_high = (
            _build_variable_ratio_system(
                project,
                number=4,
                electricity_demand_profile=[40.0, 40.0, 40.0, 40.0],
            )
        )

        low_results = _solve_model(es_low)
        high_results = _solve_model(es_high)

        assert sum(
            _result_flow(high_results, chp_high, electricity_bus_high)
        ) >= (
            sum(_result_flow(low_results, chp_low, electricity_bus_low)) - 1e-8
        )


class TestChpInvestmentBehaviour:
    @pytest.mark.parametrize(
        (
            "chp_class",
            "conversion_factor_to_electricity",
            "conversion_factor_to_heat",
            "beta",
        ),
        [
            (ChpFixedRatio, 0.4, 0.4, None),
            (ChpVariableRatio, 0.5, 0.3, 0.4),
        ],
    )
    def test_existing_capacity_is_kept_when_optimizing(
        self,
        project: Project,
        chp_class: type[ChpFixedRatio] | type[ChpVariableRatio],
        conversion_factor_to_electricity: float,
        conversion_factor_to_heat: float,
        beta: float | None,
    ) -> None:
        es, electricity_bus, chp = _build_investment_system(
            project,
            chp_class,
            conversion_factor_to_electricity=conversion_factor_to_electricity,
            conversion_factor_to_heat=conversion_factor_to_heat,
            beta=beta,
        )

        results = _solve_model(es)
        invested = _result_scalar(results, chp, electricity_bus, "invest")

        assert invested is not None
        assert invested >= -1e-8
