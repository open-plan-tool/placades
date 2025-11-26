# from oemof.network import Node
#
#
# class Dso(Node):
#     def __init__(
#         self,
#         name,
#         energy_price=0.3,
#         feedin_tariff=0.1,
#         peak_demand_pricing=0,
#         peak_demand_pricing_period=1,
#         renewable_share=0.44,
#         feedin_cap=None,
#     ):
#         """
#         Energy provider for electricity distribution.
#
#         This class represents a distribution system operator (DSO) that
#         provides electricity from the utility grid with pricing and
#         feedin capabilities.
#
#         .. important ::
#             The renewable share affects the overall system renewable
#             factor calculation.
#
#         :Structure:
#           *input*
#             1. from_bus : Electricity
#           *output*
#             1. to_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         energy_price : float, default=0.3
#             Price of the energy carrier sourced from the utility grid.
#         feedin_tariff : float, default=0.1
#             Price received for feeding electricity into the grid.
#         peak_demand_pricing : float, default=0
#             Grid fee to be paid based on the peak demand of a given
#             period.
#         peak_demand_pricing_period : int, default=1
#             Number of reference periods in one year for the peak
#             demand pricing.
#         renewable_share : float, default=0.44
#             Share of renewables in the generation mix of the energy
#             supplied by the DSO utility.
#         feedin_cap : float or None, default=None
#             Maximum flow for feeding electricity into the grid at any
#             given timestep.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> ebus = Bus(label="electricity_bus")
#         >>> my_dso = Dso(
#         ...     name="main_grid",
#         ...     energy_price=0.25,
#         ...     feedin_tariff=0.08,
#         ... )
#
#         """
#         self.name = name
#         self.energy_price = energy_price
#         self.feedin_tariff = feedin_tariff
#         self.peak_demand_pricing = peak_demand_pricing
#         self.peak_demand_pricing_period = peak_demand_pricing_period
#         self.renewable_share = renewable_share
#         self.feedin_cap = feedin_cap
#         super().__init__()
#
#
# class GasDso(Node):
#     def __init__(
#         self,
#         name,
#         energy_price=0.3,
#         feedin_tariff=0.1,
#         peak_demand_pricing=0,
#         peak_demand_pricing_period=1,
#         renewable_share=0.44,
#         feedin_cap=None,
#     ):
#         """
#         Energy provider for gas distribution.
#
#         This class represents a distribution system operator (DSO) that
#         provides gas from the utility grid with pricing and feedin
#         capabilities.
#
#         .. important ::
#             The renewable share affects the overall system renewable
#             factor calculation.
#
#         :Structure:
#           *input*
#             1. from_bus : Gas
#           *output*
#             1. to_bus : Gas
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         energy_price : float, default=0.3
#             Price of the energy carrier sourced from the utility grid.
#         feedin_tariff : float, default=0.1
#             Price received for feeding electricity into the grid.
#         peak_demand_pricing : float, default=0
#             Grid fee to be paid based on the peak demand of a given
#             period.
#         peak_demand_pricing_period : int, default=1
#             Number of reference periods in one year for the peak
#             demand pricing.
#         renewable_share : float, default=0.44
#             Share of renewables in the generation mix of the energy
#             supplied by the DSO utility.
#         feedin_cap : float or None, default=None
#             Maximum flow for feeding electricity into the grid at any
#             given timestep.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> gas_bus = Bus(label="gas_bus")
#         >>> my_gas_dso = GasDso(
#         ...     name="gas_grid",
#         ...     energy_price=0.05,
#         ...     feedin_tariff=0.03,
#         ... )
#
#         """
#         self.name = name
#         self.energy_price = energy_price
#         self.feedin_tariff = feedin_tariff
#         self.peak_demand_pricing = peak_demand_pricing
#         self.peak_demand_pricing_period = peak_demand_pricing_period
#         self.renewable_share = renewable_share
#         self.feedin_cap = feedin_cap
#         super().__init__()
#
#
# class Demand(Node):
#     def __init__(
#         self,
#         name,
#         input_timeseries=None,
#     ):
#         """
#         Electricity demand/consumption component.
#
#         This class represents an electricity demand that consumes
#         electrical energy according to a specified time series pattern.
#
#         :Structure:
#           *input*
#             1. from_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         input_timeseries : str or None, default=None
#             Name of the csv file containing the input generation or
#             demand timeseries.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> ebus = Bus(label="electricity_bus")
#         >>> my_demand = Demand(
#         ...     name="office_demand",
#         ...     input_timeseries="electricity_demand.csv",
#         ... )
#
#         """
#         self.name = name
#         self.input_timeseries = input_timeseries
#         super().__init__()
#
#
# class SolarInverter(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         efficiency=0.8,
#     ):
#         """
#         Solar inverter for DC to AC conversion.
#
#         This class represents a solar inverter that converts DC
#         electricity from photovoltaic panels to AC electricity for
#         grid connection or local consumption.
#
#         .. important ::
#             The efficiency parameter significantly affects the overall
#             system performance.
#
#         :Structure:
#           *input*
#             1. from_bus : Electricity
#           *output*
#             1. to_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> dc_bus = Bus(label="dc_bus")
#         >>> ac_bus = Bus(label="ac_bus")
#         >>> my_inverter = SolarInverter(
#         ...     name="pv_inverter_01",
#         ...     installed_capacity=5000,
#         ...     efficiency=0.95,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.efficiency = efficiency
#         super().__init__()
#
#
# class PvPlant(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         renewable_asset=True,
#         input_timeseries=None,
#     ):
#         """
#         Photovoltaic power plant for solar electricity generation.
#
#         This class represents a photovoltaic plant that converts solar
#         irradiation into electrical energy using photovoltaic panels.
#
#         .. important ::
#             This is a renewable energy source that contributes to the
#             renewable share of the system.
#
#         :Structure:
#           *output*
#             1. to_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         renewable_asset : bool, default=True
#             Choose if this asset should be considered as renewable.
#         input_timeseries : str or None, default=None
#             Name of the csv file containing the input generation or
#             demand timeseries.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> ebus = Bus(label="electricity_bus")
#         >>> my_pv = PvPlant(
#         ...     name="rooftop_pv",
#         ...     installed_capacity=100,
#         ...     input_timeseries="solar_irradiation.csv",
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.renewable_asset = renewable_asset
#         self.input_timeseries = input_timeseries
#         super().__init__()
#
#
# class Electrolyzer(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         efficiency=0.8,
#     ):
#         """
#         Electrolyzer for hydrogen production.
#
#         This class represents an electrolyzer that converts electrical
#         energy into hydrogen gas through electrolysis, producing both
#         hydrogen and waste heat.
#
#         .. important ::
#             The efficiency parameter determines the conversion rate
#             from electricity to hydrogen.
#
#         :Structure:
#           *input*
#             1. el_bus : Electricity
#           *output*
#             1. heat_bus : Heat
#             2. h2_bus : H2
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> el_bus = Bus(label="electricity_bus")
#         >>> h2_bus = Bus(label="hydrogen_bus")
#         >>> heat_bus = Bus(label="heat_bus")
#         >>> my_electrolyzer = Electrolyzer(
#         ...     name="hydrogen_electrolyzer",
#         ...     installed_capacity=1000,
#         ...     efficiency=0.7,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.efficiency = efficiency
#         super().__init__()
#
#
# class Capacity(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         efficiency=0.8,
#         soc_max=1,
#         soc_min=0,
#         crate=1,
#         dispatchable=True,
#         thermal_loss_rate=0,
#         fixed_thermal_losses_relative=0,
#         fixed_thermal_losses_absolute=0,
#     ):
#         """
#         Energy storage capacity component.
#
#         This class represents the storage capacity component of an
#         energy storage system with thermal losses and state of charge
#         management.
#
#         .. important ::
#             The C-rate determines the maximum charge/discharge power
#             relative to capacity.
#
#         :Structure:
#           *input*
#             1. charge : Electricity
#           *output*
#             1. discharge : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#         soc_max : float, default=1
#             The maximum permissible level of charge of the storage as
#             a factor of the nominal capacity.
#         soc_min : float, default=0
#             The minimum permissible level of charge of the storage as
#             a factor of the nominal capacity.
#         crate : float, default=1
#             Maximum permissable power at which the storage can be
#             charged or discharged relative to the nominal capacity.
#         dispatchable : bool, default=True
#             Specifies whether the storage can be dispatched.
#         thermal_loss_rate : float, default=0
#             Thermal losses of the storage per timestep.
#         fixed_thermal_losses_relative : float, default=0
#             Thermal losses of storage independent of state of charge
#             between consecutive timesteps relative to nominal capacity.
#         fixed_thermal_losses_absolute : float, default=0
#             Thermal losses of the storage independent of the state of
#             charge and independent of nominal storage capacity.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> ebus = Bus(label="electricity_bus")
#         >>> my_storage = Capacity(
#         ...     name="battery_capacity",
#         ...     installed_capacity=1000,
#         ...     soc_max=0.9,
#         ...     soc_min=0.1,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.efficiency = efficiency
#         self.soc_max = soc_max
#         self.soc_min = soc_min
#         self.crate = crate
#         self.dispatchable = dispatchable
#         self.thermal_loss_rate = thermal_loss_rate
#         self.fixed_thermal_losses_relative = fixed_thermal_losses_relative
#         self.fixed_thermal_losses_absolute = fixed_thermal_losses_absolute
#         super().__init__()
#
#
# class H2Dso(Node):
#     def __init__(
#         self,
#         name,
#         energy_price=0.3,
#         feedin_tariff=0.1,
#         peak_demand_pricing=0,
#         peak_demand_pricing_period=1,
#         renewable_share=0.44,
#         feedin_cap=None,
#     ):
#         """
#         Energy provider for hydrogen distribution.
#
#         This class represents a distribution system operator (DSO) that
#         provides hydrogen from the utility grid with pricing and feedin
#         capabilities.
#
#         .. important ::
#             The renewable share affects the overall system renewable
#             factor calculation.
#
#         :Structure:
#           *input*
#             1. from_bus : H2
#           *output*
#             1. to_bus : H2
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         energy_price : float, default=0.3
#             Price of the energy carrier sourced from the utility grid.
#         feedin_tariff : float, default=0.1
#             Price received for feeding electricity into the grid.
#         peak_demand_pricing : float, default=0
#             Grid fee to be paid based on the peak demand of a given
#             period.
#         peak_demand_pricing_period : int, default=1
#             Number of reference periods in one year for the peak
#             demand pricing.
#         renewable_share : float, default=0.44
#             Share of renewables in the generation mix of the energy
#             supplied by the DSO utility.
#         feedin_cap : float or None, default=None
#             Maximum flow for feeding electricity into the grid at any
#             given timestep.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> h2_bus = Bus(label="hydrogen_bus")
#         >>> my_h2_dso = H2Dso(
#         ...     name="hydrogen_grid",
#         ...     energy_price=8.0,
#         ...     feedin_tariff=6.0,
#         ... )
#
#         """
#         self.name = name
#         self.energy_price = energy_price
#         self.feedin_tariff = feedin_tariff
#         self.peak_demand_pricing = peak_demand_pricing
#         self.peak_demand_pricing_period = peak_demand_pricing_period
#         self.renewable_share = renewable_share
#         self.feedin_cap = feedin_cap
#         super().__init__()
#
#
# class HeatDso(Node):
#     def __init__(
#         self,
#         name,
#         energy_price=0.3,
#         feedin_tariff=0.1,
#         peak_demand_pricing=0,
#         peak_demand_pricing_period=1,
#         renewable_share=0.44,
#         feedin_cap=None,
#     ):
#         """
#         Energy provider for heat distribution.
#
#         This class represents a distribution system operator (DSO) that
#         provides heat from the utility grid with pricing and feedin
#         capabilities.
#
#         .. important ::
#             The renewable share affects the overall system renewable
#             factor calculation.
#
#         :Structure:
#           *input*
#             1. from_bus : Heat
#           *output*
#             1. to_bus : Heat
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         energy_price : float, default=0.3
#             Price of the energy carrier sourced from the utility grid.
#         feedin_tariff : float, default=0.1
#             Price received for feeding electricity into the grid.
#         peak_demand_pricing : float, default=0
#             Grid fee to be paid based on the peak demand of a given
#             period.
#         peak_demand_pricing_period : int, default=1
#             Number of reference periods in one year for the peak
#             demand pricing.
#         renewable_share : float, default=0.44
#             Share of renewables in the generation mix of the energy
#             supplied by the DSO utility.
#         feedin_cap : float or None, default=None
#             Maximum flow for feeding electricity into the grid at any
#             given timestep.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> heat_bus = Bus(label="heat_bus")
#         >>> my_heat_dso = HeatDso(
#         ...     name="heat_grid",
#         ...     energy_price=0.12,
#         ...     feedin_tariff=0.08,
#         ... )
#
#         """
#         self.name = name
#         self.energy_price = energy_price
#         self.feedin_tariff = feedin_tariff
#         self.peak_demand_pricing = peak_demand_pricing
#         self.peak_demand_pricing_period = peak_demand_pricing_period
#         self.renewable_share = renewable_share
#         self.feedin_cap = feedin_cap
#         super().__init__()
#
#
# class GasDemand(Node):
#     def __init__(
#         self,
#         name,
#         input_timeseries=None,
#     ):
#         """
#         Gas demand/consumption component.
#
#         This class represents a gas demand that consumes gas according
#         to a specified time series pattern.
#
#         :Structure:
#           *input*
#             1. from_bus : Gas
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         input_timeseries : str or None, default=None
#             Name of the csv file containing the input generation or
#             demand timeseries.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> gas_bus = Bus(label="gas_bus")
#         >>> my_gas_demand = GasDemand(
#         ...     name="industrial_gas_demand",
#         ...     input_timeseries="gas_demand.csv",
#         ... )
#
#         """
#         self.name = name
#         self.input_timeseries = input_timeseries
#         super().__init__()
#
#
# class H2Demand(Node):
#     def __init__(
#         self,
#         name,
#         input_timeseries=None,
#     ):
#         """
#         Hydrogen demand/consumption component.
#
#         This class represents a hydrogen demand that consumes hydrogen
#         according to a specified time series pattern.
#
#         :Structure:
#           *input*
#             1. from_bus : H2
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         input_timeseries : str or None, default=None
#             Name of the csv file containing the input generation or
#             demand timeseries.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> h2_bus = Bus(label="hydrogen_bus")
#         >>> my_h2_demand = H2Demand(
#         ...     name="fuel_cell_demand",
#         ...     input_timeseries="hydrogen_demand.csv",
#         ... )
#
#         """
#         self.name = name
#         self.input_timeseries = input_timeseries
#         super().__init__()
#
#
# class HeatDemand(Node):
#     def __init__(
#         self,
#         name,
#         input_timeseries=None,
#     ):
#         """
#         Heat demand/consumption component.
#
#         This class represents a heat demand that consumes thermal energy
#         according to a specified time series pattern.
#
#         :Structure:
#           *input*
#             1. from_bus : Heat
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         input_timeseries : str or None, default=None
#             Name of the csv file containing the input generation or
#             demand timeseries.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> heat_bus = Bus(label="heat_bus")
#         >>> my_heat_demand = HeatDemand(
#         ...     name="building_heating",
#         ...     input_timeseries="heat_demand.csv",
#         ... )
#
#         """
#         self.name = name
#         self.input_timeseries = input_timeseries
#         super().__init__()
#
#
# class TransformerStationIn(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         efficiency=0.8,
#     ):
#         """
#         Transformer station input component.
#
#         This class represents the input stage of a transformer station
#         that converts electrical energy from one voltage level to
#         another voltage level.
#
#         .. important ::
#             The efficiency parameter affects the conversion losses
#             during voltage transformation.
#
#         :Structure:
#           *input*
#             1. from_bus : Electricity
#           *output*
#             1. to_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> mv_bus = Bus(label="medium_voltage_bus")
#         >>> lv_bus = Bus(label="low_voltage_bus")
#         >>> my_transformer_in = TransformerStationIn(
#         ...     name="trafo_station_in_01",
#         ...     installed_capacity=500,
#         ...     efficiency=0.98,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.efficiency = efficiency
#         super().__init__()
#
#
# class TransformerStationOut(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         efficiency=0.8,
#     ):
#         """
#         Transformer station output component.
#
#         This class represents the output stage of a transformer station
#         that converts electrical energy from one voltage level to
#         another voltage level.
#
#         .. important ::
#             The efficiency parameter affects the conversion losses
#             during voltage transformation.
#
#         :Structure:
#           *input*
#             1. from_bus : Electricity
#           *output*
#             1. to_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> mv_bus = Bus(label="medium_voltage_bus")
#         >>> lv_bus = Bus(label="low_voltage_bus")
#         >>> my_transformer_out = TransformerStationOut(
#         ...     name="trafo_station_out_01",
#         ...     installed_capacity=500,
#         ...     efficiency=0.98,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.efficiency = efficiency
#         super().__init__()
#
#
# class StorageChargeControllerIn(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         efficiency=0.8,
#     ):
#         """
#         Storage charge controller input component.
#
#         This class represents the input stage of a charge controller
#         that manages the charging process of energy storage systems.
#
#         .. important ::
#             The efficiency parameter affects the energy losses during
#             the charging process.
#
#         :Structure:
#           *input*
#             1. from_bus : Electricity
#           *output*
#             1. to_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> ac_bus = Bus(label="ac_bus")
#         >>> storage_bus = Bus(label="storage_bus")
#         >>> my_charge_controller_in = StorageChargeControllerIn(
#         ...     name="charge_controller_in_01",
#         ...     installed_capacity=100,
#         ...     efficiency=0.95,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.efficiency = efficiency
#         super().__init__()
#
#
# class StorageChargeControllerOut(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         efficiency=0.8,
#     ):
#         """
#         Storage charge controller output component.
#
#         This class represents the output stage of a charge controller
#         that manages the discharging process of energy storage systems.
#
#         .. important ::
#             The efficiency parameter affects the energy losses during
#             the discharging process.
#
#         :Structure:
#           *input*
#             1. from_bus : Electricity
#           *output*
#             1. to_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> storage_bus = Bus(label="storage_bus")
#         >>> ac_bus = Bus(label="ac_bus")
#         >>> my_charge_controller_out = StorageChargeControllerOut(
#         ...     name="charge_controller_out_01",
#         ...     installed_capacity=100,
#         ...     efficiency=0.95,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.efficiency = efficiency
#         super().__init__()
#
#
# class DieselGenerator(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         efficiency=0.8,
#     ):
#         """
#         Diesel generator for electricity generation.
#
#         This class represents a diesel generator that converts diesel fuel
#         into electrical energy for backup or primary power generation.
#
#         .. important ::
#             This is a non-renewable energy source that produces emissions
#             during operation.
#
#         :Structure:
#           *input*
#             1. from_bus : Electricity
#           *output*
#             1. to_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> ebus = Bus(label="electricity_bus")
#         >>> my_diesel_gen = DieselGenerator(
#         ...     name="backup_generator",
#         ...     installed_capacity=50,
#         ...     efficiency=0.35,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.efficiency = efficiency
#         super().__init__()
#
#
# class FuelCell(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         efficiency=0.8,
#     ):
#         """
#         Fuel cell for electricity generation.
#
#         This class represents a fuel cell that converts hydrogen or other
#         fuels into electrical energy through electrochemical processes.
#
#         .. important ::
#             The efficiency of fuel cells is typically higher than
#             combustion-based generators.
#
#         :Structure:
#           *input*
#             1. from_bus : H2
#           *output*
#             1. to_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> h2_bus = Bus(label="hydrogen_bus")
#         >>> ebus = Bus(label="electricity_bus")
#         >>> my_fuel_cell = FuelCell(
#         ...     name="hydrogen_fuel_cell",
#         ...     installed_capacity=25,
#         ...     efficiency=0.6,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.efficiency = efficiency
#         super().__init__()
#
#
# class GasBoiler(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         efficiency=0.8,
#     ):
#         """
#         Gas boiler for heat generation.
#
#         This class represents a gas boiler that converts gas fuel into
#         thermal energy for heating applications.
#
#         .. important ::
#             The efficiency parameter determines the conversion rate
#             from gas to thermal output.
#
#         :Structure:
#           *input*
#             1. from_bus : Gas
#           *output*
#             1. to_bus : Heat
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> gas_bus = Bus(label="gas_bus")
#         >>> heat_bus = Bus(label="heat_bus")
#         >>> my_gas_boiler = GasBoiler(
#         ...     name="central_gas_boiler",
#         ...     installed_capacity=100,
#         ...     efficiency=0.9,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.efficiency = efficiency
#         super().__init__()
#
#
# class HeatPump(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_var=0.01,
#         opex_fix=10,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         efficiency=0.8,
#     ):
#         """
#         Heat pump for efficient heat generation.
#
#         This class represents a heat pump that extracts heat from a
#         low-temperature source and delivers it at a higher temperature
#         using electrical energy.
#
#         .. important ::
#             Heat pumps typically achieve efficiencies (COP) greater
#             than 1.0, making them very efficient heating systems.
#
#         :Structure:
#           *input*
#             1. electricity_bus : Electricity
#             2. heat_bus : Heat
#           *output*
#             1. to_bus : Heat
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> el_bus = Bus(label="electricity_bus")
#         >>> ambient_heat_bus = Bus(label="ambient_heat_bus")
#         >>> heat_bus = Bus(label="heat_bus")
#         >>> my_heat_pump = HeatPump(
#         ...     name="air_source_heat_pump",
#         ...     installed_capacity=15,
#         ...     efficiency=3.5,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_var = opex_var
#         self.opex_fix = opex_fix
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.efficiency = efficiency
#         super().__init__()
#
#
# class WindPlant(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         renewable_asset=True,
#         input_timeseries=None,
#     ):
#         """
#         Wind power plant for wind electricity generation.
#
#         This class represents a wind power plant that converts wind energy
#         into electrical energy using wind turbines.
#
#         .. important ::
#             This is a renewable energy source that contributes to the
#             renewable share of the system.
#
#         :Structure:
#           *output*
#             1. to_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         renewable_asset : bool, default=True
#             Choose if this asset should be considered as renewable.
#         input_timeseries : str or None, default=None
#             Name of the csv file containing the input generation or
#             demand timeseries.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> ebus = Bus(label="electricity_bus")
#         >>> my_wind = WindPlant(
#         ...     name="offshore_wind_farm",
#         ...     installed_capacity=2000,
#         ...     input_timeseries="wind_speed.csv",
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.renewable_asset = renewable_asset
#         self.input_timeseries = input_timeseries
#         super().__init__()
#
#
# class BiogasPlant(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         renewable_asset=True,
#         input_timeseries=None,
#     ):
#         """
#         Biogas power plant for renewable gas generation.
#
#         This class represents a biogas plant that produces renewable gas
#         from organic waste materials through anaerobic digestion.
#
#         .. important ::
#             This is a renewable energy source that produces carbon-neutral
#             gas fuel.
#
#         :Structure:
#           *output*
#             1. to_bus : Gas
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         renewable_asset : bool, default=True
#             Choose if this asset should be considered as renewable.
#         input_timeseries : str or None, default=None
#             Name of the csv file containing the input generation or
#             demand timeseries.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> gas_bus = Bus(label="gas_bus")
#         >>> my_biogas = BiogasPlant(
#         ...     name="agricultural_biogas",
#         ...     installed_capacity=500,
#         ...     input_timeseries="biogas_production.csv",
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.renewable_asset = renewable_asset
#         self.input_timeseries = input_timeseries
#         super().__init__()
#
#
# class GeothermalConversion(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         renewable_asset=True,
#         input_timeseries=None,
#     ):
#         """
#         Geothermal conversion plant for renewable heat generation.
#
#         This class represents a geothermal plant that extracts thermal
#         energy from the Earth's subsurface for heat generation.
#
#         .. important ::
#             This is a renewable energy source that provides consistent
#             baseload heat generation.
#
#         :Structure:
#           *output*
#             1. to_bus : Heat
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         renewable_asset : bool, default=True
#             Choose if this asset should be considered as renewable.
#         input_timeseries : str or None, default=None
#             Name of the csv file containing the input generation or
#             demand timeseries.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> heat_bus = Bus(label="heat_bus")
#         >>> my_geothermal = GeothermalConversion(
#         ...     name="deep_geothermal_plant",
#         ...     installed_capacity=1000,
#         ...     input_timeseries="geothermal_heat.csv",
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.renewable_asset = renewable_asset
#         self.input_timeseries = input_timeseries
#         super().__init__()
#
#
# class SolarThermalPlant(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         renewable_asset=True,
#         input_timeseries=None,
#     ):
#         """
#         Solar thermal plant for renewable heat generation.
#
#         This class represents a solar thermal plant that converts solar
#         irradiation into thermal energy using solar collectors.
#
#         .. important ::
#             This is a renewable energy source that provides heat directly
#             from solar radiation.
#
#         :Structure:
#           *output*
#             1. to_bus : Heat
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         renewable_asset : bool, default=True
#             Choose if this asset should be considered as renewable.
#         input_timeseries : str or None, default=None
#             Name of the csv file containing the input generation or
#             demand timeseries.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> heat_bus = Bus(label="heat_bus")
#         >>> my_solar_thermal = SolarThermalPlant(
#         ...     name="solar_collectors",
#         ...     installed_capacity=50,
#         ...     input_timeseries="solar_thermal.csv",
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.renewable_asset = renewable_asset
#         self.input_timeseries = input_timeseries
#         super().__init__()
#
#
# class ChargingPower(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         crate=1,
#         efficiency=0.8,
#         dispatchable=True,
#     ):
#         """
#         Charging power component for energy storage systems.
#
#         This class represents the charging power component of an energy
#         storage system that controls the charging process with specified
#         power ratings and efficiency.
#
#         .. important ::
#             The C-rate determines the maximum charge power relative to
#             storage capacity.
#
#         :Structure:
#           *input*
#             1. charge : Electricity
#           *output*
#             1. discharge : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         crate : float, default=1
#             Maximum permissable power at which the storage can be
#             charged or discharged relative to the nominal capacity.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#         dispatchable : bool, default=True
#             Specifies whether the storage can be dispatched.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> ebus = Bus(label="electricity_bus")
#         >>> my_charging_power = ChargingPower(
#         ...     name="battery_charging_power",
#         ...     installed_capacity=50,
#         ...     crate=0.5,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.crate = crate
#         self.efficiency = efficiency
#         self.dispatchable = dispatchable
#         super().__init__()
#
#
# class DischargingPower(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         crate=1,
#         efficiency=0.8,
#         dispatchable=True,
#     ):
#         """
#         Discharging power component for energy storage systems.
#
#         This class represents the discharging power component of an energy
#         storage system that controls the discharging process with specified
#         power ratings and efficiency.
#
#         .. important ::
#             The C-rate determines the maximum discharge power relative to
#             storage capacity.
#
#         :Structure:
#           *input*
#             1. charge : Electricity
#           *output*
#             1. discharge : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         crate : float, default=1
#             Maximum permissable power at which the storage can be
#             charged or discharged relative to the nominal capacity.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#         dispatchable : bool, default=True
#             Specifies whether the storage can be dispatched.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> ebus = Bus(label="electricity_bus")
#         >>> my_discharging_power = DischargingPower(
#         ...     name="battery_discharging_power",
#         ...     installed_capacity=50,
#         ...     crate=0.5,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.crate = crate
#         self.efficiency = efficiency
#         self.dispatchable = dispatchable
#         super().__init__()
#
#
# class Bess(Node):
#     def __init__(
#         self,
#         name,
#     ):
#         """
#         Battery Energy Storage System (BESS).
#
#         This class represents a complete battery energy storage system
#         for electrical energy storage and dispatch.
#
#         .. important ::
#             This is a simplified representation of a complete BESS
#             including all necessary components.
#
#         :Structure:
#           *input*
#             1. charge : Electricity
#           *output*
#             1. discharge : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> ebus = Bus(label="electricity_bus")
#         >>> my_bess = Bess(
#         ...     name="lithium_battery_system",
#         ... )
#
#         """
#         self.name = name
#         super().__init__()
#
#
# class Gess(Node):
#     def __init__(
#         self,
#         name,
#     ):
#         """
#         Gas Energy Storage System (GESS).
#
#         This class represents a gas energy storage system for storing
#         and dispatching gas energy carriers.
#
#         .. important ::
#             This system can store various types of gas including natural
#             gas and biogas.
#
#         :Structure:
#           *input*
#             1. charge : Gas
#           *output*
#             1. discharge : Gas
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> gas_bus = Bus(label="gas_bus")
#         >>> my_gess = Gess(
#         ...     name="gas_storage_tank",
#         ... )
#
#         """
#         self.name = name
#         super().__init__()
#
#
# class H2ess(Node):
#     def __init__(
#         self,
#         name,
#     ):
#         """
#         Hydrogen Energy Storage System (H2ESS).
#
#         This class represents a hydrogen energy storage system for storing
#         and dispatching hydrogen gas for various applications.
#
#         .. important ::
#             This system requires specialized storage technology for
#             hydrogen handling and safety.
#
#         :Structure:
#           *input*
#             1. charge : H2
#           *output*
#             1. discharge : H2
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> h2_bus = Bus(label="hydrogen_bus")
#         >>> my_h2ess = H2ess(
#         ...     name="hydrogen_storage_tank",
#         ... )
#
#         """
#         self.name = name
#         super().__init__()
#
#
# class Hess(Node):
#     def __init__(
#         self,
#         name,
#     ):
#         """
#         Heat Energy Storage System (HESS).
#
#         This class represents a thermal energy storage system for storing
#         and dispatching thermal energy for heating applications.
#
#         .. important ::
#             This system can store thermal energy for later use in
#             heating applications.
#
#         :Structure:
#           *input*
#             1. charge : Heat
#           *output*
#             1. discharge : Heat
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> heat_bus = Bus(label="heat_bus")
#         >>> my_hess = Hess(
#         ...     name="thermal_storage_tank",
#         ... )
#
#         """
#         self.name = name
#         super().__init__()
#
#
# class Chp(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_var=0.01,
#         opex_fix=10,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         efficiency_multiple=None,
#         efficiency=0.8,
#         thermal_loss_rate=0,
#     ):
#         """
#         Combined Heat and Power (CHP) plant.
#
#         This class represents a combined heat and power plant that
#         simultaneously generates electricity and useful heat from a
#         single fuel source.
#
#         .. important ::
#             CHP systems achieve higher overall efficiency by utilizing
#             waste heat for useful purposes.
#
#         :Structure:
#           *input*
#             1. fuel : Gas
#           *output*
#             1. heat_bus : Heat
#             2. electricity_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         efficiency_multiple : float or None, default=None
#             Multiple efficiency values for different outputs.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#         thermal_loss_rate : float, default=0
#             Thermal losses per timestep.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> gas_bus = Bus(label="gas_bus")
#         >>> heat_bus = Bus(label="heat_bus")
#         >>> el_bus = Bus(label="electricity_bus")
#         >>> my_chp = Chp(
#         ...     name="gas_chp_plant",
#         ...     installed_capacity=500,
#         ...     efficiency=0.85,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_var = opex_var
#         self.opex_fix = opex_fix
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.efficiency_multiple = efficiency_multiple
#         self.efficiency = efficiency
#         self.thermal_loss_rate = thermal_loss_rate
#         super().__init__()
#
#
# class ChpFixedRatio(Node):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_var=1000,
#         opex_fix=10,
#         lifetime=20,
#         optimize_cap=False,
#         maximum_capacity=None,
#         efficiency_multiple=None,
#         efficiency=0.8,
#     ):
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
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         maximum_capacity : float or None, default=None
#             Maximum total capacity of an asset that can be installed
#             at the project site.
#         efficiency_multiple : float or None, default=None
#             Multiple efficiency values for different outputs.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
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
#         ...     efficiency=0.8,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.maximum_capacity = maximum_capacity
#         self.efficiency_multiple = efficiency_multiple
#         self.efficiency = efficiency
#         super().__init__()
