from oemof.solph import Investment


def create_invest_if_wanted(
    optimise_cap, existing_capacity, project_data, **kwargs
):
    if optimise_cap is True:
        epc = project_data.calculate_epc(method="oemof")
        return Investment(ep_costs=epc)
    else:
        return existing_capacity


def calculate_annuity_mvs(
    capex_var,
    capex_fix,
    lifetime,
    age_installed,
    tax,
    lifetime_project,
    discount_factor,
):
    # ToDo: (RLI) Add MVS method for the annuity/epc.
    return 5
