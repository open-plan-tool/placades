from oemof.eesyplan.investment import calculate_annuity
from oemof.solph import Investment


class Project:
    def __init__(
        self,
        name,
        tax,
        discount_factor,
        economic_period=20,
    ):
        self.name = name
        self.tax = float(tax)
        self.economic_period = economic_period
        self.discount_factor = float(discount_factor)

    def calculate_annuity(self, capex_spec, asset_lifetime):
        """
        Calculate the annuity of investment..

        Parameters
        ----------
        capex_spec
        asset_lifetime

        Returns
        -------
        float or None

        Examples
        --------
        >>> my_project = Project(
        ...     name="my_project",
        ...     economic_period=20,
        ...     tax=0,
        ...     discount_factor=0.01
        ...     )
        >>> round(my_project.calculate_annuity(234, 20, 0), 3)
        12.967
        >>> my_project.calculate_annuity(234, 20, 0, "wrong")
        >>> round(my_project.calculate_annuity(234, 20, 0, "oemof"), 3)
        12.967

        """
        return calculate_annuity(
            capex_spec=capex_spec,
            asset_lifetime=asset_lifetime,
            tax=self.tax,
            discount_factor=self.discount_factor,
        )

    def create_invest_if_wanted(
        self,
        installed_capacity,
        capex_spec,
        opex_spec,
        lifetime,
        maximum_capacity,
        minimum_capacity,
    ):
        if (maximum_capacity or minimum_capacity) and installed_capacity:
            raise ValueError(
                "Maximum capacity and installed capacity can't be set at the same time. Create an existing component with an installed capacity or create an non existing component that shall be optimised"
            )

        if installed_capacity is None:
            specific_annual_cost = (
                self.calculate_annuity(capex_spec, lifetime) + opex_spec
            )
            return Investment(
                ep_costs=specific_annual_cost,
                existing=0,  # existing capacity with investment is not allowed
                maximum=maximum_capacity,
                minimum=minimum_capacity,
            )
        else:
            return installed_capacity
