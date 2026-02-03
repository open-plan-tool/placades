from oemof.solph import Flow
from oemof.solph.components import Converter

from placades.investment import _create_invest_if_wanted


class ChpFixedRatio(Converter):
    def __init__(
        self,
        name,
        bus_in_fuel,
        bus_out_electricity,
        bus_out_heat,
        conversion_factor_to_electricity,
        conversion_factor_to_heat,
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
        conversion_factor_to_electricity : float
            |conversion_factor_to_electricity|
        conversion_factor_to_heat : float
            |conversion_factor_to_heat|
        expandable : bool, default=True
            |expandable|
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
        >>> from oemof.solph import Bus
        >>> gas_bus = Bus(label="gas_bus")
        >>> heat_bus = Bus(label="heat_bus")
        >>> el_bus = Bus(label="electricity_bus")
        >>> my_chp_fixed = ChpFixedRatio(
        ...     name="fixed_ratio_chp",
        ...     installed_capacity=300,
        ...     conversion_factor_to_electricity=0.3,
        ...     conversion_factor_to_heat=0.5,
        ...     capex_var=1500,
        ...     opex_fix=15,
        ...     lifetime=20,
        ...     optimize_cap=True,
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
            bus_out_electricity: conversion_factor_to_electricity,
            bus_out_heat: conversion_factor_to_heat,
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
        super().__init__(
            label=name,
            outputs=outputs,
            inputs=inputs,
            conversion_factors=conversion_factors,
        )
