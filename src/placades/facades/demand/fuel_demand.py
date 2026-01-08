# from oemof.solph import Flow
# from oemof.solph.components import Sink
#
#
# class GasDemand(Sink):
#     """
#     Gas demand/consumption component.
#
#     This class represents a gas demand that consumes gas according
#     to a specified time series pattern.
#
#     :Structure:
#       *input*
#         1. from_bus : Gas
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
#     >>> gas_bus = Bus(label="gas_bus")
#     >>> my_gas_demand = GasDemand(
#     ...     name="industrial_gas_demand",
#     ...     bus=gas_bus,
#     ...     input_timeseries="gas_demand.csv",
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
