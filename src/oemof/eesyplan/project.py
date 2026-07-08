from oemof.eesyplan.investment import calculate_annuity_mvs
from oemof.eesyplan.type_checks import check_parameter
from oemof.tools.economics import annuity


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
        latitude=50.587031,
        longitude=10.165876,
    ):
        self.name = name
        self.tax = float(tax)
        self.lifetime = lifetime
        self.discount_factor = float(discount_factor)
        self.shortage_cost = shortage_cost
        self.excess_cost = excess_cost

    def calculate_epc(self, capex_var, lifetime, age_installed, method="mvs"):
        """
        Calculate the annuity of investment..

        Parameters
        ----------
        capex_var
        lifetime
        age_installed
        method

        Returns
        -------
        float or None

        Examples
        --------
        >>> my_project = Project(
        ...     name="my_project",
        ...     lifetime=20,
        ...     tax=0,
        ...     discount_factor=0.01
        ...     )
        >>> round(my_project.calculate_epc(234, 20, 0), 3)
        12.967
        >>> my_project.calculate_epc(234, 20, 0, "wrong")
        >>> round(my_project.calculate_epc(234, 20, 0, "oemof"), 3)
        12.967

        """
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
