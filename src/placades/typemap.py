from oemof.solph.components import Source

from placades import CHP
from placades import Battery
from placades import BiogasPlant
from placades import Boiler
from placades import CarrierBus
from placades import ChpFixedRatio
from placades import ChpVariableRatio
from placades import Demand
from placades import DieselGenerator
from placades import DsoElectricity
from placades import DsoFuel
from placades import DsoHeat
from placades import DsoHydrogen
from placades import ElectricalStorage
from placades import ElectricalTransformator
from placades import Electrolyzer
from placades import FuelCell
from placades import FuelDemand
from placades import FuelStorage
from placades import GeothermalPlant
from placades import H2Demand
from placades import HeatDemand
from placades import HeatPump
from placades import HydrogenStorage
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
    "h2_dso": DsoHydrogen,
    "heat_dso": DsoHeat,
    "gas_demand": FuelDemand,
    "h2_demand": H2Demand,
    "heat_demand": HeatDemand,
    "transformer_station_in": ElectricalTransformator,
    "transformer_station_out": ElectricalTransformator,
    "storage_charge_controller_in": ElectricalTransformator,
    "storage_charge_controller_out": ElectricalTransformator,
    "solar_inverter": ElectricalTransformator,
    "diesel_generator": DieselGenerator,
    "fuel_cell": FuelCell,
    "gas_boiler": Boiler,
    "electrolyzer": Electrolyzer,
    "heat_pump": HeatPump,
    "biogas_plant": BiogasPlant,
    "geothermal_conversion": GeothermalPlant,
    "solar_thermal_plant": SolarThermalPlant,
    "bess": ElectricalStorage,
    "gess": FuelStorage,
    "h2ess": HydrogenStorage,
    "hess": ThermalStorage,
    "chp": ChpVariableRatio,
    "chp_fixed_ratio": ChpFixedRatio,
}
