"""Validation helpers for converter components."""

from __future__ import annotations

import math

from oemof.solph import Bus


def validate_name(value: object) -> str:
    """Validate a component name.

    Parameters
    ----------
    value : object
        Value to validate.

    Returns
    -------
    str
        Validated component name.
    """
    if not isinstance(value, str):
        raise TypeError("name must be str.")
    if not value:
        raise ValueError("name must not be empty.")
    return value


def validate_bus(name: str, value: object) -> Bus:
    """Validate a solph bus.

    Parameters
    ----------
    name : str
        Parameter name.
    value : object
        Value to validate.

    Returns
    -------
    oemof.solph.Bus
        Validated bus.
    """
    if not isinstance(value, Bus):
        raise TypeError(f"{name} must be an oemof.solph.Bus.")
    return value


def validate_bool(name: str, value: object) -> bool:
    """Validate a boolean value.

    Parameters
    ----------
    name : str
        Parameter name.
    value : object
        Value to validate.

    Returns
    -------
    bool
        Validated boolean value.
    """
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool.")
    return value


def validate_non_negative_float(name: str, value: object) -> float:
    """Validate a finite non-negative float.

    Parameters
    ----------
    name : str
        Parameter name.
    value : object
        Value to validate.

    Returns
    -------
    float
        Validated float.
    """
    numeric_value = to_float(name, value)

    if numeric_value < 0:
        raise ValueError(f"{name} must be >= 0.")

    return numeric_value


def validate_optional_non_negative_capacity(
    name: str,
    value: object | None,
) -> float | None:
    """Validate an optional non-negative capacity.

    Parameters
    ----------
    name : str
        Parameter name.
    value : object or None
        Capacity value.

    Returns
    -------
    float or None
        Validated capacity.

    Notes
    -----
    ``float("inf")`` is allowed for backwards compatibility with existing
    eesyplan converter defaults.
    """
    if value is None:
        return None

    numeric_value = to_float(name, value, allow_infinite=True)

    if numeric_value < 0:
        raise ValueError(f"{name} must be >= 0.")

    return numeric_value


def validate_non_negative_int(name: str, value: object) -> int:
    """Validate a non-negative integer.

    Parameters
    ----------
    name : str
        Parameter name.
    value : object
        Value to validate.

    Returns
    -------
    int
        Validated integer.
    """
    int_value = to_int(name, value)

    if int_value < 0:
        raise ValueError(f"{name} must be >= 0.")

    return int_value


def validate_positive_int(name: str, value: object) -> int:
    """Validate a positive integer.

    Parameters
    ----------
    name : str
        Parameter name.
    value : object
        Value to validate.

    Returns
    -------
    int
        Validated integer.
    """
    int_value = to_int(name, value)

    if int_value <= 0:
        raise ValueError(f"{name} must be > 0.")

    return int_value


def validate_efficiency(name: str, value: object) -> float:
    """Validate an efficiency factor.

    Parameters
    ----------
    name : str
        Parameter name.
    value : object
        Efficiency value.

    Returns
    -------
    float
        Validated efficiency.

    Notes
    -----
    Efficiencies are restricted to ``0 < value <= 1``.
    """
    numeric_value = to_float(name, value)

    if numeric_value <= 0 or numeric_value > 1:
        raise ValueError(f"{name} must be > 0 and <= 1.")

    return numeric_value


def validate_maximum_capacity_not_below_installed(
    maximum_capacity: float | None,
    installed_capacity: float,
) -> None:
    """Validate relation between maximum and installed capacity.

    Parameters
    ----------
    maximum_capacity : float or None
        Maximum capacity.
    installed_capacity : float
        Existing installed capacity.
    """
    if maximum_capacity is None:
        return

    if math.isinf(maximum_capacity):
        return

    if maximum_capacity < installed_capacity:
        raise ValueError("maximum_capacity must be >= installed_capacity.")


def to_float(
    name: str,
    value: object,
    *,
    allow_infinite: bool = False,
) -> float:
    """Convert value to float and validate finiteness.

    Parameters
    ----------
    name : str
        Parameter name.
    value : object
        Value to convert.
    allow_infinite : bool, default=False
        Whether ``float("inf")`` is allowed.

    Returns
    -------
    float
        Converted float.
    """
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric.")

    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be numeric.") from error

    if math.isnan(numeric_value):
        raise ValueError(f"{name} must be finite.")

    if not allow_infinite and not math.isfinite(numeric_value):
        raise ValueError(f"{name} must be finite.")

    return numeric_value


def to_int(name: str, value: object) -> int:
    """Convert value to int and reject non-integer values.

    Parameters
    ----------
    name : str
        Parameter name.
    value : object
        Value to convert.

    Returns
    -------
    int
        Converted integer.
    """
    if isinstance(value, bool):
        raise TypeError(f"{name} must be integer.")

    try:
        int_value = int(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be integer.") from error

    if int_value != value:
        raise TypeError(f"{name} must be integer.")

    return int_value
