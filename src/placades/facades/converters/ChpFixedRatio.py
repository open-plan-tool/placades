from oemof.solph.components import Converter


class ChpFixedRatio(Converter):
    def __init__(
        self,
        name,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        opex_fix=10,
        lifetime=20,
        optimize_cap=False,
        maximum_capacity=None,
        efficiency_multiple=None,
        efficiency=0.8,
    ):
        """
        Combined Heat and Power plant with fixed heat-to-power ratio.

        This class represents a CHP plant that operates with a fixed
        ratio between heat and electricity generation, providing less
        operational flexibility but simpler control.

        .. important ::
            The fixed ratio constraint limits operational flexibility
            but ensures consistent heat-to-power ratios.

        :Structure:
          *input*
            1. fuel : Gas
          *output*
            1. heat_bus : Heat
            2. electricity_bus : Electricity

        Parameters
        ----------
        name : str
            Name of the asset.
        age_installed : int, default=0
            Number of years the asset has already been in operation.
        installed_capacity : float, default=0
            Already existing installed capacity.
        capex_var : float, default=1000
            Specific investment costs of the asset related to the
            installed capacity (CAPEX).
        opex_fix : float, default=10
            Specific operational and maintenance costs of the asset
            related to the installed capacity (OPEX_fix).
        lifetime : int, default=20
            Number of operational years of the asset until it has to
            be replaced.
        optimize_cap : bool, default=False
            Choose if capacity optimization should be performed for
            this asset.
        maximum_capacity : float or None, default=None
            Maximum total capacity of an asset that can be installed
            at the project site.
        efficiency_multiple : float or None, default=None
            Multiple efficiency values for different outputs.
        efficiency : float, default=0.8
            Ratio of energy output to energy input.

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> gas_bus = Bus(label="gas_bus")
        >>> heat_bus = Bus(label="heat_bus")
        >>> el_bus = Bus(label="electricity_bus")
        >>> my_chp_fixed = ChpFixedRatio(
        ...     name="fixed_ratio_chp",
        ...     installed_capacity=300,
        ...     efficiency=0.8,
        ... )

        """
        self.name = name
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_var = capex_var
        self.opex_fix = opex_fix
        self.lifetime = lifetime
        self.optimize_cap = optimize_cap
        self.maximum_capacity = maximum_capacity
        self.efficiency_multiple = efficiency_multiple
        self.efficiency = efficiency
        super().__init__()
