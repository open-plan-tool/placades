from oemof.eesyplan import CarrierBus
from oemof.network import Node
from oemof.solph import Flow
from oemof.solph.components import Converter
from oemof.solph.components import Sink


class HeatingNetwork(CarrierBus):
    def __init__(
        self,
        name,
        absolute_losses=None,  # ToDo: wie werden die angegeben: pro timestep?
    ):
        """

        Parameters
        ----------
        name : string
            |name|
        absolute_losses : float, optional
            |absolute_losses|

        Examples
        --------
        >>> hn = HeatingNetwork(name="Heating Network", absolute_losses=5)
        """
        self.name = name

        super().__init__(name=self.name, carrier="heat")

        if absolute_losses is not None:
            self.subnode(
                Sink,
                local_name="absolute_losses",
                inputs={self: Flow(nominal_capacity=1, fix=absolute_losses)},
            )


class HeatingPipe(Node):
    def __init__(
        self,
        name,
        bus_1_heat,
        bus_2_heat,
        absolute_losses=None,  # ToDo: wie werden die angegeben: pro timestep?
        relative_losses=0.0,
        return_pipe=True,
    ):
        """

        Parameters
        ----------
        name : string
            |name|
        bus_1_heat : Node object
            |bus_1_heat|
        bus_2_heat : Node object
            |bus_2_heat|
        absolute_losses : float, optional (default: None)
            |absolute_losses|
        relative_losses : float, optional (default: 0.0)
            |relative_losses|
        return_pipe : bool, optional (default: True)
            |return_pipe|

        Examples
        --------
        >>> w = HeatingNetwork(name="Heating Network West", absolute_losses=5)
        >>> e = HeatingNetwork(name="Heating Network East")
        >>> pipe1 =HeatingPipe(name="pipe1", bus_1_heat=w, bus_2_heat=e,
        ...                    relative_losses=0.1, return_pipe=True)
        >>> pipe2 =HeatingPipe(name="pipe1", bus_1_heat=w, bus_2_heat=e,
        ...                    absolute_losses=1, return_pipe=False)

        """
        self.name = name

        super().__init__(label=self.name)

        self.subnode(
            Converter,
            inputs={bus_1_heat: Flow()},
            outputs={bus_2_heat: Flow()},
            local_name="heat_pipeline_1_2",
            conversion_factors={bus_2_heat: (1 - relative_losses)},
        )
        if return_pipe:
            self.subnode(
                Converter,
                inputs={bus_2_heat: Flow()},
                outputs={bus_1_heat: Flow()},
                local_name="heat_pipeline_2_1",
                conversion_factors={bus_1_heat: (1 - relative_losses)},
            )
        if absolute_losses is not None:
            self.subnode(
                Sink,
                local_name="absolute_losses",
                inputs={
                    bus_1_heat: Flow(nominal_capacity=1, fix=absolute_losses)
                },
            )
