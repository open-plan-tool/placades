from oemof.solph import Flow
from oemof.solph.components import Converter

from placades.investment import _create_invest_if_wanted


class Electrolyzer(Converter):
    def __init__(
        self,
        name,
        bus_in_electricity,
        bus_out_h2,
        bus_out_heat,
        project_data,
        efficiency=0.3,
        efficiency_heat=0.6,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        capex_fix=0,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=True,
        maximum_capacity=float("+inf"),
    ):
        """
        Electrolyzer for hydrogen production.

        This class represents an electrolyzer that converts electrical
        energy into hydrogen gas through electrolysis, producing both
        hydrogen and waste heat.

        .. important ::
            The efficiency parameter determines the conversion rate
            from electricity to hydrogen.

        :Structure:
          *input*
            1. el_bus : Electricity
          *output*
            1. heat_bus : Heat
            2. h2_bus : H2
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
        efficiency_heat : float, default=0.6
            TODO find a good attribute name and description

        Examples
        --------

        >>> from placades import Project
        >>> from oemof.solph import Bus
        >>> el_bus_in = Bus(label="el_bus_in")
        >>> heat_bus_out = Bus(label="heat_bus_out")
        >>> h2_bus_out = Bus(label="h2_bus_out")
        >>> my_electrolyzer = Electrolyzer(
        ...     name="Electrolyzer",
        ...     bus_in_electricity=el_bus_in,
        ...     bus_out_heat=heat_bus_out,
        ...     bus_out_h2=h2_bus_out,
        ...     age_installed=0,
        ...     installed_capacity=0,
        ...     capex_var=1000,
        ...     opex_fix=1000,
        ...     lifetime=20,
        ...     maximum_capacity=None,
        ...     efficiency=0.9,
        ...     efficiency_heat=0.1,
        ...     opex_var=0,
        ...     optimize_cap=True,
        ...     project_data=Project(
        ...         name="Project_X", lifetime=20, tax=0,
        ...         discount_factor=0.01),
        ...     )

        """
        nv = _create_invest_if_wanted(
            optimise_cap=optimize_cap,
            capex_var=capex_var,
            opex_fix=opex_fix,
            lifetime=lifetime,
            age_installed=age_installed,
            existing_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
            project_data=project_data,
        )

        inputs = {bus_in_electricity: Flow()}

        outputs = {
            bus_out_heat: Flow(
                nominal_capacity=nv,
                variable_costs=opex_var,
            ),
            bus_out_h2: Flow(
                nominal_capacity=nv,
                variable_costs=opex_var,
            ),
        }

        self.name = name
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_fix = capex_fix
        self.capex_var = capex_var
        self.opex_fix = opex_fix
        self.opex_var = opex_var
        self.lifetime = lifetime
        self.maximum_capacity = maximum_capacity
        self.efficiency = efficiency
        self.efficiency_heat = efficiency_heat
        super().__init__(
            label=name,
            outputs=outputs,
            inputs=inputs,
            conversion_factors={
                bus_out_h2: efficiency,
                bus_out_heat: efficiency_heat,
            },
        )
