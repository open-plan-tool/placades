from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd
from pyomo.environ import SolverFactory
from pyomo.opt import TerminationCondition

from oemof import solph
from oemof.solph import Flow
from oemof.solph import processing


@dataclass(frozen=True)
class StorageSpec:
    """Hilfsstruktur für parametrisierte Speichertests."""

    storage_type: str
    cls: type
    bus_in_arg: str
    bus_out_arg: str


@dataclass
class DummyProjectData:
    """Minimaler Ersatz für project_data in Investment-Tests."""

    interest_rate: float = 0.05
    observation_period: int = 20
    project_duration: int = 20

    def __post_init__(self):
        self.duration = self.observation_period
        self.analysis_period = self.observation_period

        self.economic_data = {
            "interest_rate": self.interest_rate,
            "observation_period": self.observation_period,
            "project_duration": self.project_duration,
        }

        self.general_data = {
            "interest_rate": self.interest_rate,
            "observation_period": self.observation_period,
            "project_duration": self.project_duration,
        }

    def calculate_epc(self, *args: Any, **kwargs: Any) -> float:
        """Minimaler Ersatz für project_data.calculate_epc()."""

        for key in ("capex_var", "capex", "ep_costs", "investment_costs"):
            value = kwargs.get(key)

            if isinstance(value, int | float):
                return float(value)

        for value in args:
            if isinstance(value, int | float):
                return float(value)

        return 0.0

    def annuity_factor(self, lifetime: float | None = None) -> float:
        """Berechnet einen einfachen Annuitätsfaktor."""

        lifetime = lifetime or self.observation_period

        if self.interest_rate == 0:
            return 1 / lifetime

        q = 1 + self.interest_rate
        return (q**lifetime * self.interest_rate) / (q**lifetime - 1)

    def get_annuity_factor(self, lifetime: float | None = None) -> float:
        """Alias für unterschiedliche Implementierungen."""

        return self.annuity_factor(lifetime=lifetime)


class ScalarSequence(float):
    """Float-kompatibler Skalar, der zusätzlich wie eine oemof-Sequenz indexierbar ist."""

    def __new__(cls, value):
        return super().__new__(cls, value)

    def __getitem__(self, _index):
        return float(self)


def flow_nominal_capacity_kwargs(
    *,
    optimize_cap: bool,
    installed_capacity: float | None,
    crate: float | None,
) -> dict:
    """Erzeugt die nominal/investment-Argumente für Lade-/Entlade-Flows."""

    if crate is None:
        return {}

    if optimize_cap:
        # Technisch notwendig für solph invest_relation_*.
        # Keine separaten Kosten, da die Investition über die Speicherkapazität bewertet wird.
        return {"investment": solph.Investment(ep_costs=0)}

    return {"nominal_value": installed_capacity * crate}


def storage_nominal_capacity(
    *,
    optimize_cap: bool,
    installed_capacity: float | None,
):
    """Gibt die feste Speicherkapazität zurück oder None bei Kapazitätsoptimierung."""

    if optimize_cap:
        return None

    return installed_capacity


def storage_bus_kwargs(
    spec: StorageSpec, bus_in, bus_out=None
) -> dict[str, Any]:
    """Erzeugt die bus_in-/bus_out-Keyword-Argumente für eine Speicherklasse."""

    kwargs = {spec.bus_in_arg: bus_in}

    if bus_out is not None:
        kwargs[spec.bus_out_arg] = bus_out

    return kwargs


def get_nominal(obj):
    """Liest nominal_capacity oder nominal_value versionsrobust aus."""

    for attr in ("nominal_capacity", "nominal_value"):
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            if value is not None:
                return value

    return None


def get_input_flow(storage, bus):
    """Gibt den Input-Flow eines Speichers zurück."""

    return storage.inputs[bus]


def get_output_flow(storage, bus):
    """Gibt den Output-Flow eines Speichers zurück."""

    return storage.outputs[bus]


def is_investment(value) -> bool:
    """Prüft versionsrobust, ob ein Wert ein oemof Investment-Objekt ist."""

    return value.__class__.__name__ == "Investment"


def assert_close(actual: float, expected: float, rel_tol: float = 1e-9):
    """Kleiner Wrapper für numerische Vergleiche."""

    assert math.isclose(actual, expected, rel_tol=rel_tol), (
        f"Expected {expected}, got {actual}"
    )


def make_timeindex(periods: int = 3):
    """Erzeugt einen einfachen Zeitindex."""

    return pd.date_range("2026-01-01", periods=periods, freq="h")


def make_energy_system(periods: int = 3):
    """Erzeugt ein EnergySystem.

    `infer_last_interval=True` wird genutzt, falls die installierte solph-Version
    dieses Argument unterstützt.
    """

    timeindex = make_timeindex(periods=periods)

    try:
        return solph.EnergySystem(
            timeindex=timeindex,
            infer_last_interval=True,
        )
    except TypeError:
        return solph.EnergySystem(timeindex=timeindex)


def cbc_available() -> bool:
    """Prüft, ob der CBC-Solver verfügbar ist."""

    try:
        return SolverFactory("cbc").available(exception_flag=False)
    except TypeError:
        return SolverFactory("cbc").available(False)


def solve_with_cbc(energysystem):
    """Erstellt und löst ein solph-Modell mit CBC."""

    model = solph.Model(energysystem)

    result = model.solve(
        solver="cbc",
        solve_kwargs={"tee": False},
    )

    # Neuere oemof.solph-Versionen geben ein solph.Results-Objekt zurück.
    # Die eigentlichen Pyomo-Solver-Ergebnisse liegen dann in _solver_results.
    solver_result = getattr(result, "_solver_results", result)

    solver_info = getattr(solver_result, "solver", None)

    termination_condition = getattr(
        solver_info,
        "termination_condition",
        None,
    )

    solver_status = getattr(
        solver_info,
        "status",
        None,
    )

    assert (
        termination_condition == TerminationCondition.optimal
        or str(termination_condition).lower() == "optimal"
    ), (
        f"Solver status: {solver_status}, "
        f"termination_condition: {termination_condition}, "
        f"solver_result_type: {type(solver_result)}, "
        f"solver_result: {solver_result}"
    )

    return model


def result_flow_sequence(model, from_node, to_node):
    """Liest eine Flow-Zeitreihe aus den oemof-Ergebnissen."""

    results = processing.results(model)
    sequences = results[(from_node, to_node)]["sequences"]

    if "flow" in sequences.columns:
        return sequences["flow"]

    for column in sequences.columns:
        if column == "flow":
            return sequences[column]

        if isinstance(column, tuple) and column[0] == "flow":
            return sequences[column]

    raise KeyError(f"No flow sequence found for {(from_node, to_node)}")


def make_fixed_shift_system(spec: StorageSpec):
    """Erstellt ein kleines System, in dem der Speicher Energie verschieben muss."""

    energy_system = make_energy_system(periods=3)

    bus = solph.Bus(label=f"{spec.storage_type}_bus")

    source = solph.components.Source(
        label=f"{spec.storage_type}_source",
        outputs={
            bus: Flow(
                nominal_capacity=1,
                fix=[1, 0, 0],
                variable_costs=0,
            )
        },
    )

    demand = solph.components.Sink(
        label=f"{spec.storage_type}_demand",
        inputs={
            bus: Flow(
                nominal_capacity=1,
                fix=[0, 1, 0],
            )
        },
    )

    storage = spec.cls(
        name=f"{spec.storage_type}_storage",
        **storage_bus_kwargs(spec, bus_in=bus, bus_out=bus),
        installed_capacity=1,
        optimize_cap=False,
        crate=1,
        efficiency=1,
        self_discharge=0,
        soc_min=0,
        soc_max=1,
        initial_storage_level=0,
        balanced=False,
    )

    energy_system.add(bus, source, demand, storage)

    return energy_system, bus, storage


def make_invest_shift_system(spec: StorageSpec):
    """Erstellt ein kleines System, in dem der Speicher investiv gebaut werden muss."""

    energy_system = make_energy_system(periods=3)

    bus = solph.Bus(label=f"{spec.storage_type}_invest_bus")

    source = solph.components.Source(
        label=f"{spec.storage_type}_invest_source",
        outputs={
            bus: Flow(
                nominal_capacity=1,
                fix=[1, 0, 0],
                variable_costs=0,
            )
        },
    )

    demand = solph.components.Sink(
        label=f"{spec.storage_type}_invest_demand",
        inputs={
            bus: Flow(
                nominal_capacity=1,
                fix=[0, 1, 0],
            )
        },
    )

    storage = spec.cls(
        name=f"{spec.storage_type}_invest_storage",
        **storage_bus_kwargs(spec, bus_in=bus, bus_out=bus),
        installed_capacity=0,
        optimize_cap=True,
        maximum_capacity=1,
        capex_var=1,
        opex_fix=0,
        lifetime=20,
        crate=1,
        efficiency=1,
        self_discharge=0,
        soc_min=0,
        soc_max=1,
        initial_storage_level=0,
        balanced=False,
        project_data=DummyProjectData(),
    )

    energy_system.add(bus, source, demand, storage)

    return energy_system, bus, storage
