# from oemof.solph.components import Converter
#
#
# class ElectricalTransformator(Converter):
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
#         Electrical transformator, e.g. for different voltage levels
#
#         This class represents an electrical conversion of any kind
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
#         >>> my_inverter = electrical_transformator(
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
