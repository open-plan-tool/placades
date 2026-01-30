# from oemof.solph.components import Converter
# from oemof.solph import Flow
#
# from placades.investment import _create_invest_if_wanted
#
# class ChpFixedRatio(Converter):
#     def __init__(
#         self,
#         label,
#         project_data,
#         bus_in_fuel,
#         bus_out_electricity,
#         bus_out_heat,
#         conversion_factor_to_electricity,
#         conversion_factor_to_heat,
#         expandable=True,
#         maximum_capacity=None,
#         capex_specific=1000,
#         opex_specific=1000,
#         variable_costs=0,
#         lifetime=20,
#         installed_capacity=0,
#         age_installed=0,
#
#     ):
#
#         """
#         Combined Heat and Power plant with fixed heat-to-power ratio.
#
#         This class represents a CHP plant that operates with a fixed
#         ratio between heat and electricity generation, providing less
#         operational flexibility but simpler control.
#
#         .. important ::
#             The fixed ratio constraint limits operational flexibility
#             but ensures consistent heat-to-power ratios.
#
#         :Structure:
#           *input*
#             1. fuel : Gas
#           *output*
#             1. heat_bus : Heat
#             2. electricity_bus : Electricity
#
#         :Optimization:
#           The characteristic quantity of the optimization is the
#           *maximum electricity
#           power-output (active power)* of the CHP given in kW
#
#         Parameters
#         ----------
#         label : str
#             |label|
#         project_data: project_data
#             |project_data|
#         bus_out_electricity:  bus-object
#             |bus_out_electricity|
#         bus_out_heat:  bus-object
#             |bus_out_heat|
#         conversion_factor_to_electricity : float
#             |conversion_factor_to_electricity|
#         conversion_factor_to_heat : float
#             |conversion_factor_to_heat|
#         expandable : bool, default=True
#             |expandable|
#         maximum_capacity : float or None, default=None
#             |maximum_capacity|
#         age_installed : int, default=0
#             |age_installed|
#         installed_capacity : float, default=0
#             |installed_capacity|
#         capex_specific : float, default=1000
#             |capex_specific|
#         opex_specific : float, default=10
#             |opex_specific|
#         variable_costs : float, default=0,
#             |variable_costs|
#         lifetime : int, default=20
#             |lifetime|
#
#
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> gas_bus = Bus(label="gas_bus")
#         >>> heat_bus = Bus(label="heat_bus")
#         >>> el_bus = Bus(label="electricity_bus")
#         >>> my_chp_fixed = ChpFixedRatio(
#         ...     name="fixed_ratio_chp",
#         ...     installed_capacity=300,
#         ...     conversion_factor_to_electricity=0.3,
#         ...     conversion_factor_to_heat=0.5,
#         ...     capex=1500,
#         ...     opex=15,
#         ...     lifetime=20,
#         ...     optimize_cap=True,
#         ... )
#
#         """
#
#         nv = _create_invest_if_wanted(
#             optimise_cap=expandable,
#             capex_specific=capex_specific,
#             opex_specific=opex_specific,
#             lifetime=lifetime,
#             age_installed=age_installed,
#             existing_capacity=installed_capacity,
#             project_data=project_data,
#         )
#
#         inputs = {bus_in_fuel: Flow()}
#
#         outputs = {
#             bus_out_electricity: Flow(
#                 nominal_capacity=nv,
#                 variable_costs=variable_costs,
#             ),
#             bus_out_heat: Flow()
#         }
#
#         conversion_factors = {
#             bus_out_electricity: conversion_factor_to_electricity,
#             bus_out_heat: conversion_factor_to_heat
#         }
#
#
#         self.label = label
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_specific = capex_specific
#         self.opex_specific = opex_specific
#         self.variable_costs = variable_costs
#         self.lifetime = lifetime
#         self.expandable = expandable
#         self.maximum_capacity = maximum_capacity
#         self.conversion_factor_to_electricity = (
#             conversion_factor_to_electricity)
#         self.conversion_factor_to_heat = conversion_factor_to_heat
#         super().__init__(
#             label=label,
#             outputs=outputs,
#             inputs=inputs,
#             conversion_factors=conversion_factors,
#         )
