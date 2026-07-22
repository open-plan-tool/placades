from __future__ import annotations

import pytest

from oemof.eesyplan.components.storages import ElectricalStorage
from oemof.eesyplan.components.storages import FuelStorage
from oemof.eesyplan.components.storages import HydrogenStorage
from oemof.eesyplan.components.storages import ThermalStorage

try:
    from ._helpers import StorageSpec
    from ._helpers import cbc_available
    from ._helpers import make_fixed_shift_system
    from ._helpers import make_invest_shift_system
    from ._helpers import result_flow_sequence
    from ._helpers import solve_with_cbc
except ImportError:
    from _helpers import StorageSpec
    from _helpers import cbc_available
    from _helpers import make_fixed_shift_system
    from _helpers import make_invest_shift_system
    from _helpers import result_flow_sequence
    from _helpers import solve_with_cbc


pytestmark = pytest.mark.skipif(
    not cbc_available(),
    reason="CBC solver is not available.",
)


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
def test_fixed_storage_can_shift_energy_with_solver(spec):
    energy_system, bus, storage = make_fixed_shift_system(spec)

    model = solve_with_cbc(energy_system)

    charge = result_flow_sequence(model, bus, storage)
    discharge = result_flow_sequence(model, storage, bus)

    assert charge.max() >= 0.99
    assert discharge.max() >= 0.99


@pytest.mark.parametrize("spec", STORAGE_SPECS)
def test_invest_storage_can_shift_energy_with_solver(spec):
    energy_system, bus, storage = make_invest_shift_system(spec)

    model = solve_with_cbc(energy_system)

    charge = result_flow_sequence(model, bus, storage)
    discharge = result_flow_sequence(model, storage, bus)

    assert charge.max() >= 0.99
    assert discharge.max() >= 0.99
