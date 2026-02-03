from placades.facades.providers.dso import DSO


class DsoHeat(DSO):
    def __init__(
        self,
        name,
        bus_heat,
        energy_price=0.3,
        feedin_tariff=0.1,
        peak_demand_pricing=0,
        peak_demand_pricing_period=1,
        renewable_share=0.44,
        feedin_cap=None,
    ):
        """
        Energy provider for heat distribution.

        This class represents a distribution system operator (DSO) that
        provides heat from the utility grid with pricing and
        feedin capabilities.

        .. important ::
            The renewable share affects the overall system renewable
            factor calculation.

        :Structure:
          *input* & *output*
            bus : Heat

        Parameters
        ----------
        name : str
            |name|
        energy_price : float, default=0.3
            |energy_prics|
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
        >>> from placades import CarrierBus, DsoElectricity
        >>> hbus = CarrierBus(name="heat_bus")
        >>> my_dso = DsoFuel(
        ...     name="main_grid",
        ...     bus_heat=ebus,
        ...     energy_price=0.25,
        ...     feedin_tariff=0.08,
        ... )

        """
        super().__init__(
            name=name,
            bus=bus_heat,
            energy_price=energy_price,
            feedin_tariff=feedin_tariff,
            peak_demand_pricing=peak_demand_pricing,
            peak_demand_pricing_period=peak_demand_pricing_period,
            renewable_share=renewable_share,
            feedin_cap=feedin_cap,
        )
