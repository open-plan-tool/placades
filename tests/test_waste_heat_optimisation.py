"""Optimisation tests for the direct waste heat component."""

from __future__ import annotations

from typing import Any

import pytest
from pyomo.environ import SolverFactory
from pyomo.environ import value as pyomo_value

from oemof.eesyplan import EnergySystem as EesyplanEnergySystem
from oemof.eesyplan import Project
from oemof.eesyplan import optimise
from oemof.eesyplan.components.converters.waste_heat import WasteHeatDirect
from oemof.solph import Bus
from oemof.solph import EnergySystem as SolphEnergySystem
from oemof.solph import Flow
from oemof.solph import Model
from oemof.solph import processing
from oemof.solph.components import Sink
from oemof.solph.components import Source


# ---------------------------------------------------------------------------
# Solver / result helpers
# ---------------------------------------------------------------------------


def _skip_if_solver_missing(solver: str = "cbc") -> None:
    if not SolverFactory(solver).available(exception_flag=False):
        pytest.skip(f"Solver {solver!r} is not available.")


def _termination_condition_from_runtime_error(error: RuntimeError) -> str:
    message = str(error).lower()
    marker = "termination condition:"
    if marker in message:
        return message.split(marker, 1)[1].splitlines()[0].strip()
    if "infeasible" in message:
        return "infeasible"
    return "runtime_error"


def _eesyplan_solver_termination_condition(results: Any) -> str:
    return str(
        results._solver_results["Solver"][0]["Termination condition"]
    ).lower()


def _eesyplan_objective(results: Any) -> float:
    return float(results._meta_results["objective"])


def _solph_results(results: Any) -> dict[Any, Any]:
    return processing.results(results._model)


def _is_nan(value: Any) -> bool:
    try:
        return value != value
    except TypeError:
        return False


def _result_flow(
    results: dict[Any, Any],
    from_node: Any,
    to_node: Any,
    length: int,
) -> list[float]:
    flow_sequence = results[(from_node, to_node)]["sequences"]["flow"]
    raw_values = list(flow_sequence)

    while raw_values and _is_nan(raw_values[-1]):
        raw_values.pop()

    values = raw_values[:length]

    if len(values) != length:
        raise AssertionError(
            f"Expected {length} flow values for ({from_node}, {to_node}), "
            f"got {len(values)} values: {values!r}"
        )
    if any(_is_nan(value) for value in values):
        raise AssertionError(
            f"Flow contains NaN inside optimisation horizon: {values!r}"
        )

    return [float(value) for value in values]


def _result_scalar(edge_results: dict[str, Any], name: str) -> float:
    for key, value in edge_results["scalars"].items():
        if name in str(key):
            return float(value)
    raise AssertionError(f"Could not find scalar result containing {name!r}.")


def _value_as_float(value: Any) -> float:
    if value is None:
        raise TypeError("Cannot convert None to float.")
    if hasattr(value, "_value"):
        return float(value._value)
    try:
        return float(value)
    except (TypeError, ValueError):
        pass
    if hasattr(value, "dropna") and hasattr(value, "iloc"):
        non_empty = value.dropna()
        if len(non_empty) == 0:
            raise TypeError(
                f"Cannot convert empty pandas object to float: {value!r}"
            )
        return float(non_empty.iloc[0])
    if hasattr(value, "iloc"):
        return float(value.iloc[0])
    if hasattr(value, "__iter__"):
        return float(next(iter(value)))
    raise TypeError(f"Cannot convert value to float: {value!r}")


def _investment_ep_costs(waste_heat: Any, heat_bus: Any) -> float:
    return _value_as_float(waste_heat.outputs[heat_bus].investment.ep_costs)


# ---------------------------------------------------------------------------
# Validation / profile helpers
# ---------------------------------------------------------------------------


def _require_non_empty_profile(name: str, profile: list[float]) -> None:
    if not profile:
        raise ValueError(f"{name} must not be empty.")


def _require_non_negative_profile(name: str, profile: list[float]) -> None:
    negative_values = [value for value in profile if value < 0]
    if negative_values:
        raise ValueError(
            f"{name} must not contain negative values. Found: {negative_values!r}"
        )


def _require_same_profile_length(
    first_name: str,
    first_profile: list[float],
    second_name: str,
    second_profile: list[float],
) -> None:
    if len(first_profile) != len(second_profile):
        raise ValueError(
            f"{first_name} and {second_name} must have the same length. "
            f"Got {len(first_profile)} and {len(second_profile)}."
        )


def _nominal_and_normalised_profile(
    profile: list[float],
) -> tuple[float, list[float]]:
    nominal_capacity = max(max(profile), 1.0)
    return nominal_capacity, [value / nominal_capacity for value in profile]


def _build_fixed_sink(bus: Bus, label: str, profile: list[float]) -> Sink:
    nominal_capacity, fix = _nominal_and_normalised_profile(profile)
    return Sink(
        label=label,
        inputs={bus: Flow(nominal_capacity=nominal_capacity, fix=fix)},
    )


def _build_profile_source(
    bus: Bus,
    label: str,
    profile: list[float],
    *,
    forced: bool,
) -> Source:
    nominal_capacity, normalised = _nominal_and_normalised_profile(profile)
    flow = (
        Flow(nominal_capacity=nominal_capacity, fix=normalised)
        if forced
        else Flow(nominal_capacity=nominal_capacity, maximum=normalised)
    )
    return Source(label=label, outputs={bus: flow})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def project() -> Project:
    return Project(
        name="Project_X",
        lifetime=20,
        tax=0,
        discount_factor=0.01,
    )


# ---------------------------------------------------------------------------
# System builders
# ---------------------------------------------------------------------------


def _build_solph_dispatch_system(
    project: Project,
) -> tuple[
    SolphEnergySystem,
    WasteHeatDirect,
    Bus,
    Bus,
    list[float],
    list[float],
    float,
]:
    pd = pytest.importorskip("pandas")

    raw_heat_profile = [10.0, 20.0, 30.0]
    efficiency_hex = 0.8
    demand_profile = [8.0, 16.0, 24.0]

    timeindex = pd.date_range(
        "2026-01-01", periods=len(raw_heat_profile), freq="h"
    )
    energy_system = SolphEnergySystem(
        timeindex=timeindex, infer_last_interval=True
    )

    raw_heat_bus = Bus(label="raw_waste_heat")
    heat_bus = Bus(label="heat")

    raw_heat_source = Source(
        label="raw_waste_heat_source",
        outputs={raw_heat_bus: Flow(nominal_capacity=max(raw_heat_profile))},
    )

    waste_heat = WasteHeatDirect(
        name="waste_heat",
        bus_in_heat=raw_heat_bus,
        bus_out_heat=heat_bus,
        project_data=project,
        heat_profile=raw_heat_profile,
        installed_capacity=max(demand_profile),
        optimize_cap=False,
        heat_cost=0.0,
        efficiency_hex=efficiency_hex,
        opex_var=0.0,
    )

    heat_demand = _build_fixed_sink(heat_bus, "heat_demand", demand_profile)

    energy_system.add(
        raw_heat_bus, heat_bus, raw_heat_source, waste_heat, heat_demand
    )
    return (
        energy_system,
        waste_heat,
        raw_heat_bus,
        heat_bus,
        raw_heat_profile,
        demand_profile,
        efficiency_hex,
    )


def _build_eesyplan_system(
    project: Project,
    *,
    optimize_cap: bool,
    demand_profile: list[float],
    installed_capacity: float,
    capex_var: float,
) -> tuple[
    EesyplanEnergySystem, WasteHeatDirect, list[float], list[float], float
]:
    _require_non_empty_profile("demand_profile", demand_profile)
    _require_non_negative_profile("demand_profile", demand_profile)

    efficiency_hex = 0.8
    raw_heat_profile = [
        max(value / efficiency_hex, 1.0) for value in demand_profile
    ]

    energy_system = EesyplanEnergySystem(2026, number=len(demand_profile))
    raw_heat_bus = Bus(label="raw_waste_heat")
    heat_bus = Bus(label="heat")

    raw_heat_source = _build_profile_source(
        raw_heat_bus,
        "raw_waste_heat_source",
        raw_heat_profile,
        forced=False,
    )

    waste_heat = WasteHeatDirect(
        name="waste_heat",
        bus_in_heat=raw_heat_bus,
        bus_out_heat=heat_bus,
        project_data=project,
        heat_profile=raw_heat_profile,
        installed_capacity=installed_capacity,
        capex_fix=0.0,
        capex_var=capex_var,
        opex_fix=0.0,
        opex_var=0.0,
        lifetime=20,
        optimize_cap=optimize_cap,
        maximum_capacity=None,
        heat_cost=0.0,
        efficiency_hex=efficiency_hex,
    )

    heat_demand = _build_fixed_sink(heat_bus, "heat_demand", demand_profile)

    energy_system.add(
        raw_heat_bus, heat_bus, raw_heat_source, waste_heat, heat_demand
    )
    return (
        energy_system,
        waste_heat,
        raw_heat_profile,
        demand_profile,
        efficiency_hex,
    )


def _build_waste_heat_reality_system(
    project: Project,
    *,
    demand_profile: list[float],
    raw_waste_heat_profile: list[float],
    raw_waste_heat_forced: bool,
    dump_sink_enabled: bool,
    dump_sink_variable_costs: float,
    backup_boiler_enabled: bool,
    backup_boiler_variable_costs: float,
    waste_heat_variable_costs: float,
    optimize_cap: bool = False,
    installed_capacity: float | None = None,
    capex_var: float = 0.0,
    efficiency_hex: float = 0.8,
) -> dict[str, Any]:
    _require_non_empty_profile("demand_profile", demand_profile)
    _require_non_empty_profile(
        "raw_waste_heat_profile", raw_waste_heat_profile
    )
    _require_same_profile_length(
        "demand_profile",
        demand_profile,
        "raw_waste_heat_profile",
        raw_waste_heat_profile,
    )
    _require_non_negative_profile("demand_profile", demand_profile)
    _require_non_negative_profile(
        "raw_waste_heat_profile", raw_waste_heat_profile
    )

    if installed_capacity is None:
        installed_capacity = max(max(demand_profile), 1.0)

    energy_system = EesyplanEnergySystem(2026, number=len(demand_profile))
    raw_heat_bus = Bus(label="raw_waste_heat")
    heat_bus = Bus(label="heat")

    raw_heat_source = _build_profile_source(
        raw_heat_bus,
        "raw_waste_heat_source",
        raw_waste_heat_profile,
        forced=raw_waste_heat_forced,
    )

    waste_heat = WasteHeatDirect(
        name="waste_heat",
        bus_in_heat=raw_heat_bus,
        bus_out_heat=heat_bus,
        project_data=project,
        heat_profile=raw_waste_heat_profile,
        installed_capacity=installed_capacity,
        capex_fix=0.0,
        capex_var=capex_var,
        opex_fix=0.0,
        opex_var=0.0,
        lifetime=20,
        optimize_cap=optimize_cap,
        maximum_capacity=None,
        heat_cost=waste_heat_variable_costs,
        efficiency_hex=efficiency_hex,
    )

    heat_demand = _build_fixed_sink(heat_bus, "heat_demand", demand_profile)

    components: list[Any] = [
        raw_heat_bus,
        heat_bus,
        raw_heat_source,
        waste_heat,
        heat_demand,
    ]

    dump_sink = None
    if dump_sink_enabled:
        dump_sink = Sink(
            label="raw_waste_heat_dump_sink",
            inputs={
                raw_heat_bus: Flow(variable_costs=dump_sink_variable_costs)
            },
        )
        components.append(dump_sink)

    backup_boiler = None
    if backup_boiler_enabled:
        backup_boiler = Source(
            label="backup_boiler",
            outputs={
                heat_bus: Flow(variable_costs=backup_boiler_variable_costs)
            },
        )
        components.append(backup_boiler)

    energy_system.add(*components)

    return {
        "energy_system": energy_system,
        "waste_heat": waste_heat,
        "raw_heat_bus": raw_heat_bus,
        "heat_bus": heat_bus,
        "dump_sink": dump_sink,
        "backup_boiler": backup_boiler,
        "demand_profile": demand_profile,
        "raw_waste_heat_profile": raw_waste_heat_profile,
        "efficiency_hex": efficiency_hex,
        "dump_sink_variable_costs": dump_sink_variable_costs,
        "backup_boiler_variable_costs": backup_boiler_variable_costs,
        "waste_heat_variable_costs": waste_heat_variable_costs,
    }


# ---------------------------------------------------------------------------
# Case runners
# ---------------------------------------------------------------------------


def _run_optimised_waste_heat_case(
    project: Project,
    *,
    demand_profile: list[float],
    optimize_cap: bool,
    installed_capacity: float,
    capex_var: float,
) -> dict[str, Any]:
    _skip_if_solver_missing("cbc")

    energy_system, waste_heat, _, _, efficiency_hex = _build_eesyplan_system(
        project=project,
        optimize_cap=optimize_cap,
        demand_profile=demand_profile,
        installed_capacity=installed_capacity,
        capex_var=capex_var,
    )

    results = optimise(energy_system)
    assert results.__class__.__name__ == "Results"
    assert _eesyplan_solver_termination_condition(results) == "optimal"

    return {
        "energy_system": energy_system,
        "waste_heat": waste_heat,
        "efficiency_hex": efficiency_hex,
        "results": results,
        "solph_results": _solph_results(results),
        "heat_bus": waste_heat.bus_out_heat,
        "raw_heat_bus": waste_heat.bus_in_heat,
    }


def _run_waste_heat_reality_case(
    project: Project,
    *,
    demand_profile: list[float],
    raw_waste_heat_profile: list[float],
    raw_waste_heat_forced: bool,
    dump_sink_enabled: bool = False,
    dump_sink_variable_costs: float = 0.0,
    backup_boiler_enabled: bool = False,
    backup_boiler_variable_costs: float = 100.0,
    waste_heat_variable_costs: float = 0.0,
    optimize_cap: bool = False,
    installed_capacity: float | None = None,
    capex_var: float = 0.0,
) -> dict[str, Any]:
    _skip_if_solver_missing("cbc")

    case = _build_waste_heat_reality_system(
        project=project,
        demand_profile=demand_profile,
        raw_waste_heat_profile=raw_waste_heat_profile,
        raw_waste_heat_forced=raw_waste_heat_forced,
        dump_sink_enabled=dump_sink_enabled,
        dump_sink_variable_costs=dump_sink_variable_costs,
        backup_boiler_enabled=backup_boiler_enabled,
        backup_boiler_variable_costs=backup_boiler_variable_costs,
        waste_heat_variable_costs=waste_heat_variable_costs,
        optimize_cap=optimize_cap,
        installed_capacity=installed_capacity,
        capex_var=capex_var,
    )

    try:
        results = optimise(case["energy_system"])
    except RuntimeError as error:
        termination_condition = _termination_condition_from_runtime_error(
            error
        )
        if "infeasible" not in termination_condition:
            raise
        case.update(
            {
                "results": None,
                "solph_results": None,
                "solver_error": error,
                "termination_condition": termination_condition,
            }
        )
        return case

    termination_condition = _eesyplan_solver_termination_condition(results)
    case.update(
        {
            "results": results,
            "termination_condition": termination_condition,
            "solver_error": None,
            "solph_results": _solph_results(results)
            if termination_condition == "optimal"
            else None,
        }
    )
    return case


# ---------------------------------------------------------------------------
# Flow access helpers
# ---------------------------------------------------------------------------


def _useful_heat_output(case: dict[str, Any], length: int) -> list[float]:
    return _result_flow(
        case["solph_results"], case["waste_heat"], case["heat_bus"], length
    )


def _raw_heat_input(case: dict[str, Any], length: int) -> list[float]:
    return _result_flow(
        case["solph_results"], case["raw_heat_bus"], case["waste_heat"], length
    )


def _dump_flow(case: dict[str, Any], length: int) -> list[float]:
    assert case["dump_sink"] is not None
    return _result_flow(
        case["solph_results"], case["raw_heat_bus"], case["dump_sink"], length
    )


def _backup_heat_output(case: dict[str, Any], length: int) -> list[float]:
    assert case["backup_boiler"] is not None
    return _result_flow(
        case["solph_results"], case["backup_boiler"], case["heat_bus"], length
    )


def _waste_heat_investment(case: dict[str, Any]) -> float:
    return _result_scalar(
        case["solph_results"][(case["waste_heat"], case["heat_bus"])], "invest"
    )


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


class TestInputValidation:
    def test_empty_demand_profile_raises_value_error(
        self, project: Project
    ) -> None:
        with pytest.raises(
            ValueError, match="demand_profile must not be empty"
        ):
            _build_eesyplan_system(
                project=project,
                optimize_cap=False,
                demand_profile=[],
                installed_capacity=1.0,
                capex_var=0.0,
            )

    def test_negative_demand_profile_raises_value_error(
        self, project: Project
    ) -> None:
        with pytest.raises(
            ValueError, match="demand_profile must not contain negative values"
        ):
            _build_eesyplan_system(
                project=project,
                optimize_cap=False,
                demand_profile=[1.0, -2.0, 3.0],
                installed_capacity=3.0,
                capex_var=0.0,
            )


# ---------------------------------------------------------------------------
# Dispatch behaviour
# ---------------------------------------------------------------------------


class TestDispatchBehaviour:
    def test_waste_heat_direct_optimization_succeeds_with_solver(
        self, project: Project
    ) -> None:
        _skip_if_solver_missing("cbc")

        energy_system, *_ = _build_solph_dispatch_system(project)
        model = Model(energy_system)
        model.solve(solver="cbc")

        assert isinstance(model, Model)
        assert float(pyomo_value(model.objective)) == pytest.approx(0.0)

    def test_waste_heat_direct_solved_flows_match_expected_values(
        self, project: Project
    ) -> None:
        _skip_if_solver_missing("cbc")

        (
            energy_system,
            waste_heat,
            raw_heat_bus,
            heat_bus,
            raw_heat_profile,
            demand_profile,
            efficiency_hex,
        ) = _build_solph_dispatch_system(project)

        model = Model(energy_system)
        model.solve(solver="cbc")
        results = processing.results(model)

        raw_heat_input = _result_flow(
            results, raw_heat_bus, waste_heat, len(raw_heat_profile)
        )
        useful_heat_output = _result_flow(
            results, waste_heat, heat_bus, len(demand_profile)
        )

        assert raw_heat_input == pytest.approx(raw_heat_profile)
        assert useful_heat_output == pytest.approx(demand_profile)
        assert [
            value * efficiency_hex for value in raw_heat_input
        ] == pytest.approx(useful_heat_output)

    def test_waste_heat_direct_optimise_accepts_eesyplan_energy_system(
        self,
        project: Project,
    ) -> None:
        demand_profile = [8.0, 16.0, 24.0]

        energy_system, *_ = _build_eesyplan_system(
            project=project,
            optimize_cap=False,
            demand_profile=demand_profile,
            installed_capacity=max(demand_profile),
            capex_var=0.0,
        )

        _skip_if_solver_missing("cbc")
        results = optimise(energy_system)

        assert results.__class__.__name__ == "Results"
        assert _eesyplan_solver_termination_condition(results) == "optimal"
        assert _eesyplan_objective(results) == pytest.approx(0.0)
        assert hasattr(results, "_model")

    @pytest.mark.parametrize(
        ("demand_profile", "installed_capacity"),
        [
            ([0.0, 5.0, 12.0], 12.0),
            ([2.0, 6.0, 10.0], 10.0),
            ([2.0, 4.0, 1.0], 100.0),
        ],
    )
    def test_must_meet_demand_and_not_exceed_fixed_capacity(
        self,
        project: Project,
        demand_profile: list[float],
        installed_capacity: float,
    ) -> None:
        case = _run_optimised_waste_heat_case(
            project=project,
            demand_profile=demand_profile,
            optimize_cap=False,
            installed_capacity=installed_capacity,
            capex_var=0.0,
        )

        useful_heat_output = _useful_heat_output(case, len(demand_profile))
        raw_heat_input = _raw_heat_input(case, len(demand_profile))
        expected_raw_heat_input = [
            value / case["efficiency_hex"] for value in demand_profile
        ]

        assert useful_heat_output == pytest.approx(demand_profile)
        assert all(
            value <= installed_capacity + 1e-8 for value in useful_heat_output
        )
        assert raw_heat_input == pytest.approx(expected_raw_heat_input)

        for raw_input, useful_output in zip(
            raw_heat_input, useful_heat_output, strict=True
        ):
            assert useful_output == pytest.approx(
                raw_input * case["efficiency_hex"]
            )


# ---------------------------------------------------------------------------
# Investment behaviour
# ---------------------------------------------------------------------------


class TestInvestmentBehaviour:
    def test_must_waste_heat_direct_investment_capacity_matches_peak_demand(
        self,
        project: Project,
    ) -> None:
        demand_profile = [4.0, 8.0, 12.0]

        case = _run_optimised_waste_heat_case(
            project=project,
            demand_profile=demand_profile,
            optimize_cap=True,
            installed_capacity=0.0,
            capex_var=100.0,
        )

        assert _waste_heat_investment(case) == pytest.approx(
            max(demand_profile)
        )

    def test_must_waste_heat_direct_investment_costs_are_in_objective(
        self,
        project: Project,
    ) -> None:
        demand_profile = [4.0, 8.0, 12.0]

        case = _run_optimised_waste_heat_case(
            project=project,
            demand_profile=demand_profile,
            optimize_cap=True,
            installed_capacity=0.0,
            capex_var=100.0,
        )

        investment = _waste_heat_investment(case)
        ep_costs = _investment_ep_costs(case["waste_heat"], case["heat_bus"])
        expected_objective = investment * ep_costs

        assert _eesyplan_objective(case["results"]) == pytest.approx(
            expected_objective
        )

    def test_must_waste_heat_direct_zero_demand_causes_no_use_and_no_investment(
        self,
        project: Project,
    ) -> None:
        demand_profile = [0.0, 0.0, 0.0]

        case = _run_optimised_waste_heat_case(
            project=project,
            demand_profile=demand_profile,
            optimize_cap=True,
            installed_capacity=0.0,
            capex_var=100.0,
        )

        assert _useful_heat_output(case, len(demand_profile)) == pytest.approx(
            demand_profile
        )
        assert _raw_heat_input(case, len(demand_profile)) == pytest.approx(
            demand_profile
        )
        assert _waste_heat_investment(case) == pytest.approx(0.0)
        assert _eesyplan_objective(case["results"]) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Reality constraints
# ---------------------------------------------------------------------------


class TestRealityConstraints:
    @pytest.mark.parametrize(
        ("raw_waste_heat_forced", "expected_termination"),
        [
            (False, "optimal"),
            (True, "infeasible"),
        ],
    )
    def test_surplus_waste_heat_without_dump_sink_behaves_as_expected(
        self,
        project: Project,
        raw_waste_heat_forced: bool,
        expected_termination: str,
    ) -> None:
        demand_profile = [4.0, 8.0, 12.0]
        raw_waste_heat_profile = [20.0, 20.0, 20.0]

        case = _run_waste_heat_reality_case(
            project=project,
            demand_profile=demand_profile,
            raw_waste_heat_profile=raw_waste_heat_profile,
            raw_waste_heat_forced=raw_waste_heat_forced,
            dump_sink_enabled=False,
            backup_boiler_enabled=False,
            installed_capacity=max(demand_profile),
        )

        assert expected_termination in case["termination_condition"]

        if expected_termination == "optimal":
            useful_heat_output = _useful_heat_output(case, len(demand_profile))
            raw_heat_input = _raw_heat_input(case, len(demand_profile))
            expected_raw_heat_input = [
                demand / case["efficiency_hex"] for demand in demand_profile
            ]

            assert useful_heat_output == pytest.approx(demand_profile)
            assert raw_heat_input == pytest.approx(expected_raw_heat_input)
            assert _eesyplan_objective(case["results"]) == pytest.approx(0.0)
        else:
            assert case["results"] is None
            assert case["solph_results"] is None

    def test_fixed_capacity_below_peak_demand_becomes_infeasible(
        self, project: Project
    ) -> None:
        demand_profile = [4.0, 8.0, 12.0]
        raw_waste_heat_profile = [20.0, 20.0, 20.0]

        case = _run_waste_heat_reality_case(
            project=project,
            demand_profile=demand_profile,
            raw_waste_heat_profile=raw_waste_heat_profile,
            raw_waste_heat_forced=False,
            dump_sink_enabled=False,
            backup_boiler_enabled=False,
            waste_heat_variable_costs=0.0,
            optimize_cap=False,
            installed_capacity=10.0,
        )

        assert "infeasible" in case["termination_condition"]
        assert case["results"] is None
        assert case["solph_results"] is None

    def test_forced_surplus_dump_sink_costs_are_in_objective(
        self, project: Project
    ) -> None:
        demand_profile = [4.0, 8.0, 12.0]
        raw_waste_heat_profile = [20.0, 20.0, 20.0]
        dump_sink_variable_costs = 3.0

        case = _run_waste_heat_reality_case(
            project=project,
            demand_profile=demand_profile,
            raw_waste_heat_profile=raw_waste_heat_profile,
            raw_waste_heat_forced=True,
            dump_sink_enabled=True,
            dump_sink_variable_costs=dump_sink_variable_costs,
            backup_boiler_enabled=False,
            installed_capacity=max(demand_profile),
        )

        assert case["termination_condition"] == "optimal"

        dump_flow = _dump_flow(case, len(demand_profile))
        expected_objective = sum(dump_flow) * dump_sink_variable_costs

        assert _eesyplan_objective(case["results"]) == pytest.approx(
            expected_objective
        )

    @pytest.mark.parametrize(
        ("backup_boiler_enabled", "expected_termination"),
        [
            (False, "infeasible"),
            (True, "optimal"),
        ],
    )
    def test_waste_heat_shortage_behaves_as_expected(
        self,
        project: Project,
        backup_boiler_enabled: bool,
        expected_termination: str,
    ) -> None:
        demand_profile = [4.0, 8.0, 12.0]
        raw_waste_heat_profile = [2.0, 2.0, 2.0]

        case = _run_waste_heat_reality_case(
            project=project,
            demand_profile=demand_profile,
            raw_waste_heat_profile=raw_waste_heat_profile,
            raw_waste_heat_forced=False,
            dump_sink_enabled=False,
            backup_boiler_enabled=backup_boiler_enabled,
            backup_boiler_variable_costs=100.0,
            waste_heat_variable_costs=0.0,
            installed_capacity=max(demand_profile),
        )

        assert expected_termination in case["termination_condition"]

        if expected_termination == "infeasible":
            assert case["results"] is None
            assert case["solph_results"] is None

    def test_backup_is_preferred_when_cheaper_than_waste_heat(
        self, project: Project
    ) -> None:
        demand_profile = [4.0, 8.0, 12.0]
        raw_waste_heat_profile = [20.0, 20.0, 20.0]

        case = _run_waste_heat_reality_case(
            project=project,
            demand_profile=demand_profile,
            raw_waste_heat_profile=raw_waste_heat_profile,
            raw_waste_heat_forced=False,
            dump_sink_enabled=False,
            backup_boiler_enabled=True,
            backup_boiler_variable_costs=10.0,
            waste_heat_variable_costs=20.0,
            optimize_cap=False,
            installed_capacity=max(demand_profile),
        )

        assert case["termination_condition"] == "optimal"

        useful_heat_output = _useful_heat_output(case, len(demand_profile))
        raw_heat_input = _raw_heat_input(case, len(demand_profile))
        backup_heat_output = _backup_heat_output(case, len(demand_profile))

        assert useful_heat_output == pytest.approx([0.0, 0.0, 0.0])
        assert raw_heat_input == pytest.approx([0.0, 0.0, 0.0])
        assert backup_heat_output == pytest.approx(demand_profile)

    def test_backup_boiler_covers_residual_demand(
        self, project: Project
    ) -> None:
        demand_profile = [4.0, 8.0, 12.0]
        raw_waste_heat_profile = [5.0, 5.0, 5.0]

        case = _run_waste_heat_reality_case(
            project=project,
            demand_profile=demand_profile,
            raw_waste_heat_profile=raw_waste_heat_profile,
            raw_waste_heat_forced=False,
            dump_sink_enabled=False,
            backup_boiler_enabled=True,
            backup_boiler_variable_costs=100.0,
            waste_heat_variable_costs=0.0,
            installed_capacity=max(demand_profile),
        )

        assert case["termination_condition"] == "optimal"

        useful_heat_output = _useful_heat_output(case, len(demand_profile))
        raw_heat_input = _raw_heat_input(case, len(demand_profile))
        backup_heat_output = _backup_heat_output(case, len(demand_profile))

        expected_waste_heat_output = [
            min(demand, raw_available * case["efficiency_hex"])
            for demand, raw_available in zip(
                demand_profile,
                raw_waste_heat_profile,
                strict=True,
            )
        ]
        expected_raw_heat_input = [
            useful_output / case["efficiency_hex"]
            for useful_output in expected_waste_heat_output
        ]
        expected_backup_heat_output = [
            demand - waste_output
            for demand, waste_output in zip(
                demand_profile,
                expected_waste_heat_output,
                strict=True,
            )
        ]

        assert useful_heat_output == pytest.approx(expected_waste_heat_output)
        assert raw_heat_input == pytest.approx(expected_raw_heat_input)
        assert backup_heat_output == pytest.approx(expected_backup_heat_output)
