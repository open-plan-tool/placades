from oemof.solph import Bus
from oemof.solph import Flow
from oemof.solph.components import Sink
from oemof.solph.components import Source


class CarrierBus(Bus):  # todo add shortage source and excess sink with costs
    """Bus mit Medium-Attribut"""

    def __init__(
        self,
        name,
        carrier=None,
        balanced=True,
        excess_cost=None,
        shortage_cost=None,
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
        balanced : bool
            Text
        excess_cost : float
            Text
        shortage_cost: float
            Text

        Examples
        --------
        >>> electricity_bus = CarrierBus(name="grid", carrier="electricity")
        >>> gas_bus = CarrierBus(name="gas_grid", carrier="natural_gas")
        >>> heat_bus = CarrierBus(name="district_heating", carrier="heat")
        >>> h2_bus = CarrierBus(name="h2_network", carrier="hydrogen")
        >>> h2_bus
        <CarrierBus 'h2_network' carrier='hydrogen'>
        """
        super().__init__(label=name, balanced=balanced)
        self.carrier = carrier
        self.name = name
        self.excess_cost = excess_cost
        self.shortage_cost = shortage_cost

        if excess_cost is not None:
            self.subnode(
                Sink,
                local_name="excess",
                inputs={
                    self: Flow(
                        variable_costs=excess_cost,
                    )
                },
            )

        if shortage_cost is not None:
            self.subnode(
                Source,
                local_name="shortage",
                inputs={
                    self: Flow(
                        variable_costs=shortage_cost,
                    )
                },
            )

    def __repr__(self):
        return (
            f"<CarrierBus '{self.name}', carrier='{self.carrier}'>, "
            f"shortage: {self.shortage_cost}, excess: {self.excess_cost}"
        )
