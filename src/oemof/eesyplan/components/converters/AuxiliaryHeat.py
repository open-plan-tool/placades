import numpy as np
from oemof.solph import Flow
from oemof.solph.components import Converter

from oemof.eesyplan.investment import _create_invest_if_wanted


class AuxiliaryHeatSplit(Converter):
    def __init__(
        self,
        name,
        node_in_heat,
        node_in_heat_auxiliary,
        node_out_heat,
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
        optimize_cap=True,
        maximum_capacity=float("+inf"),
    ):
        """
                self,
        name,
        bus_in_fuel,
        bus_out_electricity,
        project_data,
        efficiency=0.3,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        capex_fix=0,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=True,
        maximum_capacity=float("+inf"),
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
            node_in_heat: Flow(),
            node_in_heat_auxiliary: Flow(),
        }
        outputs = {
            node_out_heat: Flow(
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
                node_in_heat: 1 / energy_total,
                node_in_heat_auxiliary: energy_top / energy_total,
            },
        )
