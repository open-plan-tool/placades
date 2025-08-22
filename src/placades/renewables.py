from oemof.solph import Facade
from oemof.solph.components import Source
from oemof.solph.flows import Flow


class PV(Facade):
    def __init__(self, label, el_bus, peak_capacity, normalised_output, *args):
        self.peak_capacity = peak_capacity
        self.normalised_output = normalised_output
        self.el_bus = el_bus
        super().__init__(*args, label=label, facade_type=type(self))

    def define_subnetwork(self):
        self.subnode(
            Source,
            outputs={
                self.el_bus: Flow(
                    fix=self.normalised_output,
                    nominal_capacity=self.peak_capacity,
                )
            },
            label="pv_source",
        )
