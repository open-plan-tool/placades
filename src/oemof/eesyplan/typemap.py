from oemof.solph.components import Source

from oemof.eesyplan.facades.buses.carrier import CarrierBus
from oemof.eesyplan.facades.converters.Boiler import Boiler
from oemof.eesyplan.facades.converters.ChpFixedRatio import ChpFixedRatio
from oemof.eesyplan.facades.converters.ChpVariableRatio import ChpVariableRatio
from oemof.eesyplan.facades.converters.DieselGenerator import DieselGenerator
from oemof.eesyplan.facades.converters.ElectricalTransformator import (
    ElectricalTransformator,
)
from oemof.eesyplan.facades.converters.Electrolyzer import Electrolyzer
from oemof.eesyplan.facades.converters.FuelCell import FuelCell
from oemof.eesyplan.facades.converters.HeatPump import HeatPump
from oemof.eesyplan.facades.demand.electricity_demand import ElectricityDemand
from oemof.eesyplan.facades.demand.fuel_demand import FuelDemand
from oemof.eesyplan.facades.demand.heat_demand import HeatDemand
from oemof.eesyplan.facades.demand.hydrogen_demand import H2Demand
from oemof.eesyplan.facades.production.BiogasPlant import BiogasPlant
from oemof.eesyplan.facades.production.GeothermalPlant import GeothermalPlant
from oemof.eesyplan.facades.production.PvPlant import PvPlant
from oemof.eesyplan.facades.production.SolarThermalPlant import (
    SolarThermalPlant,
)
from oemof.eesyplan.facades.production.WindTurbine import WindTurbine
from oemof.eesyplan.facades.providers.DSO_electricity import DsoElectricity
from oemof.eesyplan.facades.providers.DSO_fuel import DsoFuel
from oemof.eesyplan.facades.providers.DSO_heat import DsoHeat
from oemof.eesyplan.facades.providers.DSO_hydrogen import DsoHydrogen
from oemof.eesyplan.facades.storages.ElectricalStorage import ElectricalStorage
from oemof.eesyplan.facades.storages.FuelStorage import FuelStorage
from oemof.eesyplan.facades.storages.HydrogenStorage import HydrogenStorage
from oemof.eesyplan.facades.storages.ThermalStorage import ThermalStorage
from oemof.eesyplan.project import Project

TYPEMAP = {
    "Battery": ElectricalStorage,
    "CarrierBus": CarrierBus,
    "demand": ElectricityDemand,
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
