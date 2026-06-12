from oemof.solph import Flow
from oemof.solph.components import Converter

from oemof.eesyplan.investment import _create_invest_if_wanted


class ChpFixedRatio(Converter):
    def __init__(
        self,
        name,
        bus_in_fuel,
        bus_out_electricity,
        bus_out_heat,
        efficiency_electricity_chp,
        efficiency_heat_chp,
        project_data,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=True,
        maximum_capacity=float("+inf"),
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
        efficiency_electricity_chp : float
            conversion_factor_to_electricity
        efficiency_heat_chp : float
            conversion_factor_to_heat
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
        >>> from oemof.eesyplan import Project
        >>> from oemof.eesyplan import CarrierBus
        >>> gas_bus = CarrierBus(name="gas_bus")
        >>> heat_bus = CarrierBus(name="heat_bus")
        >>> el_bus = CarrierBus(name="electricity_bus")
        >>> my_chp_fixed = ChpFixedRatio(
        ...     name="fixed_ratio_chp",
        ...     bus_in_fuel=gas_bus,
        ...     bus_out_heat=heat_bus,
        ...     bus_out_electricity=el_bus,
        ...     installed_capacity=300,
        ...     conversion_factor_to_electricity=0.3,
        ...     conversion_factor_to_heat=0.5,
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

        conversion_factors = {
            bus_out_electricity: efficiency_electricity_chp,
            bus_out_heat: efficiency_heat_chp,
        }

        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_var = capex_var
        self.opex_fix = opex_fix
        self.opex_var = opex_var
        self.lifetime = lifetime
        self.optimize_cap = optimize_cap
        self.maximum_capacity = maximum_capacity
        self.efficiency_electricity_chp = efficiency_electricity_chp
        self.efficiency_heat_chp = efficiency_heat_chp
        super().__init__(
            label=name,
            outputs=outputs,
            inputs=inputs,
            conversion_factors=conversion_factors,
        )
