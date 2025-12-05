from placades.type_checks import check_parameter

try:
    from oemof.tools.economics import annuity
except ModuleNotFoundError:
    annuity = None

from placades.investment import calculate_annuity_mvs


class Project:
    def __init__(
        self,
        name,
        lifetime,
        tax,
        discount_factor,
        shortage_cost=999,
        excess_cost=99,
        disable_shortage=False,
        disable_excess=False,
        latitude= 50.587031,
        longitude=10.165876
    ):
        self.name = name
        self.tax = tax
        self.lifetime = lifetime
        self.discount_factor = discount_factor
        self.shortage_cost = shortage_cost
        self.excess_cost = excess_cost

    def calculate_epc(self, capex_var, lifetime, age_installed, method="mvs"):
        if method == "mvs":
            check_parameter(
                capex_var,
                self.lifetime,
                self.discount_factor,
                lifetime,
                self.tax,
                age_installed,
            )
            return calculate_annuity_mvs(
                capex_var=capex_var,
                lifetime=lifetime,
                age_installed=age_installed,
                tax=self.tax,
                lifetime_project=self.lifetime,
                discount_factor=self.discount_factor,
            )
        elif method == "oemof":
            check_missing_module(annuity, "oemof", "oemof-tools")
            check_parameter(
                capex_var, self.lifetime, self.discount_factor, lifetime
            )
            return annuity(
                capex=capex_var,
                n=self.lifetime,
                wacc=self.discount_factor,
                u=lifetime,
            )
        return None


def check_missing_module(module, name, package):
    if module is None:
        msg = (
            f"To use the annuity method of {name} the package "
            f"{package} is needed.\nUse `pip install {package}` "
            "to install it."
        )
        raise ModuleNotFoundError(msg)
