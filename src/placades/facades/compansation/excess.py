from oemof.solph import Flow
from oemof.solph.components import Sink


class Excess(Sink):
    """
    Short description

    Long description about the facade and how to use it.

    .. important ::
        Some important information about this facade.


    Parameters
    ----------
    name : str
        |name|
    bus_in : oemof.solph.Bus or placade.CarrierBus
        |bus_in|
    cost : float or array-like
        |cost|

    Examples
    --------

    """

    def __init__(self, name, bus_in, cost):
        super().__init__(
            label=name,
            inputs={
                bus_in: Flow(
                    variable_costs=cost,
                )
            },
        )
