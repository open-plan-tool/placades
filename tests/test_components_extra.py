import numpy as np

from oemof.eesyplan import Project
from oemof.eesyplan.components.buses.carrier import CarrierBus
from oemof.eesyplan.components.compansation.excess import Excess
from oemof.eesyplan.components.compansation.shortage import Shortage
from oemof.eesyplan.components.converters.Boiler import Boiler
from oemof.eesyplan.components.converters.DieselGenerator import (
    DieselGenerator,
)
from oemof.eesyplan.components.converters.ElectricalTransformator import (
    ElectricalTransformator,
)
from oemof.eesyplan.components.converters.Electrolyzer import Electrolyzer
from oemof.eesyplan.components.converters.FuelCell import FuelCell
from oemof.eesyplan.components.converters.HeatPump import HeatPump
from oemof.eesyplan.components.demand.fuel_demand import FuelDemand
from oemof.eesyplan.components.demand.heat_demand import HeatDemand
from oemof.eesyplan.components.demand.hydrogen_demand import H2Demand
from oemof.eesyplan.components.production.BiogasPlant import BiogasPlant
from oemof.eesyplan.components.production.GeothermalPlant import (
    GeothermalPlant,
)
from oemof.eesyplan.components.production.SolarThermalPlant import (
    SolarThermalPlant,
)
from oemof.eesyplan.components.providers.DSO_fuel import DsoFuel
from oemof.eesyplan.components.providers.DSO_heat import DsoHeat
from oemof.eesyplan.components.providers.DSO_hydrogen import DsoHydrogen
from oemof.eesyplan.components.storages.FuelStorage import FuelStorage
from oemof.eesyplan.components.storages.HydrogenStorage import HydrogenStorage
from oemof.eesyplan.components.storages.ThermalStorage import ThermalStorage
from oemof.solph import Bus


def _project():
    return Project(
        name="test_project", lifetime=20, tax=0, discount_factor=0.01
    )


def _timeseries(n=24):
    return np.ones(n)


# --- Compensation components ---


def test_excess():
    bus = CarrierBus(name="el_bus")
    ex = Excess("my_excess", bus, 999)
    assert str(ex.label) == "my_excess"


def test_shortage():
    bus = CarrierBus(name="el_bus")
    sh = Shortage("my_shortage", bus, 999)
    assert str(sh.label) == "my_shortage"


# --- Demand components ---


def test_fuel_demand():
    bus = CarrierBus(name="fuel_bus")
    ts = _timeseries()
    d = FuelDemand("fuel_demand", bus, ts)
    assert d.name == "fuel_demand"
    assert d.profile is ts


def test_heat_demand():
    bus = CarrierBus(name="heat_bus")
    ts = _timeseries()
    d = HeatDemand("heat_demand", bus, ts)
    assert d.name == "heat_demand"
    assert d.profile is ts


def test_h2_demand():
    bus = CarrierBus(name="h2_bus")
    ts = _timeseries()
    d = H2Demand("h2_demand", bus, ts)
    assert d.name == "h2_demand"
    assert d.profile is ts


# --- Converters ---


def test_boiler():
    fuel_bus = Bus(label="fuel_bus")
    heat_bus = Bus(label="heat_bus")
    p = _project()
    b = Boiler(
        name="boiler",
        bus_in_fuel=fuel_bus,
        bus_out_heat=heat_bus,
        project_data=p,
    )
    assert b.name == "boiler"
    assert b.efficiency == 0.8


def test_boiler_dispatch():
    fuel_bus = Bus(label="fuel_bus")
    heat_bus = Bus(label="heat_bus")
    p = _project()
    b = Boiler(
        name="boiler",
        bus_in_fuel=fuel_bus,
        bus_out_heat=heat_bus,
        project_data=p,
        optimize_cap=False,
        installed_capacity=100,
        age_installed=0,
    )
    assert b.installed_capacity == 100


def test_diesel_generator():
    fuel_bus = Bus(label="fuel_bus")
    el_bus = Bus(label="el_bus")
    p = _project()
    g = DieselGenerator(
        name="diesel",
        bus_in_fuel=fuel_bus,
        bus_out_electricity=el_bus,
        project_data=p,
    )
    assert g.name == "diesel"
    assert g.efficiency == 0.3


def test_diesel_generator_dispatch():
    fuel_bus = Bus(label="fuel_bus")
    el_bus = Bus(label="el_bus")
    p = _project()
    g = DieselGenerator(
        name="diesel",
        bus_in_fuel=fuel_bus,
        bus_out_electricity=el_bus,
        project_data=p,
        optimize_cap=False,
        installed_capacity=50,
        age_installed=0,
    )
    assert g.installed_capacity == 50


def test_electrical_transformator():
    in_bus = Bus(label="in_bus")
    out_bus = Bus(label="out_bus")
    p = _project()
    t = ElectricalTransformator(
        name="transformer",
        bus_in_electricity=in_bus,
        bus_out_electricity=out_bus,
        project_data=p,
    )
    assert t.name == "transformer"
    assert t.efficiency == 0.3


def test_electrical_transformator_dispatch():
    in_bus = Bus(label="in_bus")
    out_bus = Bus(label="out_bus")
    p = _project()
    t = ElectricalTransformator(
        name="transformer",
        bus_in_electricity=in_bus,
        bus_out_electricity=out_bus,
        project_data=p,
        optimize_cap=False,
        installed_capacity=200,
        age_installed=0,
    )
    assert t.installed_capacity == 200


def test_electrolyzer_with_heat():
    el_bus = Bus(label="el_bus")
    h2_bus = Bus(label="h2_bus")
    heat_bus = Bus(label="heat_bus")
    p = _project()
    e = Electrolyzer(
        name="electrolyzer",
        bus_in_electricity=el_bus,
        bus_out_h2=h2_bus,
        project_data=p,
        bus_out_heat=heat_bus,
    )
    assert e.name == "electrolyzer"
    assert e.efficiency_heat == 0.6


def test_electrolyzer_without_heat():
    el_bus = Bus(label="el_bus")
    h2_bus = Bus(label="h2_bus")
    p = _project()
    e = Electrolyzer(
        name="electrolyzer",
        bus_in_electricity=el_bus,
        bus_out_h2=h2_bus,
        project_data=p,
        bus_out_heat=None,
    )
    assert e.name == "electrolyzer"


def test_electrolyzer_dispatch():
    el_bus = Bus(label="el_bus")
    h2_bus = Bus(label="h2_bus")
    heat_bus = Bus(label="heat_bus")
    p = _project()
    e = Electrolyzer(
        name="electrolyzer",
        bus_in_electricity=el_bus,
        bus_out_h2=h2_bus,
        project_data=p,
        bus_out_heat=heat_bus,
        optimize_cap=False,
        installed_capacity=100,
        age_installed=0,
    )
    assert e.installed_capacity == 100


def test_fuel_cell():
    h2_bus = Bus(label="h2_bus")
    el_bus = Bus(label="el_bus")
    p = _project()
    fc = FuelCell(
        name="fuel_cell",
        bus_in_h2=h2_bus,
        bus_out_electricity=el_bus,
        project_data=p,
    )
    assert fc.name == "fuel_cell"
    assert fc.efficiency == 0.8


def test_fuel_cell_dispatch():
    h2_bus = Bus(label="h2_bus")
    el_bus = Bus(label="el_bus")
    p = _project()
    fc = FuelCell(
        name="fuel_cell",
        bus_in_h2=h2_bus,
        bus_out_electricity=el_bus,
        project_data=p,
        optimize_cap=False,
        installed_capacity=50,
        age_installed=0,
    )
    assert fc.installed_capacity == 50


def test_heat_pump_with_list_cop():
    heat_in = Bus(label="heat_in")
    el_in = Bus(label="el_in")
    heat_out = Bus(label="heat_out")
    p = _project()
    hp = HeatPump(
        name="heat_pump",
        bus_in_heat=heat_in,
        bus_in_electricity=el_in,
        bus_out_heat=heat_out,
        project_data=p,
        cop=[3.0, 3.5, 4.0],
    )
    assert hp.name == "heat_pump"


def test_heat_pump_dispatch():
    heat_in = Bus(label="heat_in")
    el_in = Bus(label="el_in")
    heat_out = Bus(label="heat_out")
    p = _project()
    hp = HeatPump(
        name="heat_pump",
        bus_in_heat=heat_in,
        bus_in_electricity=el_in,
        bus_out_heat=heat_out,
        project_data=p,
        optimize_cap=False,
        installed_capacity=100,
        age_installed=0,
    )
    assert hp.installed_capacity == 100


# --- Production sources ---


def test_biogas_plant():
    bus = Bus(label="fuel_bus")
    ts = _timeseries()
    p = _project()
    bp = BiogasPlant(
        project_data=p,
        bus_out_fuel=bus,
        input_timeseries=ts,
        name="biogas",
    )
    assert bp.name == "biogas"


def test_biogas_plant_dispatch():
    bus = Bus(label="fuel_bus")
    ts = _timeseries()
    p = _project()
    bp = BiogasPlant(
        project_data=p,
        bus_out_fuel=bus,
        input_timeseries=ts,
        name="biogas",
        optimize_cap=False,
        installed_capacity=50,
        age_installed=0,
    )
    assert bp.installed_capacity == 50


def test_geothermal_plant():
    bus = Bus(label="heat_bus")
    ts = _timeseries()
    p = _project()
    gp = GeothermalPlant(
        project_data=p,
        bus_out_heat=bus,
        input_timeseries=ts,
        name="geothermal",
    )
    assert gp.name == "geothermal"


def test_geothermal_plant_dispatch():
    bus = Bus(label="heat_bus")
    ts = _timeseries()
    p = _project()
    gp = GeothermalPlant(
        project_data=p,
        bus_out_heat=bus,
        input_timeseries=ts,
        name="geothermal",
        optimize_cap=False,
        installed_capacity=30,
        age_installed=0,
    )
    assert gp.installed_capacity == 30


def test_solar_thermal_plant():
    bus = Bus(label="heat_bus")
    ts = _timeseries()
    p = _project()
    st = SolarThermalPlant(
        project_data=p,
        bus_out_heat=bus,
        input_timeseries=ts,
        name="solar_thermal",
    )
    assert st.name == "solar_thermal"


def test_solar_thermal_plant_dispatch():
    bus = Bus(label="heat_bus")
    ts = _timeseries()
    p = _project()
    st = SolarThermalPlant(
        project_data=p,
        bus_out_heat=bus,
        input_timeseries=ts,
        name="solar_thermal",
        optimize_cap=False,
        installed_capacity=40,
        age_installed=0,
    )
    assert st.installed_capacity == 40


# --- Providers ---


def test_dso_fuel():
    bus = CarrierBus(name="fuel_bus")
    dso = DsoFuel(name="dso_fuel", bus_fuel=bus)
    assert dso.name == "dso_fuel"


def test_dso_heat():
    bus = CarrierBus(name="heat_bus")
    dso = DsoHeat(name="dso_heat", bus_heat=bus)
    assert dso.name == "dso_heat"


def test_dso_hydrogen():
    bus = CarrierBus(name="h2_bus")
    dso = DsoHydrogen(name="dso_h2", bus_h2=bus)
    assert dso.name == "dso_h2"


# --- Storages ---


def test_fuel_storage_optimise():
    bus = CarrierBus(name="fuel_bus")
    p = _project()
    fs = FuelStorage(
        name="fuel_storage",
        bus_in_fuel=bus,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=True,
        soc_max=1,
        soc_min=0,
        crate=1,
        efficiency=0.99,
        project_data=p,
    )
    assert str(fs.label) == "fuel_storage"


def test_fuel_storage_dispatch():
    bus = CarrierBus(name="fuel_bus")
    p = _project()
    fs = FuelStorage(
        name="fuel_storage",
        bus_in_fuel=bus,
        age_installed=0,
        installed_capacity=100,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=False,
        soc_max=1,
        soc_min=0,
        crate=1,
        efficiency=0.99,
        project_data=p,
    )
    assert str(fs.label) == "fuel_storage"


def test_fuel_storage_with_output_bus():
    bus_in = CarrierBus(name="fuel_bus_in")
    bus_out = CarrierBus(name="fuel_bus_out")
    p = _project()
    fs = FuelStorage(
        name="fuel_storage",
        bus_in_fuel=bus_in,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=True,
        soc_max=1,
        soc_min=0,
        crate=1,
        efficiency=0.99,
        project_data=p,
        bus_out_fuel=bus_out,
    )
    assert str(fs.label) == "fuel_storage"


def test_hydrogen_storage_optimise():
    bus = CarrierBus(name="h2_bus")
    p = _project()
    hs = HydrogenStorage(
        name="h2_storage",
        bus_in_h2=bus,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=True,
        soc_max=1,
        soc_min=0,
        crate=1,
        efficiency=0.99,
        project_data=p,
    )
    assert str(hs.label) == "h2_storage"


def test_hydrogen_storage_dispatch():
    bus = CarrierBus(name="h2_bus")
    p = _project()
    hs = HydrogenStorage(
        name="h2_storage",
        bus_in_h2=bus,
        age_installed=0,
        installed_capacity=100,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=False,
        soc_max=1,
        soc_min=0,
        crate=1,
        efficiency=0.99,
        project_data=p,
    )
    assert str(hs.label) == "h2_storage"


def test_hydrogen_storage_with_output_bus():
    bus_in = CarrierBus(name="h2_bus_in")
    bus_out = CarrierBus(name="h2_bus_out")
    p = _project()
    hs = HydrogenStorage(
        name="h2_storage",
        bus_in_h2=bus_in,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=True,
        soc_max=1,
        soc_min=0,
        crate=1,
        efficiency=0.99,
        project_data=p,
        bus_out_h2=bus_out,
    )
    assert str(hs.label) == "h2_storage"


def test_thermal_storage_optimise():
    bus = CarrierBus(name="heat_bus")
    p = _project()
    ts = ThermalStorage(
        name="thermal_storage",
        bus_in_heat=bus,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=True,
        soc_max=1,
        soc_min=0,
        crate=1,
        efficiency=0.99,
        fixed_thermal_losses_relative=0.0,
        fixed_thermal_losses_absolute=0.0,
        project_data=p,
    )
    assert str(ts.label) == "thermal_storage"


def test_thermal_storage_dispatch():
    bus = CarrierBus(name="heat_bus")
    p = _project()
    ts = ThermalStorage(
        name="thermal_storage",
        bus_in_heat=bus,
        age_installed=0,
        installed_capacity=100,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=False,
        soc_max=1,
        soc_min=0,
        crate=1,
        efficiency=0.99,
        fixed_thermal_losses_relative=0.01,
        fixed_thermal_losses_absolute=0.0,
        project_data=p,
    )
    assert str(ts.label) == "thermal_storage"


def test_thermal_storage_with_output_bus():
    bus_in = CarrierBus(name="heat_bus_in")
    bus_out = CarrierBus(name="heat_bus_out")
    p = _project()
    ts = ThermalStorage(
        name="thermal_storage",
        bus_in_heat=bus_in,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=True,
        soc_max=1,
        soc_min=0,
        crate=1,
        efficiency=0.99,
        fixed_thermal_losses_relative=0.0,
        fixed_thermal_losses_absolute=0.0,
        project_data=p,
        bus_out_heat=bus_out,
    )
    assert str(ts.label) == "thermal_storage"
