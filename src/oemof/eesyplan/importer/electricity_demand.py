import datetime

import pandas as pd
from demandlib import bdew


def create_el_demand(
    profile_type,
    annual_electricity_demand,
    # todo: add a function to "restore variability or randomness to a profile"
):
    """
    Function to create a BDEW - standardized electricity load profiles.

    The BDEW standard electricity profiles are based on a large set of measured
    data averaged into a single load time series, which makes them suitable for
    aggregated demand studies but not ideal for simulating individual building
    peaks.

    profile_type: str
        A BDWD profile can be chosen. Available BDEW electricity profiles are:

        "H0_dyn" or "Household"
        "G0" or "General trade/business/commerce"
        "G1" or "Business on weekdays 8 a.m. - 6 p.m."
        "G2" or "Businesses with heavy consumption in the evening hours"
        "G3" or "Continuous running business"
        "G4" or "Shoping / barber shop"
        "G5" or "Bakery with baking"
        "G6" or "Weekend focused"
        "G7" or "Mobile phone transmitter stations"
        "L0" or "Agricultural"


    annual_electricity_demand: numeric
        total electricity demand in the chosen timeperiod

    Example:

    >>> from demandlib import bdew
    >>> electricity_demand = create_el_demand(
    ...     profile_type="household",
    ...     annual_electricity_demand=3000,)
    """

    # todo: get time from project
    times = pd.date_range(
        "2021-01-01 0:00", "2021-12-31 23:00", freq="1h", tz="Europe/Berlin"
    )

    # add holidays, holidays are treated as Sundays
    holidays = {
        # ToDo: Create a more accurate table based on location of project
        datetime.date(times[0].year, 1, 1): "New year",
        datetime.date(times[0].year, 5, 1): "Labour Day",
        datetime.date(times[0].year, 10, 3): "Day of German Unity",
        datetime.date(times[0].year, 12, 25): "Christmas Day",
        datetime.date(times[0].year, 12, 26): "Second Christmas Day",
    }

    match profile_type:
        case "General trade / business / commerce" | "G0":
            profile_type = "g0"
        case "Business on weekdays 8 a.m. - 6 p.m."  | "G1":
            profile_type = "g1"
        case "Businesses with heavy consumption in the evening hours"  | "G2":
            profile_type = "g2"
        case "Continuous running business"  | "G3":
            profile_type = "g3"
        case "Shop / barber shop"  | "G4":
            profile_type = "g4"
        case "Bakery with baking"  | "G5":
            profile_type = "g5"
        case "Weekend focused"  | "G6":
            profile_type = "g6"
        case "Mobile phone transmitter stations"  | "G7":
            profile_type = "g7"
        case "Agricultural"  | "L0":
            profile_type = "l0"
        case "Household"  | "H0_dyn":
            profile_type = "h0_dyn"

    e_slp = bdew.ElecSlp(year=times[0].year, holidays=holidays)
    demand_profile = e_slp.get_scaled_profiles(
        {profile_type: annual_electricity_demand}
    )

    return demand_profile
