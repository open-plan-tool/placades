from oemof.solph.components import GenericStorage
from oemof.solph import Flow

class ElectricalStorage(GenericStorage):
    def __init__(
        self,
        name,
    ):
        """
        Battery Energy Storage System (BESS).

        This class represents a complete battery energy storage system
        for electrical energy storage and dispatch.

        .. important ::
            This is a simplified representation of a complete BESS
            including all necessary components.

        :Structure:
          *input*
            1. charge : Electricity
          *output*
            1. discharge : Electricity

        Parameters
        ----------
        name : str
            Name of the asset.

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> ebus = Bus(label="electricity_bus")
        >>> my_bess = ElectricalStorage(
        ...     name="lithium_battery_system",
        ... )

        """
        self.name = name
        super().__init__()
