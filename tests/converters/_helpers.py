"""Shared helpers for converter tests.

Important:
These helpers intentionally do not translate constructor parameter names.
Tests should instantiate eesyplan components with their documented public API,
for example: name, bus_in_fuel, bus_out_heat, project_data, optimize_cap, etc.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

import pandas as pd
import pytest

from oemof import solph

_NOT_GIVEN = object()
_PLAIN_SCALAR_TYPES = (str, bytes, int, float, bool, type(None))


def unwrap(value: Any, max_depth: int = 20) -> Any:
    """Unwrap common solph/pyomo/oemof wrapper objects."""
    current = value

    for _ in range(max_depth):
        if isinstance(current, _PLAIN_SCALAR_TYPES):
            break

        if isinstance(current, pd.Series | pd.DataFrame | pd.Index):
            break

        if hasattr(current, "_value"):
            next_value = current._value
        elif hasattr(current, "value"):
            next_value = current.value
        else:
            break

        if callable(next_value):
            try:
                next_value = next_value()
            except TypeError:
                break

        if next_value is current:
            break

        current = next_value

    return current


def scalar(value: Any) -> Any:
    """Return a comparable scalar from wrappers, sequences or pandas objects."""
    unwrapped = unwrap(value)

    if isinstance(unwrapped, pd.DataFrame):
        assert not unwrapped.empty
        return scalar(unwrapped.iloc[0, 0])

    if isinstance(unwrapped, pd.Series):
        assert not unwrapped.empty
        return scalar(unwrapped.iloc[0])

    if isinstance(unwrapped, pd.Index):
        assert len(unwrapped) > 0
        return scalar(unwrapped[0])

    if isinstance(unwrapped, list | tuple):
        assert len(unwrapped) > 0
        return scalar(unwrapped[0])

    if not isinstance(unwrapped, _PLAIN_SCALAR_TYPES) and hasattr(
        unwrapped,
        "__getitem__",
    ):
        try:
            return scalar(unwrapped[0])
        except (KeyError, IndexError, TypeError):
            pass

    return unwrap(unwrapped)


def assert_scalar_equal(actual: Any, expected: float) -> None:
    actual_scalar = scalar(actual)

    assert actual_scalar == pytest.approx(expected), (
        f"actual={actual_scalar!r}, expected={expected!r}"
    )


# def assert_scalar_equal(actual: Any, expected: Any) -> None:
#     """Assert scalar equality, using pytest.approx for numeric values."""
#     actual_scalar = scalar(actual)
#
#     if expected is None:
#         assert actual_scalar is None
#     elif isinstance(expected, (int, float)):
#         assert actual_scalar == pytest.approx(expected)
#     else:
#         assert actual_scalar == expected


def assert_mapping_has_key(mapping: dict[Any, Any], key: Any) -> None:
    assert key in mapping, (
        f"Expected key {key!r}, got keys {list(mapping.keys())!r}."
    )


def input_flow(component: Any, bus: Any) -> Any:
    """Return the input flow connected to bus."""
    assert hasattr(component, "inputs")
    assert_mapping_has_key(component.inputs, bus)
    return component.inputs[bus]


def output_flow(component: Any, bus: Any) -> Any:
    """Return the output flow connected to bus."""
    assert hasattr(component, "outputs")
    assert_mapping_has_key(component.outputs, bus)
    return component.outputs[bus]


def assert_has_input(component: Any, bus: Any) -> None:
    assert hasattr(component, "inputs")
    assert bus in component.inputs


def assert_has_output(component: Any, bus: Any) -> None:
    assert hasattr(component, "outputs")
    assert bus in component.outputs


class DummyProjectData:
    """Minimaler Ersatz für project_data in Investment-Tests."""

    def calculate_epc(self, *args: Any, **kwargs: Any) -> float:
        for key in ("capex_var", "capex", "ep_costs", "investment_costs"):
            value = kwargs.get(key)

            if isinstance(value, int | float):
                return float(value)

        for value in args:
            if isinstance(value, int | float):
                return float(value)

        return 0.0


def assert_no_none_keys(component: Any) -> None:
    """Ensure no None keys are present in solph mappings.

    Do not use `None in mapping` because some oemof mappings implement
    __contains__ through __getitem__, which breaks for None.
    """
    for mapping_name in ("inputs", "outputs", "conversion_factors"):
        mapping = getattr(component, mapping_name, {})

        if mapping is None:
            continue

        if hasattr(mapping, "keys"):
            keys = list(mapping.keys())
        else:
            keys = list(mapping)

        assert all(key is not None for key in keys), (
            f"None key found in component.{mapping_name}: {keys!r}."
        )


def assert_conversion_factor(
    component: Any, bus: Any, expected: float
) -> None:
    assert hasattr(component, "conversion_factors")
    assert_mapping_has_key(component.conversion_factors, bus)
    assert_scalar_equal(component.conversion_factors[bus], expected)


def assert_variable_costs(flow: Any, expected: float) -> None:
    assert hasattr(flow, "variable_costs")
    assert_scalar_equal(flow.variable_costs, expected)


def looks_like_investment(value: Any) -> bool:
    """Return True if value appears to be a solph Investment object."""
    unwrapped = unwrap(value)

    if unwrapped is None or isinstance(unwrapped, _PLAIN_SCALAR_TYPES):
        return False

    class_name = unwrapped.__class__.__name__.lower()

    if "investment" in class_name:
        return True

    investment_attributes = (
        "ep_costs",
        "minimum",
        "maximum",
        "existing",
        "nonconvex",
        "offset",
    )

    return any(hasattr(unwrapped, attr) for attr in investment_attributes)


def flow_capacity(flow: Any) -> Any:
    """Return static nominal flow capacity if present.

    Supports both older and newer solph naming:
    - nominal_value
    - nominal_capacity

    Investment objects are intentionally ignored here.
    """
    for attribute_name in ("nominal_capacity", "nominal_value"):
        if not hasattr(flow, attribute_name):
            continue

        value = getattr(flow, attribute_name)

        if value is None:
            continue

        value = unwrap(value)

        if looks_like_investment(value):
            continue

        return scalar(value)

    return None


def assert_flow_capacity(flow: Any, expected: float) -> None:
    capacity = flow_capacity(flow)

    assert capacity is not None, (
        "Expected a static nominal capacity on the flow."
    )
    assert capacity == pytest.approx(expected)


def assert_input_flow_capacity(
    component: Any, bus: Any, expected: float
) -> None:
    assert_flow_capacity(input_flow(component, bus), expected)


def assert_output_flow_capacity(
    component: Any, bus: Any, expected: float
) -> None:
    assert_flow_capacity(output_flow(component, bus), expected)


def all_flows(component: Any) -> list[Any]:
    flows: list[Any] = []

    if hasattr(component, "inputs"):
        flows.extend(component.inputs.values())

    if hasattr(component, "outputs"):
        flows.extend(component.outputs.values())

    return flows


def _is_close(actual: Any, expected: float) -> bool:
    try:
        assert scalar(actual) == pytest.approx(expected)
    except AssertionError:
        return False

    return True


def assert_any_flow_has_variable_costs(
    component: Any, expected: float
) -> None:
    actual_values: list[Any] = []

    for flow in all_flows(component):
        if not hasattr(flow, "variable_costs"):
            continue

        value = flow.variable_costs
        actual_values.append(scalar(value))

        if _is_close(value, expected):
            return

    pytest.fail(
        f"No flow has variable_costs={expected!r}. "
        f"Actual variable_costs values: {actual_values!r}."
    )


def assert_any_flow_has_capacity(component: Any, expected: float) -> None:
    for flow in all_flows(component):
        capacity = flow_capacity(flow)

        if capacity is not None and _is_close(capacity, expected):
            return

    pytest.fail(f"No flow has static capacity {expected!r}.")


def investment_from_flow(flow: Any) -> Any:
    """Return Investment object from a flow if present."""
    for attribute_name in ("investment", "nominal_capacity", "nominal_value"):
        if not hasattr(flow, attribute_name):
            continue

        value = getattr(flow, attribute_name)

        if value is None:
            continue

        value = unwrap(value)

        if looks_like_investment(value):
            return value

    return None


def assert_flow_has_investment(flow: Any) -> Any:
    investment = investment_from_flow(flow)

    assert investment is not None, "Expected an Investment object on the flow."

    return investment


def investment_attribute(
    investment: Any,
    possible_names: Iterable[str],
    default: Any = None,
) -> Any:
    for name in possible_names:
        if hasattr(investment, name):
            return scalar(getattr(investment, name))

    return default


def _assert_expected_value(
    actual: Any, expected: Any, attribute_name: str
) -> None:
    if expected is None:
        assert actual is None, (
            f"Expected {attribute_name}=None, got {actual!r}."
        )
        return

    if isinstance(expected, float) and math.isinf(expected):
        assert math.isinf(actual), (
            f"Expected {attribute_name}=inf, got {actual!r}."
        )
        return

    assert actual == pytest.approx(expected), (
        f"Expected {attribute_name}={expected!r}, got {actual!r}."
    )


def assert_investment_capacity(
    flow: Any,
    *,
    existing: Any = _NOT_GIVEN,
    maximum: Any = _NOT_GIVEN,
    minimum: Any = _NOT_GIVEN,
) -> None:
    """Assert Investment capacity attributes on a flow.

    Only passed attributes are checked.
    """
    investment = assert_flow_has_investment(flow)

    if existing is not _NOT_GIVEN:
        actual_existing = investment_attribute(
            investment,
            ("existing", "existing_capacity", "existing_value"),
        )
        _assert_expected_value(actual_existing, existing, "existing")

    if maximum is not _NOT_GIVEN:
        actual_maximum = investment_attribute(
            investment,
            ("maximum", "max", "maximum_capacity", "max_capacity"),
        )
        _assert_expected_value(actual_maximum, maximum, "maximum")

    if minimum is not _NOT_GIVEN:
        actual_minimum = investment_attribute(
            investment,
            ("minimum", "min", "minimum_capacity", "min_capacity"),
        )
        _assert_expected_value(actual_minimum, minimum, "minimum")


def assert_input_flow_investment_capacity(
    component: Any,
    bus: Any,
    *,
    existing: Any = _NOT_GIVEN,
    maximum: Any = _NOT_GIVEN,
    minimum: Any = _NOT_GIVEN,
) -> None:
    assert_investment_capacity(
        input_flow(component, bus),
        existing=existing,
        maximum=maximum,
        minimum=minimum,
    )


def assert_output_flow_investment_capacity(
    component: Any,
    bus: Any,
    *,
    existing: Any = _NOT_GIVEN,
    maximum: Any = _NOT_GIVEN,
    minimum: Any = _NOT_GIVEN,
) -> None:
    assert_investment_capacity(
        output_flow(component, bus),
        existing=existing,
        maximum=maximum,
        minimum=minimum,
    )


def assert_any_flow_has_investment_capacity(
    component: Any,
    *,
    existing: Any = _NOT_GIVEN,
    maximum: Any = _NOT_GIVEN,
    minimum: Any = _NOT_GIVEN,
) -> None:
    for flow in all_flows(component):
        if investment_from_flow(flow) is not None:
            assert_investment_capacity(
                flow,
                existing=existing,
                maximum=maximum,
                minimum=minimum,
            )
            return

    pytest.fail("No Investment object found on any component flow.")


def _unique(items: Iterable[Any]) -> list[Any]:
    unique_items: list[Any] = []

    for item in items:
        if item is None:
            continue

        if item not in unique_items:
            unique_items.append(item)

    return unique_items


def assert_model_builds(component: Any) -> None:
    """Assert that a minimal solph model can be built with the component.

    This only builds the model. It does not solve it.
    """
    timeindex = pd.date_range(
        "2026-01-01",
        periods=3,
        freq="h",
    )

    try:
        energy_system = solph.EnergySystem(
            timeindex=timeindex,
            infer_last_interval=False,
        )
    except TypeError:
        energy_system = solph.EnergySystem(timeindex=timeindex)

    input_buses = list(getattr(component, "inputs", {}).keys())
    output_buses = list(getattr(component, "outputs", {}).keys())
    buses = _unique(input_buses + output_buses)

    components_module = getattr(solph, "components", solph)
    source_cls = components_module.Source
    sink_cls = components_module.Sink

    sources = [
        source_cls(
            label=f"source_for_input_bus_{index}",
            outputs={bus: solph.Flow()},
        )
        for index, bus in enumerate(_unique(input_buses))
    ]

    sinks = [
        sink_cls(
            label=f"sink_for_output_bus_{index}",
            inputs={bus: solph.Flow()},
        )
        for index, bus in enumerate(_unique(output_buses))
    ]

    energy_system.add(*(buses + sources + sinks + [component]))

    solph.Model(energy_system)
