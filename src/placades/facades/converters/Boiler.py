from oemof.solph import Flow
from oemof.solph.components import Converter

from placades.investment import _create_invest_if_wanted


class Boiler(Converter):
    def __init__(
        self,
        label,
        input_bus,
        output_bus,
        age_installed=0,
        installed_capacity=0,
        capex_specific=1000,
        opex_specific=1000,
        lifetime=20,
        optimize_cap=False,
        maximum_capacity=None,
        efficiency=0.8,
        dispatch_costs=0,
        expandable=True,
        project_data=None,
    ):
        """
        Boiler for heat generation.

        This class represents a boiler that burns fuel into
        thermal energy for heating applications.

        .. important ::
            The efficiency parameter determines the conversion rate
            from gas to thermal output.

        :Structure:
          *input*
            1. from_bus : Gas
          *output*
            1. to_bus : Heat

        Parameters
        ----------
        name : str
            Name of the asset.
        age_installed : int, default=0
            Number of years the asset has already been in operation.
        installed_capacity : float, default=0
            Already existing installed capacity.
        capex_fix : float, default=1000
            Specific investment costs of the asset related to the
            installed capacity (CAPEX).
        capex_var : float, default=1000
            Specific investment costs of the asset related to the
            installed capacity (CAPEX).
        opex_fix : float, default=10
            Specific operational and maintenance costs of the asset
            related to the installed capacity (OPEX_fix).
        opex_var : float, default=0.01
            Costs associated with a flow through/from the asset
            (OPEX_var or fuel costs).
        lifetime : int, default=20
            Number of operational years of the asset until it has to
            be replaced.
        optimize_cap : bool, default=False
            Choose if capacity optimization should be performed for
            this asset.
        maximum_capacity : float or None, default=None
            Maximum total capacity of an asset that can be installed
            at the project site.
        efficiency : float, default=0.8
            Ratio of energy output to energy input.

        Examples
        --------

        >>> from placades import Project
        >>> from oemof.solph import Bus
        >>> gas_bus = Bus(label="gas_bus")
        >>> heat_bus = Bus(label="heat_bus")
        >>> my_gas_boiler = Boiler(
        ...     label="central_gas_boiler",
        ...     input_bus=gas_bus,
        ...     output_bus=heat_bus,
        ...     age_installed=0,
        ...     installed_capacity=0,
        ...     capex_specific=1000,
        ...     opex_specific=1000,
        ...     lifetime=20,
        ...     optimize_cap=False,
        ...     maximum_capacity=None,
        ...     efficiency=0.8,
        ...     dispatch_costs=0,
        ...     expandable=True,
        ...     project_data=Project(
        ...         name="Project_X", lifetime=20, tax=0,
        ...         discount_factor=0.01),
        ...     )

        """
        nv = _create_invest_if_wanted(
            optimise_cap=expandable,
            capex_var=capex_specific,
            opex_fix=opex_specific,
            lifetime=lifetime,
            age_installed=age_installed,
            existing_capacity=installed_capacity,
            project_data=project_data,
        )

        inputs = {input_bus: Flow()}

        outputs = {
            output_bus: Flow(
                nominal_capacity=nv,
                variable_costs=dispatch_costs,
            )
        }

        self.name = label
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_fix = capex_specific
        self.capex_var = opex_specific
        self.dispatch_costs = dispatch_costs
        self.lifetime = lifetime
        self.optimize_cap = optimize_cap
        self.maximum_capacity = maximum_capacity
        self.efficiency = efficiency
        super().__init__(
            label=label,
            outputs=outputs,
            inputs=inputs,
            conversion_factors={output_bus: efficiency},
        )
