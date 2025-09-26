from oemof.network import Node
from oemof.solph.flows import Flow


class Source(Node):
    """
    Short description

    Long description about the facade and how to use it.

    .. important ::
        Some important information about this facade.


    Parameters
    ----------
    label : str or tuple
        Unique identifier of the instance.
    bus : oemof.solph.Bus or placade.CarrierBus
        Valid network bus with the carrier: electricity
    profile : iterable
        Absolute demand time series.

    Examples
    --------

    """

    def __init__(self, label, bus, cost, project):
        super().__init__(
            label=label,
            outputs={
                bus: Flow(
                    variable_costs=cost,
                )
            },
        )
