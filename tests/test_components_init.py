import pytest

from oemof.eesyplan.components.buses.carrier import CarrierBus as Bus
from oemof.eesyplan.components.converters.Boiler import Boiler
from oemof.eesyplan.components.transport.heat import HeatingNetwork
from oemof.eesyplan.project import Project
from oemof.solph.components import Sink


def test_heating_network():
    hn = HeatingNetwork(name="Heating Network", absolute_losses=5)
    assert isinstance(hn, HeatingNetwork)
    assert isinstance(hn._Node__subnodes[0], Sink)
    hn_wo_losses = HeatingNetwork(name="Heating Network")
    assert hn_wo_losses._Node__subnodes == []


def test_capacity_null_in_dispatch_mode():
    bus = Bus(name="bus")
    # Investment
    Boiler(
        name="central_gas_boiler",
        bus_in_fuel=bus,
        bus_out_heat=bus,
        age_installed=0,
        capex_var=1000,
        opex_fix=1000,
        lifetime=20,
        maximum_capacity=None,
        efficiency=0.8,
        opex_var=0,
        optimize_cap=True,
        project_data=Project(
            name="Project_X", lifetime=20, tax=0, discount_factor=0.01
        ),
    )
    # dispatch
    msg = "An installed capacity of 0 is not valid for dispatch mode."
    with pytest.raises(ValueError, match=msg):
        Boiler(
            name="central_gas_boiler",
            bus_in_fuel=bus,
            bus_out_heat=bus,
            opex_var=0,
            optimize_cap=False,
            project_data=Project(
                name="Project_X", lifetime=20, tax=0, discount_factor=0.01
            ),
        )
