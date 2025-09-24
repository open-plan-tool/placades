from placades import CHP
from placades import PV
from placades import Battery
from placades import CarrierBus
from placades import Demand
from placades import Excess
from placades import Source
from placades import WindTurbine


TYPEMAP = {
    "CHP": CHP,
    "Battery": Battery,
    "CarrierBus": CarrierBus,
    "pv_plant": PV,
    "WindTurbine": WindTurbine,
    "Demand": Demand,
    "Excess": Excess,
    "Source": Source,
}
