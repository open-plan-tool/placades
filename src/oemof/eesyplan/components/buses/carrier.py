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
        >>> electricity_bus = CarrierBus(name="grid", carrier="electricity",
        ...                      excess_cost=2)
        >>> electricity_bus.excess_cost
        2
        >>> heat_bus = CarrierBus(name="heating", carrier="heat")
        >>> heat_bus
        <CarrierBus 'heating', carrier='heat', shortage: None, excess: None>
        >>> h2_bus = CarrierBus(name="h2_network", carrier="hydrogen",
        ...                     excess_cost=0, shortage_cost=99)
        >>> h2_bus
        <CarrierBus 'h2_network', carrier='hydrogen', shortage: 99, excess: 0>
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
                outputs={
                    self: Flow(
                        variable_costs=shortage_cost,
                    )
                },
            )

    def __repr__(self):
        return (
            f"<CarrierBus '{self.name}', carrier='{self.carrier}', "
            f"shortage: {self.shortage_cost}, excess: {self.excess_cost}>"
        )
