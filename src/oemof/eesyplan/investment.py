import warnings

import pandas as pd


def crf(duration, discount_factor):
    """
    Calculates the capital recovery factor which is used to convert a one-time
    investment into an equivalent annual cost over a given duration

    Parameters
    ----------
    duration : int
        Time period of the series of equal payments (usually equal asset lifetime)
    discount_factor : float
        Weighted average cost of capital, which is the after-tax average cost
        of various capital sources

    Returns
    -------
    float : CRF capital recovery factor, used to convert a one-time
    investment into an equivalent annual cost over a given duration

    """
    if discount_factor != 0:
        vcrf = (discount_factor * (1 + discount_factor) ** duration) / (
            (1 + discount_factor) ** duration - 1
        )
    else:
        vcrf = 1 / duration

    return vcrf


def get_replacement_costs(  # todo Function not needed anymore, CRF-Method is consistent and no extra calculations needed (delete at some point)
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
        [0.0 for _i in range(project_lifetime + 1)],
        index=list(range(project_lifetime + 1)),
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


def calculate_annuity(  # Todo Costs of existing components will be calculated in postprocessing
    capex_spec,
    asset_lifetime,
    tax,
    discount_factor,
):
    npv = capex_spec * (1 + tax)

    annuity = npv * crf(asset_lifetime, discount_factor)
    return annuity
