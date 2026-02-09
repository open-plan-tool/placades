from oemof.solph import Flow
from oemof.solph.components import Sink


class HeatDemand(Sink):
    def __init__(self, name, bus_in_fuel, input_timeseries):
        """
        Gas demand/consumption component.

        This class represents a gas demand that consumes gas according
        to a specified time series pattern.
        :Structure:
            *input*
                1. bus_in_fuel : Gas

        Parameters
        ----------
        name : str
            |name|
        bus_in_fuel : placades.CarrierBus
            |bus_in_fuel|
        input_timeseries : array-like
            |input_timeseries|

        Examples
        --------
        >>> from placades import CarrierBus as Bus
        >>> fuel_bus = Bus(name="fuel_bus")
        >>> my_demand = HeatDemand(
        ...     name="office_demand",
        ...     bus_in_fuel=fuel_bus,
        ...     input_timeseries="fuel_demand.csv",
        ... )

        """

        self.profile = input_timeseries
        self.name = name

        super().__init__(
            label=name,
            inputs={
                bus_in_fuel: Flow(
                    fix=input_timeseries,
                    nominal_capacity=1,
                )
            },
        )
