from oemof.network import Sink
from oemof.solph.flows import Flow

class GasDemand(Sink):

        """
        Gas demand/consumption component.

        This class represents a gas demand that consumes gas according
        to a specified time series pattern.

        :Structure:
          *input*
            1. from_bus : Gas

        Parameters
        ----------
        label : str
            Name of the asset.
        input_timeseries : str or None, default=None
            Name of the csv file containing the input generation or
            demand timeseries.

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> gas_bus = Bus(label="gas_bus")
        >>> my_gas_demand = GasDemand(
        ...     name="industrial_gas_demand",
        ...     input_timeseries="gas_demand.csv",
        ... )

        """

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
