from __future__ import annotations

import math
from inspect import signature
from numbers import Real
from typing import Any

from oemof import solph

try:
    from oemof.solph import Bus
except ImportError:  # pragma: no cover
    from oemof.solph.buses import Bus


class _NumericScalarSequence(float):
    """Float, der zusätzlich wie eine konstante Zeitreihe indexierbar ist."""

    def __new__(cls, value):
        return super().__new__(cls, float(value))

    def __getitem__(self, _):
        return float(self)


def ScalarSequence(value):
    """Gibt None unverändert zurück, sonst einen float- und indexierbaren Wert."""
    if value is None:
        return None
    return _NumericScalarSequence(value)


def _validate_non_empty_string(parameter_name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{parameter_name} must be a string.")
    if not value.strip():
        raise ValueError(f"{parameter_name} must not be empty.")


def _validate_bus(parameter_name: str, value: Any) -> None:
    if not isinstance(value, Bus):
        raise TypeError(f"{parameter_name} must be an oemof.solph.Bus.")


def _validate_bool(parameter_name: str, value: Any) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{parameter_name} must be bool.")


def _validate_finite_number(parameter_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{parameter_name} must be a finite number.")
    if not math.isfinite(float(value)):
        raise ValueError(f"{parameter_name} must be finite.")


def _validate_non_negative_number(parameter_name: str, value: Any) -> None:
    _validate_finite_number(parameter_name, value)
    if value < 0:
        raise ValueError(f"{parameter_name} must be >= 0.")


def _validate_positive_number(parameter_name: str, value: Any) -> None:
    _validate_finite_number(parameter_name, value)
    if value <= 0:
        raise ValueError(f"{parameter_name} must be > 0.")


def _validate_fraction(parameter_name: str, value: Any) -> None:
    _validate_finite_number(parameter_name, value)
    if value < 0 or value > 1:
        raise ValueError(f"{parameter_name} must be between 0 and 1.")


def validate_common_storage_parameters(
    *,
    name: str,
    bus_in: Any,
    bus_out: Any,
    age_installed: float,
    installed_capacity: float,
    capex_var: float,
    capex_fix: float,
    opex_fix: float,
    opex_var: float,
    lifetime: float,
    optimize_cap: bool,
    soc_min: float,
    soc_max: float,
    crate: float,
    efficiency: float,
    loss_rate: float,
    maximum_capacity: float | None,
    initial_storage_level: float | None,
    balanced: bool,
    project_data: Any,
) -> None:
    _validate_non_empty_string("name", name)

    _validate_bus("bus_in", bus_in)
    _validate_bus("bus_out", bus_out)

    _validate_non_negative_number("age_installed", age_installed)
    _validate_non_negative_number("installed_capacity", installed_capacity)

    _validate_non_negative_number("capex_var", capex_var)
    _validate_non_negative_number("capex_fix", capex_fix)
    _validate_non_negative_number("opex_fix", opex_fix)

    _validate_finite_number("opex_var", opex_var)
    if opex_var < 0:
        raise ValueError("opex_var must be greater than or equal to 0.")

    _validate_positive_number("lifetime", lifetime)
    _validate_bool("optimize_cap", optimize_cap)

    _validate_fraction("soc_min", soc_min)
    _validate_fraction("soc_max", soc_max)

    if soc_min > soc_max:
        raise ValueError("soc_min must be <= soc_max.")

    _validate_positive_number("crate", crate)

    _validate_finite_number("efficiency", efficiency)
    if efficiency <= 0 or efficiency > 1:
        raise ValueError("efficiency must be > 0 and <= 1.")

    _validate_fraction("loss_rate", loss_rate)

    if maximum_capacity is not None:
        _validate_non_negative_number("maximum_capacity", maximum_capacity)
        if maximum_capacity < installed_capacity:
            raise ValueError("maximum_capacity must be >= installed_capacity.")

    if initial_storage_level is not None:
        _validate_fraction("initial_storage_level", initial_storage_level)

        if initial_storage_level < soc_min or initial_storage_level > soc_max:
            raise ValueError(
                "initial_storage_level must be between soc_min and soc_max."
            )

    _validate_bool("balanced", balanced)

    if optimize_cap and project_data is None:
        raise TypeError("project_data must not be None if optimize_cap=True.")


def validate_thermal_fixed_losses(
    *,
    fixed_thermal_losses_absolute: float,
    fixed_thermal_losses_relative: float,
) -> None:
    _validate_non_negative_number(
        "fixed_thermal_losses_absolute",
        fixed_thermal_losses_absolute,
    )
    _validate_fraction(
        "fixed_thermal_losses_relative",
        fixed_thermal_losses_relative,
    )


def storage_flow_settings(
    *,
    optimize_cap: bool,
    installed_capacity: float,
    crate: float,
) -> tuple[float | None, float | None, float | None, float | None]:
    if optimize_cap:
        capacity_charge = None
        capacity_discharge = None
        crate_charge = crate
        crate_discharge = crate
    else:
        capacity_charge = installed_capacity * crate
        capacity_discharge = installed_capacity * crate
        crate_charge = None
        crate_discharge = None

    return capacity_charge, capacity_discharge, crate_charge, crate_discharge


def split_roundtrip_efficiency(efficiency: float) -> float:
    return math.sqrt(efficiency)


def _supports_parameter(callable_object, parameter_name: str) -> bool:
    try:
        return parameter_name in signature(callable_object).parameters
    except (TypeError, ValueError):
        return False


def flow_nominal_capacity_kwargs(
    *,
    optimize_cap: bool,
    installed_capacity: float | None,
    crate: float | None,
) -> dict:
    """Erzeugt Flow-Kapazitätsargumente.

    Bei fixer Speicherkapazität:
        Flow bekommt feste nominal_capacity = installed_capacity * crate.

    Bei Investment:
        Flow bekommt ein kostenfreies Investment.
        Die Kopplung zur Speicherkapazität erfolgt über
        invest_relation_input_capacity/output_capacity am GenericStorage.
    """

    if crate is None:
        return {}

    if optimize_cap:
        investment = solph.Investment(ep_costs=0)

        if _supports_parameter(solph.Flow, "investment"):
            return {"investment": investment}

        return {"nominal_capacity": investment}

    if installed_capacity is None:
        raise TypeError(
            "installed_capacity must not be None if optimize_cap=False."
        )

    nominal_capacity = installed_capacity * crate

    if _supports_parameter(solph.Flow, "nominal_capacity"):
        return {"nominal_capacity": nominal_capacity}

    return {"nominal_value": nominal_capacity}


def make_storage_flow(
    *,
    optimize_cap: bool,
    installed_capacity: float | None,
    crate: float | None,
    variable_costs: float = 0,
):
    """Erzeugt einen Storage-Lade- oder Entlade-Flow."""

    kwargs = flow_nominal_capacity_kwargs(
        optimize_cap=optimize_cap,
        installed_capacity=installed_capacity,
        crate=crate,
    )

    kwargs["variable_costs"] = variable_costs

    flow = solph.Flow(**kwargs)

    # Wichtig für Tests UND Solver:
    # math.isclose(...) soll funktionieren, aber der Solver braucht value[t].
    flow.variable_costs = ScalarSequence(variable_costs)

    if (
        not optimize_cap
        and installed_capacity is not None
        and crate is not None
    ):
        nominal_capacity = installed_capacity * crate

        if hasattr(flow, "nominal_capacity"):
            flow.nominal_capacity = ScalarSequence(nominal_capacity)

        if hasattr(flow, "nominal_value"):
            flow.nominal_value = ScalarSequence(nominal_capacity)

    return flow


def storage_nominal_capacity(
    *,
    optimize_cap: bool,
    installed_capacity: float | None,
):
    if optimize_cap:
        return None

    if installed_capacity is None:
        raise TypeError(
            "installed_capacity must not be None if optimize_cap=False."
        )

    return installed_capacity


def _unwrap_scalar_sequence(value):
    """Holt aus solph-_FakeSequence oder ähnlichen Objekten einen Skalar."""
    if value is None:
        return None

    if isinstance(value, Real) and not isinstance(value, bool):
        return float(value)

    try:
        return float(value[0])
    except (TypeError, ValueError, KeyError, IndexError):
        pass

    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def normalize_scalar_sequence_attributes(obj, *attribute_names):
    """Ersetzt solph-_FakeSequence-Attribute durch numeric ScalarSequence."""
    for attribute_name in attribute_names:
        if not hasattr(obj, attribute_name):
            continue

        value = getattr(obj, attribute_name)

        if value is None:
            continue

        scalar_value = _unwrap_scalar_sequence(value)

        if isinstance(scalar_value, Real) and not isinstance(
            scalar_value, bool
        ):
            setattr(obj, attribute_name, ScalarSequence(scalar_value))


def normalize_investment_sequences(investment):
    """Ersetzt _FakeSequence-Werte innerhalb eines Investment-Objekts."""
    if investment is None:
        return None

    normalize_scalar_sequence_attributes(
        investment,
        "ep_costs",
        "minimum",
        "maximum",
        "existing",
        "offset",
        "overall_minimum",
        "overall_maximum",
    )

    return investment
