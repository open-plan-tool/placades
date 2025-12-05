# from oemof.solph.components import Converter
#
#
# class Electrolyzer(Converter):
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
