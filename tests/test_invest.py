import pytest

from oemof.eesyplan import CarrierBus
from oemof.eesyplan import Electrolyzer
from oemof.eesyplan import Project


def test_error_message():
    el_bus_in = CarrierBus(name="Electricity")
    h2_bus_out = CarrierBus(name="H2-Bus")
    msg = (
        "Maximum capacity and installed capacity can't be set at the same time"
    )
    with pytest.raises(ValueError, match=msg):
        Electrolyzer(
            name="Electrolyzer",
            bus_in_electricity=el_bus_in,
            bus_out_h2=h2_bus_out,
            age_installed=0,
            installed_capacity=1000,
            maximum_capacity=1000,
            capex_spec=1000,
            opex_spec=1000,
            lifetime=20,
            efficiency=0.9,
            variable_costs=0,
            project_data=Project(
                name="Project_X",
                economic_period=20,
                tax=0,
                discount_factor=0.01,
            ),
        )
