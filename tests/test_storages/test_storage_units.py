from __future__ import annotations

import math

import pytest

from oemof import solph
from oemof.eesyplan.components.storages import ElectricalStorage
from oemof.eesyplan.components.storages import FuelStorage
from oemof.eesyplan.components.storages import HydrogenStorage
from oemof.eesyplan.components.storages import ThermalStorage

try:
    from ._helpers import DummyProjectData
    from ._helpers import StorageSpec
    from ._helpers import assert_close
    from ._helpers import get_input_flow
    from ._helpers import get_nominal
    from ._helpers import get_output_flow
    from ._helpers import is_investment
    from ._helpers import storage_bus_kwargs
except ImportError:
    from _helpers import DummyProjectData
    from _helpers import StorageSpec
    from _helpers import assert_close
    from _helpers import get_input_flow
    from _helpers import get_nominal
    from _helpers import get_output_flow
    from _helpers import is_investment
    from _helpers import storage_bus_kwargs


STORAGE_SPECS = [
    StorageSpec(
        storage_type="electrical",
        cls=ElectricalStorage,
        bus_in_arg="bus_in_electricity",
        bus_out_arg="bus_out_electricity",
    ),
    StorageSpec(
        storage_type="fuel",
        cls=FuelStorage,
        bus_in_arg="bus_in_fuel",
        bus_out_arg="bus_out_fuel",
    ),
    StorageSpec(
        storage_type="hydrogen",
        cls=HydrogenStorage,
        bus_in_arg="bus_in_hydrogen",
        bus_out_arg="bus_out_hydrogen",
    ),
    StorageSpec(
        storage_type="thermal",
        cls=ThermalStorage,
        bus_in_arg="bus_in_heat",
        bus_out_arg="bus_out_heat",
    ),
]


@pytest.mark.parametrize("spec", STORAGE_SPECS)
def test_storage_fixed_capacity_initialization(spec):
    bus_in = solph.Bus(label=f"{spec.storage_type}_bus_in")
    bus_out = solph.Bus(label=f"{spec.storage_type}_bus_out")

    storage = spec.cls(
        name=f"{spec.storage_type}_storage",
        **storage_bus_kwargs(spec, bus_in=bus_in, bus_out=bus_out),
        installed_capacity=10,
        optimize_cap=False,
        capex_var=100,
        opex_fix=5,
        opex_var=2,
        lifetime=20,
        crate=0.5,
        efficiency=0.81,
        self_discharge=0.01,
        soc_min=0.1,
        soc_max=0.9,
        initial_storage_level=0.3,
        balanced=False,
    )

    input_flow = get_input_flow(storage, bus_in)
    output_flow = get_output_flow(storage, bus_out)

    assert storage.label == f"{spec.storage_type}_storage"

    assert bus_in in storage.inputs
    assert bus_out in storage.outputs

    assert_close(get_nominal(storage), 10)
    assert_close(get_nominal(input_flow), 5)
    assert_close(get_nominal(output_flow), 5)

    assert storage.capacity_charge == 5
    assert storage.capacity_discharge == 5
    assert storage.crate_charge is None
    assert storage.crate_discharge is None

    assert storage.invest_relation_input_capacity is None
    assert storage.invest_relation_output_capacity is None

    assert_close(input_flow.variable_costs, 2)

    expected_efficiency = math.sqrt(0.81)
    assert_close(storage.efficiency, 0.81)
    assert_close(storage.inflow_conversion_factor, expected_efficiency)
    assert_close(storage.outflow_conversion_factor, expected_efficiency)

    assert_close(storage.loss_rate, 0.01)
    assert_close(storage.min_storage_level, 0.1)
    assert_close(storage.max_storage_level, 0.9)
    assert_close(storage.initial_storage_level, 0.3)

    assert storage.balanced is False


@pytest.mark.parametrize("spec", STORAGE_SPECS)
def test_storage_output_bus_defaults_to_input_bus(spec):
    bus = solph.Bus(label=f"{spec.storage_type}_bus")

    storage = spec.cls(
        name=f"{spec.storage_type}_storage_default_bus",
        **storage_bus_kwargs(spec, bus_in=bus),
        installed_capacity=1,
        optimize_cap=False,
    )

    assert bus in storage.inputs
    assert bus in storage.outputs


@pytest.mark.parametrize("spec", STORAGE_SPECS)
def test_storage_invest_capacity_initialization(spec):
    bus_in = solph.Bus(label=f"{spec.storage_type}_invest_bus_in")
    bus_out = solph.Bus(label=f"{spec.storage_type}_invest_bus_out")

    storage = spec.cls(
        name=f"{spec.storage_type}_invest_storage",
        **storage_bus_kwargs(spec, bus_in=bus_in, bus_out=bus_out),
        installed_capacity=2,
        optimize_cap=True,
        maximum_capacity=12,
        capex_var=100,
        opex_fix=5,
        lifetime=20,
        crate=0.25,
        efficiency=0.81,
        initial_storage_level=0,
        balanced=True,
        project_data=DummyProjectData(),
    )

    input_flow = get_input_flow(storage, bus_in)
    output_flow = get_output_flow(storage, bus_out)

    nominal_capacity = get_nominal(storage)

    assert is_investment(nominal_capacity)

    if hasattr(nominal_capacity, "maximum"):
        assert_close(nominal_capacity.maximum, 12)

    assert get_nominal(input_flow) is None
    assert get_nominal(output_flow) is None

    assert storage.capacity_charge is None
    assert storage.capacity_discharge is None

    assert_close(storage.crate_charge, 0.25)
    assert_close(storage.crate_discharge, 0.25)

    assert_close(storage.invest_relation_input_capacity, 0.25)
    assert_close(storage.invest_relation_output_capacity, 0.25)


@pytest.mark.parametrize("spec", STORAGE_SPECS)
@pytest.mark.parametrize(
    "invalid_kwargs",
    [
        {"installed_capacity": -1},
        {"capex_var": -1},
        {"opex_fix": -1},
        {"opex_var": -1},
        {"lifetime": 0},
        {"soc_min": 0.8, "soc_max": 0.2},
        {"soc_min": -0.1},
        {"soc_max": 1.1},
        {"crate": 0},
        {"efficiency": 0},
        {"efficiency": 1.1},
        {"self_discharge": -0.01},
        {"self_discharge": 1.1},
        {"maximum_capacity": -1},
        {"initial_storage_level": -0.1},
        {"initial_storage_level": 1.1},
    ],
)
def test_storage_validation_rejects_invalid_common_parameters(
    spec, invalid_kwargs
):
    bus = solph.Bus(label=f"{spec.storage_type}_invalid_bus")

    kwargs = {
        "name": f"{spec.storage_type}_invalid_storage",
        **storage_bus_kwargs(spec, bus_in=bus),
        "installed_capacity": 1,
        "optimize_cap": False,
    }
    kwargs.update(invalid_kwargs)

    with pytest.raises(ValueError, match=r".+"):
        spec.cls(**kwargs)


def test_thermal_storage_rejects_conflicting_loss_aliases():
    bus = solph.Bus(label="thermal_conflicting_loss_bus")

    with pytest.raises(ValueError, match=r".+"):
        ThermalStorage(
            name="thermal_conflicting_loss_storage",
            bus_in_heat=bus,
            self_discharge=0.01,
            thermal_loss_rate=0.02,
            installed_capacity=1,
        )


def test_thermal_storage_accepts_thermal_loss_rate_alias():
    bus = solph.Bus(label="thermal_loss_alias_bus")

    storage = ThermalStorage(
        name="thermal_loss_alias_storage",
        bus_in_heat=bus,
        thermal_loss_rate=0.01,
        installed_capacity=1,
    )

    assert_close(storage.self_discharge, 0.01)
    assert_close(storage.thermal_loss_rate, 0.01)
    assert_close(storage.loss_rate, 0.01)
