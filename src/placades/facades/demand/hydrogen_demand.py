from oemof.solph import Flow
from oemof.solph.components import Sink


class H2Demand(Sink):
    def __init__(self, name, bus_in_hydrogen, input_timeseries):
        """
        Hydrogen demand/consumption component.

        This class represents a hydrogen demand that consumes hydrogen
        according to a specified time series pattern.

        :Structure:
        *input*
            1. from_bus : Hydrogen

        Parameters
        ----------
        name : str
            |name|
        bus_in_hydrogen : placades.CarrierBus
            |bus_in_hydrogen|
        input_timeseries : array-like
            |input_timeseries|

        Examples
        --------
        >>> from placades import CarrierBus as Bus
        >>> h2_bus = Bus(label="hydrogen_bus")
        >>> my_h2_demand = H2Demand(
        ...     name="fuel_cell_demand",
        ...     bus_in_hydrogen=h2_bus,
        ...     input_timeseries="hydrogen_demand.csv",
        ... )

        """

        self.profile = input_timeseries
        self.name = name

        super().__init__(
            label=name,
            inputs={
                bus_in_hydrogen: Flow(
                    fix=input_timeseries,
                    nominal_capacity=1,
                )
            },
        )
