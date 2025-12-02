from oemof.solph.components import GenericStorage
from oemof.solph import Flow


class HydrogenStorage(GenericStorage):
    def __init__(
        self,
        name,
    ):
        """
        Hydrogen Energy Storage System (H2ESS).

        This class represents a hydrogen energy storage system for storing
        and dispatching hydrogen gas for various applications.

        .. important ::
            This system requires specialized storage technology for
            hydrogen handling and safety.

        :Structure:
          *input*
            1. charge : H2
          *output*
            1. discharge : H2

        Parameters
        ----------
        name : str
            Name of the asset.

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> h2_bus = Bus(label="hydrogen_bus")
        >>> my_h2ess = HydrogenStorage(
        ...     name="hydrogen_storage_tank",
        ... )

        """
        self.name = name
        super().__init__()
