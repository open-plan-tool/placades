from oemof.network import Node
from oemof.solph import Flow
from oemof.solph import Investment
from oemof.solph.components import Converter
from pyomo.core.base.block import ScalarBlock
from pyomo.environ import Constraint
from oemof.eesyplan.model import CONSTRAINT_GROUPS


class PeakPricingBlock(ScalarBlock):
    """Kopplung der beiden Investment-Kapazitäten pro PeakPricing-Node."""

    def _create(self, group=None):
        if group is None:
            return None

        m = self.parent_block()

        def _invest_equal_rule(block, n):
            conv1 = n.subnodes[0]
            conv2 = n.subnodes[1]

            bus1 = list(conv1.inputs.keys())[0]
            bus2 = list(conv2.inputs.keys())[0]

            return (
                m.InvestmentFlowBlock.invest[bus1, conv1, 0]
                == m.InvestmentFlowBlock.invest[bus2, conv2, 0]
            )

        self.invest_equal = Constraint(group, rule=_invest_equal_rule)


Model.CONSTRAINT_GROUPS.append(ExtraPricingBlock)


class PeakPricing(Node):

    def constraint_group(self):
        return PeakPricingBlock

    def __init__(
        self,
        name,
        bus_in,
        bus_out,
        peak_price,
        cost1,
        cost2,
        flh,
        basic_amount=0,
        maximum_capacity=float("inf"),
    ):
        super().__init__(label=name)

        self.fix_cost = basic_amount

        self.subnode(
            Converter,
            inputs={
                bus_in: Flow(
                    nominal_capacity=Investment(
                        ep_costs=0, maximum=maximum_capacity
                    ),
                    variable_costs=cost1,
                )
            },
            outputs={bus_out: Flow()},
            local_name="peak_price_converter",
        )

        self.subnode(
            Converter,
            inputs={
                bus_in: Flow(
                    nominal_capacity=Investment(
                        ep_costs=peak_price, maximum=maximum_capacity
                    ),
                    variable_costs=cost2,
                    full_load_time_max=flh,
                )
            },
            outputs={bus_out: Flow()},
            local_name="peak_price_converter_flh",
        )
