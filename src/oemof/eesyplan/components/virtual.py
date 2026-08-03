from oemof.solph.components import Converter
from oemof.solph import Flow


class PeakPricing(Converter):
    def __init__(self):
        super().__init__()


class SpecificCost(Converter):
    def __init__(self, name, bus_in, bus_out, cost, capacity,
                 maximum_full_load_hours=None):
        nv = _create_invest_if_wanted(
            optimise_cap=optimize_cap,
            capex_var=capex_var,
            opex_fix=opex_fix,
            lifetime=lifetime,
            age_installed=age_installed,
            existing_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
            project_data=project_data,
        )

        super().__init__(
            label=name,
            outputs={
            bus_out: Flow(
                nominal_capacity=nv,
                variable_costs=cost,
            )
        },
            inputs={bus_in: Flow()},
        )
