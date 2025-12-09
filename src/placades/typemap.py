from oemof.solph.components import Source

from placades import CHP
from placades import Battery
from placades import CarrierBus
from placades import Demand
from placades import Excess
from placades import Project
from placades import PvPlant
from placades import WindTurbine

# Imported the list from assettypes_list.csv von https://github.com/open-plan-tool/gui/tree/main/app/static
TYPEMAP = {
    "CHP": CHP,
    "Battery": Battery,
    "CarrierBus": CarrierBus,
    "Demand": Demand,
    "Excess": Excess,
    "Source": Source,
    "project": Project,
    "pv_plant": PvPlant,
    "wind_plant": WindTurbine,
    "dso": None,
    "gas_dso": None,
    "h2_dso": None,
    "heat_dso": None,
    "demand": None,
    "gas_demand": None,
    "h2_demand": None,
    "heat_demand": None,
    "transformer_station_in": None,
    "transformer_station_out": None,
    "storage_charge_controller_in": None,
    "storage_charge_controller_out": None,
    "solar_inverter": None,
    "diesel_generator": None,
    "fuel_cell": None,
    "gas_boiler": None,
    "electrolyzer": None,
    "heat_pump": None,
    "biogas_plant": None,
    "geothermal_conversion": None,
    "solar_thermal_plant": None,
    "charging_power": None,
    "discharging_power": None,
    "capacity": None,
    "bess": None,
    "gess": None,
    "h2ess": None,
    "hess": None,
    "chp": None,
    "chp_fixed_ratio": None,
}
