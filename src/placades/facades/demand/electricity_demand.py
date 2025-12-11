from oemof.solph import Flow
from oemof.solph.components import Sink


class Demand(Sink):
    """
    Electricity demand/consumption component.

    This class represents an electricity demand that consumes
    electrical energy according to a specified time series pattern.

    :Structure:
      *input*
        1. from_bus : Electricity

    Parameters
    ----------
    name : str
        |name|
    bus_in_electricity : placades.CarrierBus
        |bus_in_electricity|
    input_timeseries : str or None
        |input_timeseries|

    Examples
    --------
    >>> from placades import CarrierBus as Bus
    >>> ebus = Bus(label="electricity_bus")
    >>> my_demand = Demand(
    ...     name="office_demand",
    ...     bus_in_electricity=ebus,
    ...     input_timeseries="electricity_demand.csv",
    ... )
    """

    def __init__(self, name, bus_in_electricity, input_timeseries):
        self.profile = input_timeseries
        self.name = name

        super().__init__(
            label=name,
            inputs={
                bus_in_electricity: Flow(
                    fix=input_timeseries,
                    nominal_capacity=1,
                )
            },
        )
