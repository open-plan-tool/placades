from oemof.network import Node
from oemof.solph import Bus
from oemof.solph import Flow
from oemof.solph.components import Converter
from oemof.solph.components import Sink
from oemof.solph.components import Source


class DSO(Node):
    def __init__(
        self,
        name,
        bus,
        energy_price=0.12,
        feedin_tariff=0.05,
        peak_demand_pricing=0,
        peak_demand_pricing_period=1,
        renewable_share=0,
        feedin_cap=None,
    ):
        """
        Energy provider for Gas distribution.

        This class represents a distribution system operator (DSO) that
        provides gas from the utility grid with pricing and
        feedin capabilities.

        .. important ::
            The renewable share affects the overall system renewable
            factor calculation.

        :Structure:
          *input* & *output*
            bus : gas

        Parameters
        ----------
        name : str
            |name|
        energy_price : float, default=0.12
            |energy_prics|
        feedin_tariff : float, default=0.05
            |feedin_tariff|
        peak_demand_pricing : float, default=0
            |peak_demand_pricing|
        peak_demand_pricing_period : int, default=1
            |peak_demand_period|
        renewable_share : float, default=0
            |renewable_share|
        feedin_cap : float or None, default=None
            |feedin_cap|

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> gbus = Bus(label="gas_bus")
        >>> my_dso = DSO(
        ...     name="gas_grid",
        ...     bus=gbus,
        ...     energy_price=0.12,
        ...     feedin_tariff=0.00,
        ... )

        """
        self.name = name
        self.bus_electricity = bus
        self.energy_price = energy_price
        self.feedin_tariff = feedin_tariff
        self.peak_demand_pricing = peak_demand_pricing
        self.peak_demand_pricing_period = peak_demand_pricing_period
        self.renewable_share = renewable_share
        self.feedin_cap = feedin_cap

        super().__init__(label=self.name)

        internal_bus = self.subnode(Bus, local_name="internal_bus")

        self.subnode(
            Converter,
            inputs={
                self.bus_electricity: Flow(
                    variable_costs=self.feedin_tariff * -1
                )
            },
            outputs={internal_bus: Flow()},
            local_name="feedin_converter",
        )

        self.subnode(
            Sink, inputs={internal_bus: Flow()}, local_name="feedin_sink"
        )

        self.subnode(
            Converter,
            inputs={internal_bus: Flow()},
            outputs={
                self.bus_electricity: Flow(variable_costs=self.energy_price)
            },
            local_name="consumption_converter",
        )

        self.subnode(
            Source,
            outputs={internal_bus: Flow()},
            local_name="consumption_source",
        )
