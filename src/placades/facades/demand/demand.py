from oemof.network import Node
from oemof.network import Sink
from oemof.solph.flows import Flow


class Demand(Sink):
    """
    Short description

    Long description about the facade and how to use it.

    .. important ::
        Some important information about this facade.

    :Structure:
      *output*
        1. bus_electricity : electricity
        2. bus_heat : heat
      *input*
        1. bus_gas : gas
        2. bus_coal : coal

    Parameters
    ----------
    label : str or tuple
        Unique identifier of the instance.
    bus : oemof.solph.Bus or placade.CarrierBus
        Valid network bus with the carrier: electricity
    profile : iterable
        Absolute demand time series.

    Examples
    --------
    >>> from oemof.solph import Bus
    >>> hbus = Bus(label="my_heat_bus")
    >>> demand = Demand(
    ...     label="heat1",
    ...     bus=hbus,
    ...     profile=[123, 200, 85]
    ... )
    >>> demand.inputs[hbus].fix
    array([123, 200,  85])
    >>> isinstance(list(demand.inputs.keys())[0], Bus)
    True
    >>> demand.profile
    [123, 200, 85]
    >>> demand.label
    'heat1'
    """

    def __init__(self, label, bus, profile):
        self.profile = profile  # ToDo: Soll das zusätzlich hier hin? -> yes
        super().__init__(
            label=label,
            inputs={
                bus: Flow(
                    fix=profile,
                    nominal_capacity=1,
                )
            },
        )

        # add a description on how the GUI looks?


#
# from demandlib import bdew
# def create_heat_demand(timeframe,outdoor_temperature,profile_type,annual_heat_demand,building_year,wind_class=0):
#
#     match wind_class:
#         case "not windy":
#             wind_class=0
#         case "windy":
#             wind_class=1
#
#     if profile_type != 'residential':
#         building_class = 0
#     else:
#         match building_year:
#             case y if y <= 1918:
#                 building_class = 1
#             case y if 1919 <= y <= 1948:
#                 building_class = 2
#             case y if 1949 <= y <= 1957:
#                 building_class = 3
#             case y if 1958 <= y <= 1968:
#                 building_class = 4
#             case y if 1969 <= y <= 1978:
#                 building_class = 5
#             case y if 1979 <= y <= 1983:
#                 building_class = 6
#             case y if 1984 <= y <= 1994:
#                 building_class = 7
#             case y if 1995 <= y <= 1999:
#                 building_class = 8
#             case y if 2000 <= y <= 2006:
#                 building_class = 9
#             case y if 2007 <= y <= 2010:
#                 building_class = 10
#             case y if y >= 2011:
#                 building_class = 11
#
#     match profile_type:
#         case 'single-family house':
#             profile_type = 'EFH'
#         case 'apartment building':
#             profile_type = 'MFH'
#         case 'Commerce/Services general':
#             profile_type = 'GHD'
#         case 'restaurants':
#             profile_type = 'GGA'
#         case 'retail and wholesale':
#             profile_type = 'GBH'
#         case 'metal and automotive':
#             profile_type = 'GMK'
#         case 'household-like business enterprises':
#             profile_type = 'GMF'
#         case 'accommodation':
#             profile_type = 'GBH'
#         case 'Local authorities, credit institutions and insurance companies':
#             profile_type = 'GKO'
#         case 'other operational services':
#             profile_type = 'GBD'
#         case 'laundries, dry cleaning':
#             profile_type = 'GWA'
#         case 'horticulture':
#             profile_type = 'GGB'
#         case 'bakery':
#             profile_type = 'GBA'
#         case 'paper and printing':
#             profile_type = 'GPD'
#
#     holidays = { #ToDo: Create table based on location of project
#         datetime.date(2010, 5, 24): "Whit Monday",
#         datetime.date(2010, 4, 5): "Easter Monday",
#         datetime.date(2010, 5, 13): "Ascension Thursday",
#         datetime.date(2010, 1, 1): "New year",
#         datetime.date(2010, 10, 3): "Day of German Unity",
#         datetime.date(2010, 12, 25): "Christmas Day",
#         datetime.date(2010, 5, 1): "Labour Day",
#         datetime.date(2010, 4, 2): "Good Friday",
#         datetime.date(2010, 12, 26): "Second Christmas Day",
#     }
#
#     demand_profile = bdew.HeatBuilding(
#         timeframe.index,
#         holidays=holidays,
#         temperature=outdoor_temperature,
#         shlp_type=profile_type,
#         building_class=building_class,
#         wind_class=wind_class,
#         annual_heat_demand=annual_heat_demand,
#         name="",
#     ).get_bdew_profile()
#
#     return demand_profile


class Excess(Node):
    """
    Excess Node.
    """

    def __init__(self, label, bus, cost=0):
        super().__init__(
            label=label,
            inputs={bus: Flow(variable_costs=cost)},
        )
