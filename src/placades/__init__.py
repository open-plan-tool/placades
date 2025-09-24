__version__ = "0.0.0"

from placades.facades.bus import CarrierBus
from placades.facades.demand import Demand
from placades.facades.demand import Excess
from placades.facades.komponenten import CHP
from placades.facades.komponenten import Battery
from placades.facades.renewables import PV
from placades.facades.renewables import WindTurbine
from placades.facades.supply import Source

TYPEMAP = {
    "CHP": CHP,
    "Battery": Battery,
    "CarrierBus": CarrierBus,
    "PV": PV,
    "WindTurbine": WindTurbine,
    "Demand": Demand,
    "Excess": Excess,
    "Source": Source,
}


__all__ = ["CHP", "PV", "Battery", "CarrierBus", "WindTurbine"]
