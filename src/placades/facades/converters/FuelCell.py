from oemof.solph import Flow
from oemof.solph.components import Converter

from placades.investment import _create_invest_if_wanted


class FuelCell(Converter):
    def __init__(
        self,
        label,
        input_bus,
        output_bus,
        age_installed=0,
        installed_capacity=0,
        capex_specific=1000,
        opex_specific=10,
        dispatch_costs=0.01,
        lifetime=20,
        maximum_capacity=None,
        efficiency=0.8,
        expandable=True,
        project_data=None,
    ):
        """
        Fuel cell for electricity generation.

        This class represents a fuel cell that converts hydrogen or other
        fuels into electrical energy through electrochemical processes.

        .. important ::
            The efficiency of fuel cells is typically higher than
            combustion-based generators.

        :Structure:
          *input*
            1. from_bus : H2
          *output*
            1. to_bus : Electricity

        Parameters
        ----------
        label : str
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
        efficiency : float, default=0.8
            Ratio of energy output to energy input.

        Examples
        --------
        >>> from placades import Project
        >>> from oemof.solph import Bus
        >>> h2_bus = Bus(label="hydrogen_bus")
        >>> el_bus = Bus(label="electricity_bus")
        >>> my_fuel_cell = FuelCell(
        ...     label="hydrogen_fuel_cell",
        ...     input_bus=h2_bus,
        ...     output_bus=el_bus,
        ...     age_installed=0,
        ...     installed_capacity=0,
        ...     capex_specific=1000,
        ...     opex_specific=1000,
        ...     lifetime=20,
        ...     maximum_capacity=None,
        ...     efficiency=0.7,
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

        # self.label = label
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_specific = capex_specific
        self.opex_specific = opex_specific
        self.dispatch_costs = dispatch_costs
        self.lifetime = lifetime
        self.maximum_capacity = maximum_capacity
        self.efficiency = efficiency

        super().__init__(
            label=label,
            outputs=outputs,
            inputs=inputs,
            conversion_factors={output_bus: efficiency},
        )
