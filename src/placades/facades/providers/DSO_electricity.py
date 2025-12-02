# from oemof.network import Node
#
# class Dso(Node):    #todo : How to actually implement a subnetwork?
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
