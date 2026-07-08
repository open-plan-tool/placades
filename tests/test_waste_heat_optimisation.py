"""Optimisation tests for the direct waste heat component."""

from __future__ import annotations

from typing import Any

import pytest
from oemof.solph import Bus
from oemof.solph import EnergySystem as SolphEnergySystem
from oemof.solph import Flow
from oemof.solph import Model
from oemof.solph import processing
from oemof.solph.components import Sink
from oemof.solph.components import Source
from pyomo.environ import SolverFactory
from pyomo.environ import value as pyomo_value

from oemof.eesyplan import EnergySystem as EesyplanEnergySystem
from oemof.eesyplan import Project
from oemof.eesyplan import optimise
from oemof.eesyplan.components.converters.waste_heat import WasteHeatDirect


def _eesyplan_solver_termination_condition(results: Any) -> str:
    """Return solver termination condition from eesyplan Results."""
    solver_results = results._solver_results
    return str(solver_results["Solver"][0]["Termination condition"]).lower()


def _eesyplan_objective(results: Any) -> float:
    """Return objective value from eesyplan Results."""
    return float(results._meta_results["objective"])


def _solph_results_from_eesyplan_results(results: Any) -> dict[Any, Any]:
    """Return solph processing results from eesyplan Results."""
    return processing.results(results._model)


def _looks_like_solph_results(candidate: Any) -> bool:
    """Return whether candidate looks like solph processing results."""
    return isinstance(candidate, dict) and any(
        isinstance(key, tuple) and len(key) == 2 for key in candidate.keys()
    )


def _termination_condition_from_runtime_error(
    error: RuntimeError,
) -> str:
    """Extract solver termination condition from optimise RuntimeError."""
    message = str(error).lower()

    marker = "termination condition:"
    if marker in message:
        return message.split(marker, 1)[1].splitlines()[0].strip()

    if "infeasible" in message:
        return "infeasible"

    return "runtime_error"


def _find_solph_results(*objects: Any) -> dict[Any, Any]:
    """Find solph result dict inside eesyplan results or energy system."""
    visited: set[int] = set()

    def walk(obj: Any) -> dict[Any, Any] | None:
        object_id = id(obj)
        if object_id in visited:
            return None

        visited.add(object_id)

        if _looks_like_solph_results(obj):
            return obj

        if isinstance(obj, dict):
            for key in ("main", "results", "flow"):
                candidate = obj.get(key)
                found = walk(candidate)
                if found is not None:
                    return found

            for value in obj.values():
                found = walk(value)
                if found is not None:
                    return found

        if hasattr(obj, "__dict__"):
            for value in vars(obj).values():
                found = walk(value)
                if found is not None:
                    return found

        return None

    for obj in objects:
        found = walk(obj)
        if found is not None:
            return found

    raise AssertionError(
        "Could not find solph processing results in optimise result "
        "or energy system."
    )


def _skip_if_solver_missing(solver: str = "cbc") -> None:
    """Skip test if the required solver is not available."""
    if not SolverFactory(solver).available(exception_flag=False):
        pytest.skip(f"Solver {solver!r} is not available.")


def _first(value: Any) -> float:
    """Return first scalar value from scalar or sequence-like solph data."""
    try:
        return float(value[0])
    except TypeError:
        return float(value)


def _is_nan(value: Any) -> bool:
    """Return True for NaN-like values."""
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
    """Extract a flow sequence from solph results with deterministic length."""
    edge_results = results[(from_node, to_node)]
    flow_sequence = edge_results["sequences"]["flow"]

    raw_values = list(flow_sequence)

    # solph often contains one terminal NaN after the last optimisation step.
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


def _require_non_empty_profile(
    name: str,
    profile: list[float],
) -> None:
    """Require a non-empty time series profile."""
    if not profile:
        raise ValueError(f"{name} must not be empty.")


def _require_non_negative_profile(
    name: str,
    profile: list[float],
) -> None:
    """Require all profile values to be non-negative."""
    negative_values = [value for value in profile if value < 0]

    if negative_values:
        raise ValueError(
            f"{name} must not contain negative values. "
            f"Found: {negative_values!r}"
        )


def _require_same_profile_length(
    first_name: str,
    first_profile: list[float],
    second_name: str,
    second_profile: list[float],
) -> None:
    """Require two profiles to have identical length."""
    if len(first_profile) != len(second_profile):
        raise ValueError(
            f"{first_name} and {second_name} must have the same length. "
            f"Got {len(first_profile)} and {len(second_profile)}."
        )


def _nominal_and_normalised_profile(
    profile: list[float],
) -> tuple[float, list[float]]:
    """Return a safe nominal value and the profile normalised by it."""
    nominal_capacity = max(max(profile), 1.0)
    normalised_profile = [value / nominal_capacity for value in profile]

    return nominal_capacity, normalised_profile


def _result_scalar(edge_results: dict[str, Any], name: str) -> float:
    """Return scalar result value whose key contains a given name."""
    scalars = edge_results["scalars"]

    for key, value in scalars.items():
        if name in str(key):
            return float(value)

    raise AssertionError(
        f"Could not find scalar result containing {name!r}. "
        f"Available scalars: {list(scalars.index)}"
    )


def _label_matches(value: Any, label: str) -> bool:
    """Return whether a result label matches a string label."""
    text = str(value)
    return text == label or f"'{label}'" in text


def _mapping_value_by_label(mapping: dict[Any, Any], label: str) -> Any:
    """Return mapping value by stringified key label."""
    if label in mapping:
        return mapping[label]

    for key, value in mapping.items():
        if _label_matches(key, label):
            return value

    raise AssertionError(
        f"Could not find key {label!r}. "
        f"Available keys: {[str(key) for key in mapping]}"
    )


def _parsed_flow(
    flows: dict[Any, Any],
    from_label: str,
    to_label: str,
    length: int,
) -> list[float]:
    """Return parsed eesyplan flow results by labels."""
    frame = _mapping_value_by_label(flows, from_label)

    if hasattr(frame, "columns"):
        for column in frame.columns:
            if _label_matches(column, to_label):
                series = frame[column]
                return [float(value) for value in series.iloc[:length]]

        if len(frame.columns) == 1:
            series = frame.iloc[:, 0]
            return [float(value) for value in series.iloc[:length]]

        raise AssertionError(
            f"Could not find column {to_label!r} in flow {from_label!r}. "
            f"Available columns: {[str(column) for column in frame.columns]}"
        )

    series = frame.squeeze()
    return [float(value) for value in series.iloc[:length]]


@pytest.fixture
def project() -> Project:
    """Return minimal eesyplan project data."""
    return Project(
        name="Project_X",
        lifetime=20,
        tax=0,
        discount_factor=0.01,
    )


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
    """Build minimal solph system with fixed waste heat dispatch."""
    pd = pytest.importorskip("pandas")

    raw_heat_profile = [10.0, 20.0, 30.0]
    efficiency_hex = 0.8
    demand_profile = [8.0, 16.0, 24.0]

    timeindex = pd.date_range(
        "2026-01-01",
        periods=len(raw_heat_profile),
        freq="h",
    )

    energy_system = SolphEnergySystem(
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
        installed_capacity=max(demand_profile),
        optimize_cap=False,
        heat_cost=0.0,
        efficiency_hex=efficiency_hex,
        opex_var=0.0,
    )

    demand_nominal_capacity = max(demand_profile)
    demand_fix = [value / demand_nominal_capacity for value in demand_profile]

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

    return (
        energy_system,
        waste_heat,
        raw_heat_bus,
        heat_bus,
        raw_heat_profile,
        demand_profile,
        efficiency_hex,
    )


def test_waste_heat_direct_optimization_succeeds_with_solver(
    project: Project,
) -> None:
    """Test that a minimal waste heat optimisation solves successfully."""
    _skip_if_solver_missing("cbc")

    energy_system, *_ = _build_solph_dispatch_system(project)

    model = Model(energy_system)
    model.solve(solver="cbc")

    assert isinstance(model, Model)

    objective_value = float(pyomo_value(model.objective))
    assert objective_value == pytest.approx(0.0)


def test_waste_heat_direct_solved_flows_match_expected_values(
    project: Project,
) -> None:
    """Test solved input and output flows of the waste heat component."""
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
        results=results,
        from_node=raw_heat_bus,
        to_node=waste_heat,
        length=len(raw_heat_profile),
    )
    useful_heat_output = _result_flow(
        results=results,
        from_node=waste_heat,
        to_node=heat_bus,
        length=len(demand_profile),
    )

    assert raw_heat_input == pytest.approx(raw_heat_profile)
    assert useful_heat_output == pytest.approx(demand_profile)

    assert [
        value * efficiency_hex for value in raw_heat_input
    ] == pytest.approx(useful_heat_output)


def test_waste_heat_direct_investment_costs_are_in_objective(
    project: Project,
) -> None:
    """Test that investment costs are represented in the objective."""
    _skip_if_solver_missing("cbc")
    pd = pytest.importorskip("pandas")

    raw_heat_profile = [10.0, 20.0, 30.0]
    efficiency_hex = 0.8
    demand_profile = [4.0, 8.0, 12.0]

    timeindex = pd.date_range(
        "2026-01-01",
        periods=len(raw_heat_profile),
        freq="h",
    )

    energy_system = SolphEnergySystem(
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
        capex_fix=0.0,
        capex_var=100.0,
        opex_fix=0.0,
        opex_var=0.0,
        lifetime=20,
        optimize_cap=True,
        maximum_capacity=None,
        heat_cost=0.0,
        efficiency_hex=efficiency_hex,
    )

    demand_nominal_capacity = max(demand_profile)
    demand_fix = [value / demand_nominal_capacity for value in demand_profile]

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
    model.solve(solver="cbc")
    results = processing.results(model)

    edge_results = results[(waste_heat, heat_bus)]
    invest = _result_scalar(edge_results, "invest")

    investment = waste_heat.outputs[heat_bus].investment
    ep_costs = _first(investment.ep_costs)

    expected_investment = max(demand_profile)
    expected_objective = expected_investment * ep_costs

    assert invest == pytest.approx(expected_investment)
    assert pyomo_value(model.objective) == pytest.approx(expected_objective)


def _build_eesyplan_system(
    project: Project,
    *,
    optimize_cap: bool,
    demand_profile: list[float],
    installed_capacity: float,
    capex_var: float,
) -> tuple[
    EesyplanEnergySystem,
    WasteHeatDirect,
    list[float],
    list[float],
    float,
]:
    """Build minimal eesyplan energy system for waste heat tests."""
    _require_non_empty_profile("demand_profile", demand_profile)
    _require_non_negative_profile("demand_profile", demand_profile)

    efficiency_hex = 0.8

    # Keep the minimal builder technically feasible by default.
    # The raw heat profile is sized to cover the useful heat demand.
    # For zero-demand timesteps we keep a small positive potential to avoid
    # zero-nominal edge cases in components that normalise internally.
    raw_heat_profile = [
        max(value / efficiency_hex, 1.0) for value in demand_profile
    ]

    energy_system = EesyplanEnergySystem(
        2026,
        number=len(demand_profile),
    )

    raw_heat_bus = Bus(label="raw_waste_heat")
    heat_bus = Bus(label="heat")

    raw_heat_nominal_capacity, raw_heat_max = _nominal_and_normalised_profile(
        raw_heat_profile
    )

    raw_heat_source = Source(
        label="raw_waste_heat_source",
        outputs={
            raw_heat_bus: Flow(
                nominal_capacity=raw_heat_nominal_capacity,
                maximum=raw_heat_max,
            )
        },
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

    demand_nominal_capacity, demand_fix = _nominal_and_normalised_profile(
        demand_profile
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
    """Build an eesyplan waste heat system for reality tests."""
    _require_non_empty_profile("demand_profile", demand_profile)
    _require_non_empty_profile(
        "raw_waste_heat_profile",
        raw_waste_heat_profile,
    )
    _require_same_profile_length(
        "demand_profile",
        demand_profile,
        "raw_waste_heat_profile",
        raw_waste_heat_profile,
    )
    _require_non_negative_profile("demand_profile", demand_profile)
    _require_non_negative_profile(
        "raw_waste_heat_profile",
        raw_waste_heat_profile,
    )

    if installed_capacity is None:
        installed_capacity = max(max(demand_profile), 1.0)

    energy_system = EesyplanEnergySystem(
        2026,
        number=len(demand_profile),
    )

    raw_heat_bus = Bus(label="raw_waste_heat")
    heat_bus = Bus(label="heat")

    raw_heat_nominal_capacity, raw_heat_profile_normalised = (
        _nominal_and_normalised_profile(raw_waste_heat_profile)
    )

    if raw_waste_heat_forced:
        raw_heat_flow = Flow(
            nominal_capacity=raw_heat_nominal_capacity,
            fix=raw_heat_profile_normalised,
        )
    else:
        raw_heat_flow = Flow(
            nominal_capacity=raw_heat_nominal_capacity,
            maximum=raw_heat_profile_normalised,
        )

    raw_heat_source = Source(
        label="raw_waste_heat_source",
        outputs={
            raw_heat_bus: raw_heat_flow,
        },
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

    demand_nominal_capacity, demand_fix = _nominal_and_normalised_profile(
        demand_profile
    )

    heat_demand = Sink(
        label="heat_demand",
        inputs={
            heat_bus: Flow(
                nominal_capacity=demand_nominal_capacity,
                fix=demand_fix,
            )
        },
    )

    dump_sink = None

    if dump_sink_enabled:
        dump_sink = Sink(
            label="raw_waste_heat_dump_sink",
            inputs={
                raw_heat_bus: Flow(
                    variable_costs=dump_sink_variable_costs,
                )
            },
        )

    backup_boiler = None

    if backup_boiler_enabled:
        # For this test builder, the backup boiler is represented as a simple
        # heat source. This is enough to test residual heat coverage and
        # economic dispatch without adding fuel-bus complexity.
        backup_boiler = Source(
            label="backup_boiler",
            outputs={
                heat_bus: Flow(
                    variable_costs=backup_boiler_variable_costs,
                )
            },
        )

    components = [
        raw_heat_bus,
        heat_bus,
        raw_heat_source,
        waste_heat,
        heat_demand,
    ]

    if dump_sink is not None:
        components.append(dump_sink)

    if backup_boiler is not None:
        components.append(backup_boiler)

    energy_system.add(*components)

    return {
        "energy_system": energy_system,
        "waste_heat": waste_heat,
        "raw_heat_bus": raw_heat_bus,
        "heat_bus": heat_bus,
        "raw_heat_source": raw_heat_source,
        "heat_demand": heat_demand,
        "dump_sink": dump_sink,
        "backup_boiler": backup_boiler,
        "demand_profile": demand_profile,
        "raw_waste_heat_profile": raw_waste_heat_profile,
        "efficiency_hex": efficiency_hex,
        "dump_sink_variable_costs": dump_sink_variable_costs,
        "backup_boiler_variable_costs": backup_boiler_variable_costs,
        "waste_heat_variable_costs": waste_heat_variable_costs,
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
    """Build and optimise a waste heat reality case."""
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

        case["results"] = None
        case["solph_results"] = None
        case["solver_error"] = error
        case["termination_condition"] = termination_condition

        return case

    assert results.__class__.__name__ == "Results"

    termination_condition = _eesyplan_solver_termination_condition(results)

    case["results"] = results
    case["termination_condition"] = termination_condition
    case["solver_error"] = None

    if termination_condition == "optimal":
        case["solph_results"] = _solph_results_from_eesyplan_results(results)
    else:
        case["solph_results"] = None

    return case


def _reality_useful_heat_output(
    case: dict[str, Any],
) -> list[float]:
    """Return useful heat output from waste heat component."""
    return _result_flow(
        results=case["solph_results"],
        from_node=case["waste_heat"],
        to_node=case["heat_bus"],
        length=len(case["demand_profile"]),
    )


def _reality_raw_heat_input(
    case: dict[str, Any],
) -> list[float]:
    """Return raw heat input into waste heat component."""
    return _result_flow(
        results=case["solph_results"],
        from_node=case["raw_heat_bus"],
        to_node=case["waste_heat"],
        length=len(case["demand_profile"]),
    )


def _reality_dump_flow(
    case: dict[str, Any],
) -> list[float]:
    """Return raw waste heat dumped into dump sink."""
    assert case["dump_sink"] is not None

    return _result_flow(
        results=case["solph_results"],
        from_node=case["raw_heat_bus"],
        to_node=case["dump_sink"],
        length=len(case["demand_profile"]),
    )


def _reality_backup_heat_output(
    case: dict[str, Any],
) -> list[float]:
    """Return useful heat output from backup boiler."""
    assert case["backup_boiler"] is not None

    return _result_flow(
        results=case["solph_results"],
        from_node=case["backup_boiler"],
        to_node=case["heat_bus"],
        length=len(case["demand_profile"]),
    )


def test_waste_heat_direct_optimise_accepts_eesyplan_energy_system(
    project: Project,
) -> None:
    """Test waste heat component with eesyplan EnergySystem and optimise."""
    _skip_if_solver_missing("cbc")

    demand_profile = [8.0, 16.0, 24.0]

    energy_system, *_ = _build_eesyplan_system(
        project=project,
        optimize_cap=False,
        demand_profile=demand_profile,
        installed_capacity=max(demand_profile),
        capex_var=0.0,
    )

    results = optimise(energy_system)

    assert results.__class__.__name__ == "Results"
    assert _eesyplan_solver_termination_condition(results) == "optimal"
    assert _eesyplan_objective(results) == pytest.approx(0.0)
    assert hasattr(results, "_model")


def test_waste_heat_direct_result_parsing_contains_flows_and_investment(
    project: Project,
) -> None:
    """Test eesyplan result access for waste heat flows and investment."""
    _skip_if_solver_missing("cbc")

    demand_profile = [4.0, 8.0, 12.0]

    (
        energy_system,
        waste_heat,
        _,
        _,
        efficiency_hex,
    ) = _build_eesyplan_system(
        project=project,
        optimize_cap=True,
        demand_profile=demand_profile,
        installed_capacity=0.0,
        capex_var=100.0,
    )

    results = optimise(energy_system)

    assert results.__class__.__name__ == "Results"
    assert _eesyplan_solver_termination_condition(results) == "optimal"

    solph_results = _solph_results_from_eesyplan_results(results)

    heat_bus = waste_heat.bus_out_heat
    raw_heat_bus = waste_heat.bus_in_heat

    useful_heat_output = _result_flow(
        results=solph_results,
        from_node=waste_heat,
        to_node=heat_bus,
        length=len(demand_profile),
    )

    raw_heat_input = _result_flow(
        results=solph_results,
        from_node=raw_heat_bus,
        to_node=waste_heat,
        length=len(demand_profile),
    )

    expected_raw_heat_input = [
        value / efficiency_hex for value in demand_profile
    ]

    assert useful_heat_output == pytest.approx(demand_profile)
    assert raw_heat_input == pytest.approx(expected_raw_heat_input)

    edge_results = solph_results[(waste_heat, heat_bus)]
    investment = _result_scalar(edge_results, "invest")

    assert investment == pytest.approx(max(demand_profile))


# =============================================================================
# WasteHeatDirect: additional must-have and reality tests

# These tests verify:
# - whether the component meets the demand,
# - whether the energy equation is correct,
# - whether the capacity is respected,
# - whether investments are correctly sized,
# - whether investment costs are included in the objective,
# - whether nothing happens at zero demand,
# - whether excess capacity does not generate additional heat,
# - whether time-dependent profiles are tracked correctly.
# =============================================================================


def _value_as_float(value: Any) -> float:
    """Return scalar-like values as float.

    Handles plain numbers, pandas objects and oemof/solph sequence objects.
    """
    if value is None:
        raise TypeError("Cannot convert None to float.")

    # oemof.solph often stores scalar sequence values internally as _value.
    # This must be checked before trying to iterate over the object.
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
    """Return annuitized investment costs from the waste heat output flow."""
    investment = waste_heat.outputs[heat_bus].investment
    return _value_as_float(investment.ep_costs)


def _run_optimised_waste_heat_case(
    project: Any,
    demand_profile: list[float],
    optimize_cap: bool,
    installed_capacity: float,
    capex_var: float,
) -> dict[str, Any]:
    """Build and optimise a minimal eesyplan waste heat system."""
    _skip_if_solver_missing("cbc")

    (
        energy_system,
        waste_heat,
        _,
        _,
        efficiency_hex,
    ) = _build_eesyplan_system(
        project=project,
        optimize_cap=optimize_cap,
        demand_profile=demand_profile,
        installed_capacity=installed_capacity,
        capex_var=capex_var,
    )

    results = optimise(energy_system)

    assert results.__class__.__name__ == "Results"
    assert _eesyplan_solver_termination_condition(results) == "optimal"

    solph_results = _solph_results_from_eesyplan_results(results)

    heat_bus = waste_heat.bus_out_heat
    raw_heat_bus = waste_heat.bus_in_heat

    return {
        "energy_system": energy_system,
        "waste_heat": waste_heat,
        "efficiency_hex": efficiency_hex,
        "results": results,
        "solph_results": solph_results,
        "heat_bus": heat_bus,
        "raw_heat_bus": raw_heat_bus,
    }


def _useful_heat_output(case: dict[str, Any], length: int) -> list[float]:
    """Return useful heat output from WasteHeatDirect to heat bus."""
    return _result_flow(
        results=case["solph_results"],
        from_node=case["waste_heat"],
        to_node=case["heat_bus"],
        length=length,
    )


def _raw_heat_input(case: dict[str, Any], length: int) -> list[float]:
    """Return raw waste heat input from raw heat bus to WasteHeatDirect."""
    return _result_flow(
        results=case["solph_results"],
        from_node=case["raw_heat_bus"],
        to_node=case["waste_heat"],
        length=length,
    )


def _waste_heat_investment(case: dict[str, Any]) -> float:
    """Return invested useful heat capacity of WasteHeatDirect."""
    edge_results = case["solph_results"][
        (case["waste_heat"], case["heat_bus"])
    ]
    return _result_scalar(edge_results, "invest")


# =============================================================================
# Muss-Tests
# =============================================================================


def test_must_waste_heat_direct_meets_demand_with_sufficient_capacity(
    project: Any,
) -> None:
    """WasteHeatDirect must meet heat demand if potential and capacity exist."""
    demand_profile = [4.0, 8.0, 12.0]

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=False,
        installed_capacity=max(demand_profile),
        capex_var=0.0,
    )

    useful_heat_output = _useful_heat_output(
        case=case,
        length=len(demand_profile),
    )

    assert useful_heat_output == pytest.approx(demand_profile)


def test_must_waste_heat_direct_energy_balance_follows_efficiency(
    project: Any,
) -> None:
    """WasteHeatDirect must respect Q_out = Q_in * efficiency_hex."""
    demand_profile = [3.0, 7.5, 11.0]

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=False,
        installed_capacity=max(demand_profile),
        capex_var=0.0,
    )

    useful_heat_output = _useful_heat_output(
        case=case,
        length=len(demand_profile),
    )
    raw_heat_input = _raw_heat_input(
        case=case,
        length=len(demand_profile),
    )

    efficiency_hex = case["efficiency_hex"]

    for raw_input, useful_output in zip(
        raw_heat_input, useful_heat_output, strict=True
    ):
        assert useful_output == pytest.approx(raw_input * efficiency_hex)


def test_must_waste_heat_direct_input_equals_output_divided_by_efficiency(
    project: Any,
) -> None:
    """Raw waste heat input must equal useful heat demand divided by efficiency."""
    demand_profile = [5.0, 10.0, 15.0]

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=False,
        installed_capacity=max(demand_profile),
        capex_var=0.0,
    )

    raw_heat_input = _raw_heat_input(
        case=case,
        length=len(demand_profile),
    )

    expected_raw_heat_input = [
        value / case["efficiency_hex"] for value in demand_profile
    ]

    assert raw_heat_input == pytest.approx(expected_raw_heat_input)


def test_must_waste_heat_direct_fixed_capacity_is_not_exceeded(
    project: Any,
) -> None:
    """Useful heat output must never exceed installed useful heat capacity."""
    demand_profile = [2.0, 6.0, 10.0]
    installed_capacity = 10.0

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=False,
        installed_capacity=installed_capacity,
        capex_var=0.0,
    )

    useful_heat_output = _useful_heat_output(
        case=case,
        length=len(demand_profile),
    )

    assert all(
        value <= installed_capacity + 1e-8 for value in useful_heat_output
    )


def test_must_waste_heat_direct_investment_capacity_matches_peak_demand(
    project: Any,
) -> None:
    """Investment capacity must match peak useful heat demand if economic."""
    demand_profile = [4.0, 8.0, 12.0]

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=True,
        installed_capacity=0.0,
        capex_var=100.0,
    )

    investment = _waste_heat_investment(case)

    assert investment == pytest.approx(max(demand_profile))


def test_must_waste_heat_direct_investment_costs_are_in_objective(
    project: Any,
) -> None:
    """Objective must contain annuitized investment costs."""
    demand_profile = [4.0, 8.0, 12.0]

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=True,
        installed_capacity=0.0,
        capex_var=100.0,
    )

    investment = _waste_heat_investment(case)
    ep_costs = _investment_ep_costs(
        waste_heat=case["waste_heat"],
        heat_bus=case["heat_bus"],
    )

    expected_objective = investment * ep_costs

    assert _eesyplan_objective(case["results"]) == pytest.approx(
        expected_objective
    )


def test_must_waste_heat_direct_zero_demand_causes_no_use_and_no_investment(
    project: Any,
) -> None:
    """Zero heat demand must lead to zero operation and zero investment."""
    demand_profile = [0.0, 0.0, 0.0]

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=True,
        installed_capacity=0.0,
        capex_var=100.0,
    )

    useful_heat_output = _useful_heat_output(
        case=case,
        length=len(demand_profile),
    )
    raw_heat_input = _raw_heat_input(
        case=case,
        length=len(demand_profile),
    )
    investment = _waste_heat_investment(case)

    assert useful_heat_output == pytest.approx(demand_profile)
    assert raw_heat_input == pytest.approx(demand_profile)
    assert investment == pytest.approx(0.0)
    assert _eesyplan_objective(case["results"]) == pytest.approx(0.0)


# =============================================================================
# Realitätstests
# =============================================================================


def test_reality_oversized_capacity_does_not_create_extra_heat(
    project: Any,
) -> None:
    """Oversized waste heat capacity must not create heat without demand."""
    demand_profile = [2.0, 4.0, 1.0]
    installed_capacity = 100.0

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=False,
        installed_capacity=installed_capacity,
        capex_var=0.0,
    )

    useful_heat_output = _useful_heat_output(
        case=case,
        length=len(demand_profile),
    )

    assert useful_heat_output == pytest.approx(demand_profile)
    assert max(useful_heat_output) < installed_capacity


def test_reality_oversized_capacity_has_no_additional_cost_without_investment(
    project: Any,
) -> None:
    """Unused fixed capacity must not increase the objective if capex is zero."""
    demand_profile = [2.0, 4.0, 1.0]

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=False,
        installed_capacity=100.0,
        capex_var=0.0,
    )

    assert _eesyplan_objective(case["results"]) == pytest.approx(0.0)


def test_reality_investment_is_sized_to_useful_peak_not_raw_heat_peak(
    project: Any,
) -> None:
    """Investment must be based on useful heat output, not raw waste heat input."""
    demand_profile = [4.0, 8.0, 12.0]

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=True,
        installed_capacity=0.0,
        capex_var=100.0,
    )

    raw_heat_input = _raw_heat_input(
        case=case,
        length=len(demand_profile),
    )
    investment = _waste_heat_investment(case)

    useful_heat_peak = max(demand_profile)
    raw_heat_peak = max(raw_heat_input)

    assert raw_heat_peak > useful_heat_peak
    assert investment == pytest.approx(useful_heat_peak)
    assert investment < raw_heat_peak


def test_reality_time_dependent_demand_profile_is_followed_per_timestep(
    project: Any,
) -> None:
    """Waste heat output must follow the time-dependent heat demand profile."""
    demand_profile = [0.0, 5.0, 2.0]

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=False,
        installed_capacity=max(demand_profile),
        capex_var=0.0,
    )

    useful_heat_output = _useful_heat_output(
        case=case,
        length=len(demand_profile),
    )
    raw_heat_input = _raw_heat_input(
        case=case,
        length=len(demand_profile),
    )

    expected_raw_heat_input = [
        value / case["efficiency_hex"] for value in demand_profile
    ]

    assert useful_heat_output == pytest.approx(demand_profile)
    assert raw_heat_input == pytest.approx(expected_raw_heat_input)


def test_reality_no_operation_in_timestep_without_heat_demand(
    project: Any,
) -> None:
    """Waste heat component must not operate in timesteps without heat demand."""
    demand_profile = [0.0, 5.0, 3.0]

    case = _run_optimised_waste_heat_case(
        project=project,
        demand_profile=demand_profile,
        optimize_cap=False,
        installed_capacity=max(demand_profile),
        capex_var=0.0,
    )

    useful_heat_output = _useful_heat_output(
        case=case,
        length=len(demand_profile),
    )
    raw_heat_input = _raw_heat_input(
        case=case,
        length=len(demand_profile),
    )

    zero_demand_indices = [
        index for index, value in enumerate(demand_profile) if value == 0.0
    ]

    for index in zero_demand_indices:
        assert useful_heat_output[index] == pytest.approx(0.0)
        assert raw_heat_input[index] == pytest.approx(0.0)


def test_reality_non_forced_surplus_waste_heat_is_curtailed(
    project: Project,
) -> None:
    """Non-forced surplus waste heat potential must be curtailed."""
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
        installed_capacity=max(demand_profile),
    )

    assert case["termination_condition"] == "optimal"

    useful_heat_output = _reality_useful_heat_output(case)
    raw_heat_input = _reality_raw_heat_input(case)

    expected_raw_heat_input = [
        demand / case["efficiency_hex"] for demand in demand_profile
    ]

    assert useful_heat_output == pytest.approx(demand_profile)
    assert raw_heat_input == pytest.approx(expected_raw_heat_input)
    assert _eesyplan_objective(case["results"]) == pytest.approx(0.0)


def test_reality_forced_surplus_waste_heat_without_dump_sink_is_infeasible(
    project: Project,
) -> None:
    """Forced surplus waste heat without a sink must be infeasible."""
    demand_profile = [4.0, 8.0, 12.0]
    raw_waste_heat_profile = [20.0, 20.0, 20.0]

    case = _run_waste_heat_reality_case(
        project=project,
        demand_profile=demand_profile,
        raw_waste_heat_profile=raw_waste_heat_profile,
        raw_waste_heat_forced=True,
        dump_sink_enabled=False,
        backup_boiler_enabled=False,
        installed_capacity=max(demand_profile),
    )

    assert "infeasible" in case["termination_condition"]
    assert case["results"] is None
    assert case["solph_results"] is None


def test_reality_forced_surplus_dump_sink_costs_are_in_objective(
    project: Project,
) -> None:
    """Dump sink variable costs must be part of the objective."""
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

    dump_flow = _reality_dump_flow(case)

    expected_objective = sum(dump_flow) * dump_sink_variable_costs

    assert _eesyplan_objective(case["results"]) == pytest.approx(
        expected_objective
    )


def test_reality_waste_heat_shortage_without_backup_is_infeasible(
    project: Project,
) -> None:
    """Waste heat shortage without backup must be infeasible."""
    demand_profile = [4.0, 8.0, 12.0]
    raw_waste_heat_profile = [2.0, 2.0, 2.0]

    case = _run_waste_heat_reality_case(
        project=project,
        demand_profile=demand_profile,
        raw_waste_heat_profile=raw_waste_heat_profile,
        raw_waste_heat_forced=False,
        dump_sink_enabled=False,
        backup_boiler_enabled=False,
        installed_capacity=max(demand_profile),
    )

    assert "infeasible" in case["termination_condition"]
    assert case["results"] is None
    assert case["solph_results"] is None


def test_reality_waste_heat_shortage_with_backup_boiler_covers_residual_demand(
    project: Project,
) -> None:
    """Backup boiler must cover residual heat demand."""
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

    useful_heat_output = _reality_useful_heat_output(case)
    raw_heat_input = _reality_raw_heat_input(case)
    backup_heat_output = _reality_backup_heat_output(case)

    expected_waste_heat_output = [
        min(
            demand,
            raw_available * case["efficiency_hex"],
        )
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
