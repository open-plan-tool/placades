from oemof.network import Node
from oemof.solph import Bus, Investment
from oemof.solph import Flow
from oemof.solph.components import Converter
from oemof.solph.components import Sink
from oemof.solph.components import Source


class DSO(Node):
    def __init__(
        self,
        name,
        bus,
        maximum_capacity,
        energy_price,
        feedin_tariff,
        peak_demand_pricing=0,
        # peak_demand_pricing_period=1, ToDo: Still important? Not used!
        basic_amount=0,  # Warnung, weil nur für Profis :-)
    ):
        """
        Energy provider for electricity distribution.

        This class represents a distribution system operator (DSO) that
        provides electricity from the utility grid with pricing and
        feedin capabilities.

        .. important ::
            The renewable share affects the overall system renewable
            factor calculation.

        :Structure:
          *input* & *output*
            bus : Electricity

        Parameters
        ----------
        name : str
            |name|
        energy_price : float, default=0.3
            |energy_prices|
        feedin_tariff : float, default=0.1
            |feedin_tariff|
        peak_demand_pricing : float, default=0
            |peak_demand_pricing|
        peak_demand_pricing_period : int, default=1
            |peak_demand_period|
        renewable_share : float, default=0.44
            |renewable_share|
        feedin_cap : float or None, default=None
            |feedin_cap|

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> ebus = Bus(label="any_bus")
        >>> my_dso = DSO(
        ...     name="any_network",
        ...     bus=ebus,
        ...     energy_price=0.25,
        ...     feedin_tariff=0.08,
        ... )

        """
        self.name = name
        self.bus = bus
        self.maximum_capacity = maximum_capacity
        self.energy_price = energy_price
        self.feedin_tariff = feedin_tariff
        self.peak_demand_pricing = peak_demand_pricing
        self.fix_cost = basic_amount

        super().__init__(label=self.name)

        self.subnode(
            Sink,
            inputs={
                self.bus: Flow(
                    variable_costs=self.feedin_tariff * -1,
                    nominal_capacity=self.maximum_capacity,
                )
            },
            local_name="feedin_sink",
        )

        self.subnode(
            Source,
            outputs={
                self.bus: Flow(
                    variable_costs=self.energy_price,
                    nominal_capacity=Investment(
                        ep_costs=self.peak_demand_pricing,
                        maximum=self.maximum_capacity,
                    ),
                )
            },
            local_name="consumption_source",
        )
