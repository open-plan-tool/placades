from oemof.solph.components import GenericStorage
from oemof.solph import Flow

class FuelStorage(GenericStorage):
    def __init__(
        self,
        name,
    ):
        """
        Gas Energy Storage System (GESS).

        This class represents a gas energy storage system for storing
        and dispatching gas energy carriers.

        .. important ::
            This system can store various types of gas including natural
            gas and biogas.

        :Structure:
          *input*
            1. charge : Gas
          *output*
            1. discharge : Gas

        Parameters
        ----------
        name : str
            Name of the asset.

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> gas_bus = Bus(label="gas_bus")
        >>> my_gess = FuelStorage(
        ...     name="gas_storage_tank",
        ... )

        """
        self.name = name
        super().__init__()
