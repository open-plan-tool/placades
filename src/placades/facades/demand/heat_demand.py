from oemof.network import Sink
from oemof.solph.flows import Flow


class Demand(Sink):

    """
    Short description

    Long description about the facade and how to use it.

    .. important ::
        Some important information about this facade.

    :Structure:
      *output*
        1. bus_electricity : electricity
        2. bus_heat : heat
      *input*
        1. bus_gas : gas
        2. bus_coal : coal

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
    >>> from oemof.solph import Bus
    >>> hbus = Bus(label="my_heat_bus")
    """



        # add a description on how the GUI looks?

    def __init__(self, label, bus, profile):
        self.profile = profile
        self.name = label
        super().__init__(
            label=label,
            inputs={
                bus: Flow(
                    fix=profile,
                    nominal_capacity=1,
                )
            },
        )


class Excess(Sink):
    """
    Excess Node.
    """

    def __init__(self, label, bus, cost=0):
        super().__init__(
            label=label,
            inputs={bus: Flow(variable_costs=cost)},
        )
