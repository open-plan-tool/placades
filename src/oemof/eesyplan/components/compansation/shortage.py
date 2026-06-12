from oemof.solph.components import Source
from oemof.solph.flows import Flow


class Shortage(Source):
    """
    Short description

    Long description about the facade and how to use it.

    .. important ::
        Some important information about this facade.


    Parameters
    ----------
    name : str
        |name|
    bus_out : oemof.solph.Bus or placade.CarrierBus
        |bus_in|
    cost : float or array-like
        |energy_prics|

    Examples
    --------
    >>> from oemof.eesyplan import CarrierBus
    >>> el_bus = CarrierBus(name="my_electricity_bus")
    >>> ex = Shortage("my_shortage", el_bus, 999)
    >>> ex.label
    'my_shortage'

    """

    def __init__(self, name, bus_out, cost):
        super().__init__(
            label=name,
            outputs={
                bus_out: Flow(
                    variable_costs=cost,
                )
            },
        )
