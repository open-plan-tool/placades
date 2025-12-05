# from oemof.network import Source
#
#
# class GeothermalPlant(Source):
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
#         Geothermal plant for renewable heat generation.
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
