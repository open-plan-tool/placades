from oemof.eesyplan.facades.demand.demand import Demand


class H2Demand(Demand):
    def __init__(
        self, name, bus_in_hydrogen, input_timeseries, carrier="hydrogen"
    ):
        """
        Hydrogen demand/consumption component.

        This class represents a hydrogen demand that consumes hydrogen
        according to a specified time series pattern.

        :Structure:
            *input:*
                1. from_bus : Hydrogen

        Parameters
        ----------
        name : str
            |name|
        bus_in_hydrogen : oemof.eesyplan.CarrierBus
            |bus_in_hydrogen|
        input_timeseries : array-like
            |input_timeseries|

        Examples
        --------
        >>> from oemof.eesyplan import CarrierBus as Bus
        >>> h2_bus = Bus(name="hydrogen_bus")
        >>> my_h2_demand = H2Demand(
        ...     name="fuel_cell_demand",
        ...     bus_in_hydrogen=h2_bus,
        ...     input_timeseries="hydrogen_demand.csv",
        ... )

        """

        super().__init__(
            name=name,
            bus_in=bus_in_hydrogen,
            carrier=carrier,
            input_timeseries=input_timeseries,
        )
