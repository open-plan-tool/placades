from oemof.solph.components import Source

from placades import CHP
from placades import Battery
from placades import Boiler
from placades import CarrierBus
from placades import ChpFixedRatio
from placades import Demand
from placades import DsoElectricity
from placades import DsoFuel
from placades import DsoHeat
from placades import ElectricalStorage
from placades import HeatDemand
from placades import Project
from placades import PvPlant
from placades import SolarThermalPlant
from placades import ThermalStorage
from placades import WindTurbine

TYPEMAP = {
    "CHP": CHP,
    "Battery": Battery,
    "CarrierBus": CarrierBus,
    "demand": Demand,
    "Source": Source,
    "project": Project,
    "pv_plant": PvPlant,
    "wind_plant": WindTurbine,
    "dso_electricity": DsoElectricity,
    "dso": DsoElectricity,
    "gas_dso": DsoFuel,
    "h2_dso": None,
    "heat_dso": DsoHeat,
    "gas_demand": None,
    "h2_demand": None,
    "heat_demand": HeatDemand,
    "transformer_station_in": None,
    "transformer_station_out": None,
    "storage_charge_controller_in": None,
    "storage_charge_controller_out": None,
    "solar_inverter": None,
    "diesel_generator": None,
    "fuel_cell": None,
    "gas_boiler": Boiler,
    "electrolyzer": None,
    "heat_pump": None,
    "biogas_plant": None,
    "geothermal_conversion": None,
    "solar_thermal_plant": SolarThermalPlant,
    "bess": ElectricalStorage,
    "gess": None,
    "h2ess": None,
    "hess": ThermalStorage,
    "chp": None,
    "chp_fixed_ratio": ChpFixedRatio,
}
