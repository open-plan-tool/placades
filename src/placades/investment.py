import warnings

import pandas as pd
from oemof.solph import Investment


def crf(project_life, discount_factor):
    """
    Calculates the capital recovery ratio used to determine the present value
    of a series of equal payments (annuity)

    From mvs src/multi_vector_simulator/C2_economic_functions.py

    Parameters
    ----------
    project_life : int
        Time period over which the costs of the system occur
    discount_factor : float
        Weighted average cost of capital, which is the after-tax average cost
        of various capital sources

    Returns
    -------
    float : capital recovery factor, a ratio used to calculate the present
        value of an annuity

    """
    if discount_factor != 0:
        crfv = (discount_factor * (1 + discount_factor) ** project_life) / (
            (1 + discount_factor) ** project_life - 1
        )
    else:
        crfv = 1 / project_life

    return crfv


def get_replacement_costs(
    age_of_asset,
    project_lifetime,
    asset_lifetime,
    first_time_investment,
    discount_factor,
):
    """From mvs src/multi_vector_simulator/C2_economic_functions.py"""
    if project_lifetime + age_of_asset == asset_lifetime:
        number_of_investments = 1
    else:
        number_of_investments = round(
            (project_lifetime + age_of_asset) / asset_lifetime + 0.5
        )

    replacement_costs = 0
    latest_investment = first_time_investment
    year = -age_of_asset
    if abs(year) > asset_lifetime:
        warnings.warn(
            f"The age of the asset ({age_of_asset} years) is lower or equal "
            f"than the asset lifetime ({asset_lifetime} years). This does not "
            f"make sense, as a replacement is imminent or should already have "
            f"happened. Please check this value.",
            stacklevel=2,
        )

    present_value_of_capital_expenditures = pd.DataFrame(
        [0 for _i in range(project_lifetime + 1)],
        index=[j for j in range(project_lifetime + 1)],
    )

    for _count_of_replacements in range(1, number_of_investments):
        year += asset_lifetime
        if year < project_lifetime:
            latest_investment = first_time_investment / (
                (1 + discount_factor) ** year
            )
            replacement_costs += latest_investment
            present_value_of_capital_expenditures.loc[year] = latest_investment
        elif year == project_lifetime:
            warnings.warn(
                "No asset replacement costs are computed for the project's "
                "last year as the asset reach its end-of-life exactly on that"
                " year",
                stacklevel=2,
            )

    if year != project_lifetime:
        year += asset_lifetime
    if year > project_lifetime:
        linear_depreciation_last_investment = (
            latest_investment / asset_lifetime
        )
        value_at_project_end = (
            linear_depreciation_last_investment
            * (year - project_lifetime)
            / (1 + discount_factor) ** project_lifetime
        )
        replacement_costs -= value_at_project_end
        present_value_of_capital_expenditures.loc[
            project_lifetime
        ] = -value_at_project_end

    return replacement_costs


def _create_invest_if_wanted(
    optimise_cap,
    existing_capacity,
    project_data,
    capex_var,
    opex_fix,
    lifetime,
    age_installed,
):
    if optimise_cap is True:
        epc = (
            project_data.calculate_epc(
                capex_var, lifetime, age_installed, method="oemof"
            )
            + opex_fix
        )
        return Investment(ep_costs=epc)
    else:
        return existing_capacity


def calculate_annuity_mvs(
    capex_var,
    lifetime,
    age_installed,  # was used in a second call of get_replacement_costs
    tax,
    lifetime_project,
    discount_factor,
):
    # ToDo: As I understand it should be: remaining = lifetime - age_installed
    first_time_investment = capex_var * (1 + tax)
    specific_replacement_costs_optimized = get_replacement_costs(
        0, lifetime_project, lifetime, first_time_investment, discount_factor
    )
    specific_capex = (
        first_time_investment + specific_replacement_costs_optimized
    )

    specific_capex *= crf(lifetime_project, discount_factor)
    return specific_capex
