from placades import CHP
from placades import PvPlant
from placades import Battery
from placades import CarrierBus
from placades import Demand
from placades import Excess
from placades import Source
from placades import WindTurbine
from placades import Project


TYPEMAP = {
    "CHP": CHP,
    "Battery": Battery,
    "CarrierBus": CarrierBus,
    "pv_plant": PvPlant,
    "WindTurbine": WindTurbine,
    "Demand": Demand,
    "Excess": Excess,
    "Source": Source,
    "project": Project
}
