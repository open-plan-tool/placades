from oemof.solph.components import GenericStorage
from oemof.solph import Flow


class ThermalStorage(GenericStorage):
    def __init__(
        self,
        name,
    ):
        """
        Heat Energy Storage System (HESS).

        This class represents a thermal energy storage system for storing
        and dispatching thermal energy for heating applications.

        .. important ::
            This system can store thermal energy for later use in
            heating applications.

        :Structure:
          *input*
            1. charge : Heat
          *output*
            1. discharge : Heat

        Parameters
        ----------
        name : str
            Name of the asset.

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> heat_bus = Bus(label="heat_bus")
        >>> my_hess = ThermalStorage(
        ...     name="thermal_storage_tank",
        ... )

        """
        self.name = name
        super().__init__()
