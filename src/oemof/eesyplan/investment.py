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

def _create_invest_if_wanted(
    optimise_cap,
    existing_capacity,
    project_data,
    capex_var,
    opex_fix,
    lifetime,
    age_installed,
    maximum_capacity=float("+inf"),
    minimum_capacity=0,
):
    if optimise_cap:
        if age_installed != 0 or existing_capacity != 0:
            raise ValueError("When optimizing an asset no existing capacity or installation age is allowed")

    if age_installed > lifetime:
        raise ValueError("The lifetime of an existing asset needs to be higher than the age of the asset")

    epc = (
        project_data.calculate_epc(
            optimise_cap, capex_var, lifetime, age_installed, method="mvs"
        )
        + opex_fix
    )
    if optimise_cap is True:
        return Investment(
            ep_costs=epc,
            maximum=maximum_capacity,
            minimum=minimum_capacity,
        )
    else:
        return Investment(
            ep_costs=epc,
            maximum=existing_capacity,
            minimum=existing_capacity,
        )


def calculate_annuity_mvs(
    optimise_cap,
    capex_var,
    lifetime,
    age_installed,
    tax,
    lifetime_project,
    discount_factor,
):

    if optimise_cap:
        first_time_investment = 0
    else: #means that we don´t optimize but want only the replacement costs
        first_time_investment =  lifetime - age_installed


    if first_time_investment<lifetime_project: #only consider costs if first investment needed is in lifetime of the project
        NPV = capex_var * (1 + tax) * (1-discount_factor) ** first_time_investment
    else:
        NPV = 0

    eq_annual_capex = NPV * crf(lifetime, discount_factor)
    return eq_annual_capex
