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
    """
    Extra-pricing node coupling two investment capacities.

    This class models additional cost or funding.

    Variable cost can be limited to specific amount of energy.

    .. important ::
        If no ``full_load_time_limit`` the limited cost will be ignored.
        A basic amount of cost can be added to the result. This ammount is NOT
        part of the optimisation and will be ignored by the solver. Use it only
        if you know what you are doing.

    :Structure:
      *input*
        1. from_bus : ``bus_in``
      *output*
        1. to_bus : ``bus_out``

    :Optimization:
        To be written.

    Parameters
    ----------
    name : str
        Name of the component.
    bus_in : bus object
        Input bus from which the energy is drawn.
    bus_out : bus object
        Output bus into which the energy is fed.
    peak_price : float or None, default: None
        Peak price.
    cost_unlimited : float, default: 0
        Variable costs fo an unlimited amount of energy.
    cost_limited : float or None, default: None
        Variable costs of a limited amount of energy. Set full load time to
        define the amount of energy. If no full load time is defined, the
        cost_limited will be ignored.
    full_load_time_limit : float or None, default: None
        Maximum full load time to define the amount of energy for the limited
        cost. If "None" the limited cost are ignored.
    basic_amount : float, default: 0
        Fixed costs (basic amount) of the component. Will be added in the
        postprocessing and will be ignored in the optimisation. Only use if you
        know what you are doing.
    maximum_capacity : float, default: float("inf")
        Maximum capacity.

    Examples
    --------
    >>> from oemof.solph import Bus
    >>> from oemof.eesyplan.components.virtual import ExtraPricing
    >>> bus_in = Bus(label="bus_in")
    >>> bus_out = Bus(label="bus_out")
    >>> my_extra_pricing = ExtraPricing(
    ...     name="extra_pricing_node",
    ...     bus_in=bus_in,
    ...     bus_out=bus_out,
    ...     peak_price=500,
    ...     cost_unlimited=0.1,
    ...     cost_limited=0.2,
    ...     full_load_time_limit=3000,
    ...     basic_amount=100,
    ...     maximum_capacity=1000,
    ... )
    >>> my_extra_pricing.fix_cost
    100
    >>> my_extra_pricing.full_load_time_limit
    3000

    >>> my_extra_pricing_unlimited = ExtraPricing(
    ...     name="extra_pricing_unlimited",
    ...     bus_in=bus_in,
    ...     bus_out=bus_out,
    ... )
    >>> my_extra_pricing_unlimited.fix_cost
    0
    >>> my_extra_pricing_unlimited.full_load_time_limit is None
    True

    """

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
