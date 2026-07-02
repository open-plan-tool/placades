import numpy as np

from oemof.eesyplan.investment import _create_invest_if_wanted
from oemof.solph import Flow
from oemof.solph.components import Converter


class AuxiliaryHeatSplit(Converter):
    def __init__(
        self,
        name,
        bus_in_heat,
        bus_in_heat_auxiliary,
        bus_out_heat,
        project_data,
        temp_in_low,
        temp_out_low,
        temp_supply,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=False,
        maximum_capacity=float("+inf"),
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
        efficiency : float, optional (default: 0.3)
            |efficiency|
        age_installed : float or int, optional (default: 0)
            |age_installed|
        installed_capacity : float, optional (default: 0)
            |installed_capacity|
        capex_var : float, optional (default: 1000)
            |capex_var|
        capex_fix : float, optional (default: 0)
            |capex_fix|
        opex_fix : float, optional (default: 10)
            |opex_fix|
        opex_var : float, optional (default: 0)
            |opex_var|
        lifetime : int, optional (default: 20)
            |lifetime|
        optimize_cap : bool, optional (default: True)
            |optimize_cap|
        maximum_capacity : float, optional (default: float("+inf"))
            |maximum_capacity|

        Examples
        --------
        >>> from oemof.eesyplan import Project
        >>> from oemof.eesyplan import CarrierBus
        >>> heat_bus = CarrierBus(name="heat_bus")
        >>> heat_bus_aux = CarrierBus(name="heat_bus_auxiliary")
        >>> heat_supply = CarrierBus(name="heat_supply")
        >>> my_top_up_heater = AuxiliaryHeatSplit(
        ...     name="top_heat",
        ...     bus_in_heat=heat_bus,
        ...     bus_in_heat_auxiliary=heat_bus_aux,
        ...     bus_out_heat=heat_supply,
        ...     installed_capacity=5,
        ...     project_data=Project(
        ...         name="Project_X", lifetime=20, tax=0,
        ...         discount_factor=0.01),
        ...     temp_in_low=60,
        ...     temp_out_low=20,
        ...     temp_supply=80,
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
        inputs = {
            bus_in_heat: Flow(),
            bus_in_heat_auxiliary: Flow(),
        }
        outputs = {
            bus_out_heat: Flow(
                nominal_capacity=nv,
                variable_costs=opex_var,
            )
        }

        temp_supply = np.array(temp_supply)
        temp_out_low = np.array(temp_out_low)
        temp_in_low = np.array(temp_in_low)

        energy_top = (temp_supply - temp_out_low) / (
            temp_out_low - temp_in_low
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
