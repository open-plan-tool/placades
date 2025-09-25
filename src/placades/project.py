try:
    from oemof.tools.economics import annuity
except ModuleNotFoundError:
    annuity = None

from placades.investment import calculate_annuity_mvs


class ProjectData:
    def __init__(self, name, lifetime, tax, discount_factor):
        self.name = name
        self.tax = tax
        self.lifetime = lifetime
        self.discount_factor = discount_factor

    def calculate_epc(self, capex_var, capex_fix, lifetime, method="mvs"):
        if method == "mvs":
            return calculate_annuity_mvs()
        elif method == "oemof":
            if annuity is None:
                msg = (
                    "To use the annuity method of oemof the package "
                    "oemof-tools is needed.\nUse `pip install oemof-tools` "
                    "to install it."
                )
                raise ModuleNotFoundError(msg)

            return annuity(
                capex_var, self.lifetime, self.discount_factor, u=lifetime
            )
        return None
