from oemof.solph import Bus


class CarrierBus(Bus):  # todo add shortage source and excess sink with costs
    """Bus mit Medium-Attribut"""

    def __init__(self, label, carrier=None):
        """
        Bus mit Energieträger-Information

        Parameters
        ----------
        label : str or tuple
            Eindeutige Bezeichnung des Bus
        carrier : str
            Energieträger/Medium (z.B. 'electricity', 'gas', 'heat',
            'hydrogen')
        **kwargs
            Weitere Parameter für Bus

        Examples
        --------
        >>> electricity_bus = CarrierBus(label="grid", carrier="electricity")
        >>> gas_bus = CarrierBus(label="gas_grid", carrier="natural_gas")
        >>> heat_bus = CarrierBus(label="district_heating", carrier="heat")
        >>> h2_bus = CarrierBus(label="h2_network", carrier="hydrogen")
        """
        super().__init__(label=label)
        self.carrier = carrier

    def __repr__(self):
        return f"<CarrierBus '{self.label}' carrier='{self.carrier}'>"
