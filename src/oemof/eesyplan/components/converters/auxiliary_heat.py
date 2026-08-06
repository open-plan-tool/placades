import numpy as np

from oemof.solph import Flow
from oemof.solph.components import Converter


class AuxiliaryHeat(Converter):
    def __init__(
        self,
        name,
        bus_in_heat,
        bus_in_heat_auxiliary,
        bus_out_heat,
        project_data,
        temp_in_heat,
        temp_out_heat,
        temp_low_source_component,
        installed_capacity=None,
        maximum_capacity=None,
        age_installed=0,
        capex_spec=0,
        opex_spec=0,
        variable_costs=0,
        lifetime=20,
    ):
        """
        This component can be used for heat sources whose temperature is too
        low for the target heat flow. Consequently, additional energy is
        required to heat the flow to the required temperature. By definition,
        the auxiliary flow must have at least the flow temperature.

        Parameters
        ----------
        name : string
            |name|
        bus_in_heat : Node object
            |bus_in_heat|
        bus_in_heat_auxiliary : Node object
            |bus_in_heat_auxiliary|
        bus_out_heat : Node object
            |bus_out_heat|
        project_data : Project object
            |project_data|
        temp_in_heat : float or array-like
            |temp_in_heat|
        temp_out_heat : float or array-like
            |temp_out_heat|
        temp_low_source_component : float or array-like
            |temp_low_source_component|
        age_installed : float or int, optional (default: 0)
            |age_installed|
        installed_capacity : float or None (default: None)
            |installed_capacity|
        maximum_capacity : float or None (default: None)
            |maximum_capacity|
        capex_spec : float, optional (default: 1000)
            |capex_spec|
        opex_spec : float, optional (default: 10)
            |opex_spec|
        variable_costs : float or array-like, optional (default: 0)
            |variable_costs|
        lifetime : int, optional (default: 20)
            |lifetime|

        Examples
        --------
        >>> from oemof.eesyplan import Project
        >>> from oemof.eesyplan import CarrierBus
        >>> heat_bus = CarrierBus(name="heat_bus")
        >>> heat_bus_aux = CarrierBus(name="heat_bus_auxiliary")
        >>> heat_supply = CarrierBus(name="heat_supply")
        >>> my_top_up_heater = AuxiliaryHeat(
        ...     name="top_heat",
        ...     bus_in_heat=heat_bus,
        ...     bus_in_heat_auxiliary=heat_bus_aux,
        ...     bus_out_heat=heat_supply,
        ...     project_data=Project(
        ...         name="Project_X", economic_period=20, tax=0,
        ...         discount_factor=0.01),
        ...     temp_in_low=60,
        ...     temp_out_low=20,
        ...     temp_supply=80,
        ...     )
        """
        self.name = name
        self.bus_in_heat = bus_in_heat
        self.bus_in_heat_auxiliary = bus_in_heat_auxiliary
        self.bus_out_heat = bus_out_heat
        self.project_data = project_data
        self.temp_in_heat = temp_in_heat
        self.temp_low_source_component = temp_low_source_component
        self.temp_out_heat = temp_out_heat
        self.installed_capacity = installed_capacity
        self.maximum_capacity = maximum_capacity
        self.age_installed = age_installed
        self.capex_spec = capex_spec
        self.opex_spec = opex_spec
        self.variable_costs = variable_costs
        self.lifetime = lifetime
        self.age_installed = age_installed

        nv = project_data.create_invest_if_wanted(
            capex_spec=capex_spec,
            opex_spec=opex_spec,
            lifetime=lifetime,
            installed_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
        )
        inputs = {
            bus_in_heat: Flow(),
            bus_in_heat_auxiliary: Flow(),
        }
        outputs = {
            bus_out_heat: Flow(
                nominal_capacity=nv,
                variable_costs=variable_costs,
            )
        }

        temp_out_heat = np.array(temp_out_heat)
        temp_in_heat = np.array(temp_in_heat)
        temp_low_source_component = np.array(temp_low_source_component)

        energy_top = (temp_out_heat - temp_in_heat) / (
            temp_in_heat - temp_low_source_component
        )
        energy_total = energy_top + 1

        super().__init__(
            label=name,
            inputs=inputs,
            outputs=outputs,
            conversion_factors={
                bus_in_heat: 1 / energy_total,
                bus_in_heat_auxiliary: energy_top / energy_total,
            },
        )
