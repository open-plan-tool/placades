from oemof.solph import Flow
from oemof.solph.components import ExtractionTurbineCHP


class ChpVariableRatio(ExtractionTurbineCHP):
    def __init__(
        self,
        name,
        bus_in_fuel,
        bus_out_electricity,
        bus_out_heat,
        efficiency_electricity_full_condensation,
        efficiency_electricity_chp,
        efficiency_heat_chp,
        project_data,
        age_installed=0,
        installed_capacity=None,
        maximum_capacity=None,
        capex_spec=1000,
        opex_spec=10,
        variable_costs=0,
        lifetime=20,
    ):
        """
        Combined Heat and Power (CHP) plant.

        This class represents a combined heat and power plant that
        simultaneously generates electricity and useful heat from a
        single fuel source.

        .. important ::
            CHP systems achieve higher overall efficiency by utilising
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
        efficiency_electricity_full_condensation : float
            |efficiency_electricity_full_condensation|
        efficiency_electricity_chp : float
            |efficiency_electricity_chp|
        efficiency_heat_chp : float
            |efficiency_heat_chp|
        maximum_capacity : float or None, default=None
            |maximum_capacity|
        age_installed : int, default=0
            |age_installed|
        installed_capacity : float, default=0
            |installed_capacity|
        capex_spec : float, default=1000
            |capex_spec|
        opex_spec : float, default=10
            |opex_spec|
        variable_costs : float, default=0,
            |variable_costs|
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
        >>> my_chp_fixed = ChpVariableRatio(
        ...     name="variable_ratio_chp",
        ...     bus_in_fuel=gas_bus,
        ...     bus_out_heat=heat_bus,
        ...     bus_out_electricity=el_bus,
        ...     installed_capacity=0,
        ...     efficiency_electricity_full_condensation=0.3,
        ...     efficiency_electricity_chp=0.3,
        ...     efficiency_heat_chp=0.5,
        ...     capex_spec=1500,
        ...     opex_spec=15,
        ...     lifetime=20,
        ...     project_data=Project(
        ...         name="Project_X", economic_period=20, tax=0,
        ...         discount_factor=0.01,
        ...     )
        ... )

        """

        if efficiency_electricity_chp + efficiency_heat_chp >= 1.0:
            raise ValueError("Total efficiency is above 100%.")

        nv = project_data.create_invest_if_wanted(
            capex_spec=capex_spec,
            opex_spec=opex_spec,
            lifetime=lifetime,
            installed_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
            project_data=project_data,
        )

        inputs = {bus_in_fuel: Flow()}

        outputs = {
            bus_out_electricity: Flow(
                nominal_capacity=nv,
                variable_costs=variable_costs,
            ),
            bus_out_heat: Flow(),
        }

        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_spec = capex_spec
        self.opex_spec = opex_spec
        self.variable_costs = variable_costs
        self.lifetime = lifetime

        self.maximum_capacity = maximum_capacity
        self.efficiency_electricity_chp = efficiency_electricity_chp
        self.efficiency_heat_chp = efficiency_heat_chp
        self.efficiency_electricity_full_condensation = (
            efficiency_electricity_full_condensation
        )
        super().__init__(
            label=name,
            outputs=outputs,
            inputs=inputs,
            conversion_factors={
                bus_out_electricity: efficiency_electricity_chp,
                bus_out_heat: efficiency_heat_chp,
            },
            conversion_factor_full_condensation={
                bus_out_electricity: efficiency_electricity_full_condensation
            },
        )
