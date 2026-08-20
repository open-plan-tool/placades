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

    Examples
    --------
    >>> round(crf(10, 0.05), 5)
    0.1295

    """
    if discount_factor != 0:
        vcrf = (discount_factor * (1 + discount_factor) ** duration) / (
            (1 + discount_factor) ** duration - 1
        )
    else:
        vcrf = 1 / duration

    return vcrf


def calculate_annuity(
    capex_spec,
    asset_lifetime,
    tax,
    discount_factor,
):
    """
    Calculates the annuity.

    Parameters
    ----------
    capex_spec
    asset_lifetime
    tax
    discount_factor

    Returns
    -------

    Examples
    --------
    >>> round(calculate_annuity(100, 15, 0.01, 0.05), 5)
    9.73057

    """
    npv = capex_spec * (1 + tax)

    annuity = npv * crf(asset_lifetime, discount_factor)
    return annuity
