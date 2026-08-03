from oemof.eesyplan.components.buses.carrier import CarrierBus
from oemof.eesyplan.components.converters.boiler import Boiler
from oemof.eesyplan.components.converters.chp_fixed_ratio import ChpFixedRatio
from oemof.eesyplan.components.converters.chp_variable_ratio import (
    ChpVariableRatio,
)
from oemof.eesyplan.components.converters.diesel_generator import (
    DieselGenerator,
)
from oemof.eesyplan.components.converters.electrical_transformator import (
    ElectricalTransformator,
)
from oemof.eesyplan.components.converters.electrolyzer import Electrolyzer
from oemof.eesyplan.components.converters.fuel_cell import FuelCell
from oemof.eesyplan.components.converters.heat_pump import HeatPump
from oemof.eesyplan.components.demand.electricity_demand import Demand
from oemof.eesyplan.components.demand.fuel_demand import FuelDemand
from oemof.eesyplan.components.demand.heat_demand import HeatDemand
from oemof.eesyplan.components.demand.hydrogen_demand import H2Demand
from oemof.eesyplan.components.production.biogas_plant import BiogasPlant
from oemof.eesyplan.components.production.geothermal_plant import (
    GeothermalPlant,
)
from oemof.eesyplan.components.production.pv_plant import PvPlant
from oemof.eesyplan.components.production.solar_thermal_plant import (
    SolarThermalPlant,
)
from oemof.eesyplan.components.production.wind_turbine import WindTurbine
from oemof.eesyplan.components.providers.dso_electricity import DsoElectricity
from oemof.eesyplan.components.providers.dso_fuel import DsoFuel
from oemof.eesyplan.components.providers.dso_heat import DsoHeat
from oemof.eesyplan.components.providers.dso_hydrogen import DsoHydrogen
from oemof.eesyplan.components.storages.electrical_storage import (
    ElectricalStorage,
)
from oemof.eesyplan.components.storages.fuel_storage import FuelStorage
from oemof.eesyplan.components.storages.hydrogen_storage import HydrogenStorage
from oemof.eesyplan.components.storages.thermal_storage import ThermalStorage
from oemof.eesyplan.project import Project
from oemof.solph.components import Source

TYPEMAP = {
    "Battery": ElectricalStorage,
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
