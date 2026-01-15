from oemof.solph import Flow
from oemof.solph.components import Sink


class Demand(Sink):
    def __init__(self, name, bus_in_heat, input_timeseries):
        """
        Heat demand/consumption component.

        This class represents a heat demand that consumes
        heat energy according to a specified time series pattern.

        :Structure:
            *input*
                1. from_bus : Heat

        Parameters
        ----------
        name : str
            |name|
        bus_in_heat : placades.CarrierBus
            |bus_in_heat|
        input_timeseries : array-like
            |input_timeseries|

        Examples
        --------
        >>> from placades import CarrierBus as Bus
        >>> heat_bus = Bus(name="heat_bus")
        >>> my_demand = Demand(
        ...     name="office_demand",
        ...     bus_in_heat=heat_bus,
        ...     input_timeseries="heat_demand.csv",
        ... )

        """

        self.profile = input_timeseries
        self.name = name

        super().__init__(
            label=name,
            inputs={
                bus_in_heat: Flow(
                    fix=input_timeseries,
                    nominal_capacity=1,
                )
            },
        )
