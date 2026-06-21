from oemof.eesyplan.components.transport.heat import HeatingNetwork
from oemof.solph.components import Sink


def test_heating_network():
    hn = HeatingNetwork(name="Heating Network", absolute_losses=5)
    assert isinstance(hn, HeatingNetwork)
    assert isinstance(hn._Node__subnodes[0], Sink)
    hn_wo_losses = HeatingNetwork(name="Heating Network")
    assert hn_wo_losses._Node__subnodes == []
