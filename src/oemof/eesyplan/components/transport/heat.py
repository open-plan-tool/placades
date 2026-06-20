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
        relative_losses=0,
        return_pipe=True,
    ):
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
