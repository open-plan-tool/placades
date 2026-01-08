from oemof.solph import Bus


class CarrierBus(Bus):  # todo add shortage source and excess sink with costs
    """Bus mit Medium-Attribut"""

    def __init__(
        self, name, carrier=None, balanced=None, excess=None, excess_costs=None
    ):
        """
        Bus mit Energieträger-Information

        Parameters
        ----------
        name : str or tuple
            Eindeutige Bezeichnung des Bus
        carrier : str
            Energieträger/Medium (z.B. 'electricity', 'gas', 'heat',
            'hydrogen')
        **kwargs
            Weitere Parameter für Bus

        Examples
        --------
        >>> electricity_bus = CarrierBus(name="grid", carrier="electricity")
        >>> gas_bus = CarrierBus(name="gas_grid", carrier="natural_gas")
        >>> heat_bus = CarrierBus(name="district_heating", carrier="heat")
        >>> h2_bus = CarrierBus(name="h2_network", carrier="hydrogen")
        """
        super().__init__(label=name)
        self.carrier = carrier
        self.name = name

    def __repr__(self):
        return f"<CarrierBus '{self.name}' carrier='{self.carrier}'>"
