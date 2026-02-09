from oemof.solph import Flow
from oemof.solph.components import ExtractionTurbineCHP

from placades.investment import _create_invest_if_wanted


class ChpVariableRatio(ExtractionTurbineCHP):
    def __init__(
        self,
        name,
        bus_in_fuel,
        bus_out_electricity,
        bus_out_heat,
        conversion_factor_to_electricity,
        conversion_factor_to_heat,
        beta,
        project_data,
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
        Combined Heat and Power (CHP) plant.

        This class represents a combined heat and power plant that
        simultaneously generates electricity and useful heat from a
        single fuel source.

        .. important ::
            CHP systems achieve higher overall efficiency by utilizing
            waste heat for useful purposes.

        :Structure:
          *input*
            1. bus_in_fuel : Gas
          *output*
            1. bus_out_heat : Heat
            2. bus_out_electricity : Electricity

        :Optimization:
          The characteristic quantity of the optimization is the
          *maximum electricity
          power-output (active power)* of the CHP given in kW

        Parameters
        ----------
        name : str
            |name|
        bus_out_electricity:  bus-object
            |bus_out_electricity|
        bus_out_heat:  bus-object
            |bus_out_heat|
        conversion_factor_to_electricity : float
            Electrical efficiency with no heat extraction
        conversion_factor_to_heat : float
            Thermal efficiency with maximal heat extraction
        beta: float
            Power loss index
        optimize_cap : bool, default=True
            |optimize_cap|
        maximum_capacity : float or None, default=None
            |maximum_capacity|
        age_installed : int, default=0
            |age_installed|
        installed_capacity : float, default=0
            |installed_capacity|
        capex_var : float, default=1000
            |capex_var|
        opex_fix : float, default=10
            |opex_fix|
        opex_var : float, default=0,
            |opex_var|
        lifetime : int, default=20
            |lifetime|
        project_data: project_data
            |project_data|



        Examples
        --------
        >>> from placades import Project
        >>> from oemof.solph import Bus
        >>> gas_bus = Bus(label="gas_bus")
        >>> heat_bus = Bus(label="heat_bus")
        >>> el_bus = Bus(label="electricity_bus")
        >>> my_chp_fixed = ChpVariableRatio(
        ...     name="variable_ratio_chp",
        ...     bus_in_fuel=gas_bus,
        ...     bus_out_heat=heat_bus,
        ...     bus_out_electricity=el_bus,
        ...     installed_capacity=300,
        ...     conversion_factor_to_electricity=0.3,
        ...     conversion_factor_to_heat=0.5,
        ...     beta=0.5,
        ...     capex_var=1500,
        ...     opex_fix=15,
        ...     lifetime=20,
        ...     optimize_cap=True,
        ...     project_data=Project(
        ...         name="Project_X", lifetime=20, tax=0,
        ...         discount_factor=0.01,
        ...     )
        ... )

        """

        if conversion_factor_to_electricity + conversion_factor_to_heat > 1.0:
            raise ValueError("Gesamtwirkungsgrad kann nicht > 100% sein")

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

        inputs = {bus_in_fuel: Flow()}

        outputs = {
            bus_out_electricity: Flow(
                nominal_capacity=nv,
                variable_costs=opex_var,
            ),
            bus_out_heat: Flow(),
        }
        efficiency_el_wo_heat_extraction = conversion_factor_to_electricity
        efficiency_th_max_heat_extraction = conversion_factor_to_heat
        efficiency_el_max_heat_extraction = (
            efficiency_el_wo_heat_extraction
            - beta * efficiency_th_max_heat_extraction
        )
        efficiency_full_condensation = {
            bus_out_electricity: efficiency_el_wo_heat_extraction
        }

        conversion_factors = {
            bus_out_electricity: efficiency_el_max_heat_extraction,
            bus_out_heat: efficiency_th_max_heat_extraction,
        }

        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_var = capex_var
        self.opex_fix = opex_fix
        self.opex_var = opex_var
        self.lifetime = lifetime
        self.optimize_cap = optimize_cap
        self.maximum_capacity = maximum_capacity
        self.conversion_factor_to_electricity = (
            conversion_factor_to_electricity
        )
        self.conversion_factor_to_heat = conversion_factor_to_heat
        self.beta = beta
        super().__init__(
            label=name,
            outputs=outputs,
            inputs=inputs,
            conversion_factors=conversion_factors,
            conversion_factor_full_condensation=efficiency_full_condensation,
        )
