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
        Name of the asset.
    input_timeseries : str or None, default=None
        Name of the csv file containing the input generation or
        demand timeseries.

    Examples
    --------
    >>> from oemof.solph import Bus
    >>> ebus = Bus(label="electricity_bus")
    >>> my_demand = Demand(
    ...     name="office_demand",
    ...     bus=ebus,
    ...     input_timeseries="electricity_demand.csv",
    ... )

    """

    def __init__(self, name, bus, input_timeseries):
        self.profile = input_timeseries
        self.name = name

        super().__init__(
            label=name,
            inputs={
                bus: Flow(
                    fix=input_timeseries,
                    nominal_capacity=1,
                )
            },
        )
