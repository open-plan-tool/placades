from oemof.network import Node
from oemof.solph import Flow
from oemof.solph import Investment
from oemof.solph.components import Converter
from pyomo.core.base.block import ScalarBlock
from pyomo.environ import Constraint, Var
from oemof.solph import Model


class ExtraPricingBlock(ScalarBlock):
    """Kopplung der beiden Investment-Kapazitäten pro extraPricing-Node."""

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


class ExtraPricing(Node):

    def __init__(
        self,
        name,
        bus_in,
        bus_out,
        peak_price=None,
        cost_unlimited=0,
        cost_limited=None,
        full_load_time_limit=None,
        basic_amount=0,
        maximum_capacity=float("inf"),
    ):
        super().__init__(label=name)

        self.fix_cost = basic_amount
        self.full_load_time_limit = full_load_time_limit

        self.subnode(
            Converter,
            inputs={
                bus_in: Flow(
                    nominal_capacity=Investment(
                        ep_costs=0, maximum=maximum_capacity
                    ),
                    variable_costs=cost_unlimited,
                )
            },
            outputs={bus_out: Flow()},
            local_name="extra_price_converter",
        )

        if full_load_time_limit is not None:
            self.subnode(
                Converter,
                inputs={
                    bus_in: Flow(
                        nominal_capacity=Investment(
                            ep_costs=peak_price, maximum=maximum_capacity
                        ),
                        variable_costs=cost_limited,
                        full_load_time_max=full_load_time_limit,
                    )
                },
                outputs={bus_out: Flow()},
                local_name="extra_price_converter_flh",
            )

    def constraint_group(self):
        if self.full_load_time_limit is not None:
            return ExtraPricingBlock
        else:
            return None
