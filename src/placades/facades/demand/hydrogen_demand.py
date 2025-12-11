# from oemof.solph import Flow
# from oemof.solph.components import Sink
#
#
# class H2Demand(Sink):
#     """
#     Hydrogen demand/consumption component.
#
#     This class represents a hydrogen demand that consumes hydrogen
#     according to a specified time series pattern.
#
#     :Structure:
#       *input*
#         1. from_bus : H2
#
#     Parameters
#     ----------
#     name : str
#         Name of the asset.
#     input_timeseries : str or None, default=None
#         Name of the csv file containing the input generation or
#         demand timeseries.
#
#     Examples
#     --------
#     >>> from oemof.solph import Bus
#     >>> h2_bus = Bus(label="hydrogen_bus")
#     >>> my_h2_demand = H2Demand(
#     ...     name="fuel_cell_demand",
#     ...     bus=h2_bus,
#     ...     input_timeseries="hydrogen_demand.csv",
#     ... )
#
#     """
#
#     def __init__(self, name, bus, input_timeseries):
#         self.profile = input_timeseries
#         self.name = name
#         super().__init__(
#             label=name,
#             inputs={
#                 bus: Flow(
#                     fix=input_timeseries,
#                     nominal_capacity=1,
#                 )
#             },
#         )
