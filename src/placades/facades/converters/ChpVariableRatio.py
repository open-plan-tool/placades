# from oemof.solph.components import Converter
#
#
# class ChpVariableRatio(Converter):
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
#         >>> my_chp = ChpVariableRatio(
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
