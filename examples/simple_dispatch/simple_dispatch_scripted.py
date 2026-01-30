from pathlib import Path

import pandas as pd
from oemof.solph import EnergySystem
from oemof.solph import create_time_index

from placades import CarrierBus
from placades import Demand
from placades import DsoElectricity
from placades import ElectricalStorage
from placades import Project
from placades import PvPlant
from placades import WindTurbine

DATA_PATH = Path("data")

DATA_FILES = {
    "pv": Path("pv_profile.csv"),
    "demand_heat": Path("heat_demand.csv"),
    "wind": Path("wind_profile.csv"),
    "demand_elec": Path("electricity_demand.csv"),
}


def create_energy_system_sc():
    # Read data file
    project = Project(name="test", lifetime=20, tax=0, discount_factor=0)

    data = {}
    for key, fn in DATA_FILES.items():
        path = Path(DATA_PATH, fn)
        data[key] = pd.read_csv(path, header=None).squeeze()

    # ####################### initialize the energy system ####################
    datetimeindex = create_time_index(2024, number=8760)
    energy_system = EnergySystem(
        timeindex=datetimeindex, infer_last_interval=False
    )

    # ######################### create energysystem components ################

    # carrier
    bus_elec = CarrierBus(name="electricity")

    energy_system.add(bus_elec)

    energy_system.add(
        DsoElectricity(
            name="My_DSO",
            bus_electricity=bus_elec,
            energy_price=0.1,
            feedin_tariff=0.04,
        )
    )

    # sources
    energy_system.add(
        WindTurbine(
            name="wind",
            bus_out_electricity=bus_elec,
            input_timeseries=data["wind"],
            installed_capacity=6.63,
            project_data=project,
            optimize_cap=False,
        )
    )

    energy_system.add(
        PvPlant(
            name="pv",
            bus_out_electricity=bus_elec,
            project_data=project,
            installed_capacity=5.0,
            input_timeseries=data["pv"],
            optimize_cap=False,
        )
    )

    energy_system.add(
        ElectricalStorage(
            name="Batterie",
            bus_electricity=bus_elec,
            age_installed=0,
            installed_capacity=1000,
            capex_var=3,
            opex_fix=5,
            lifetime=10,
            optimize_cap=False,
            soc_max=1,
            soc_min=0,
            crate=1,
            efficiency=0.99,
            project_data=project,
            self_discharge=0.0001,
        )
    )

    # demands (electricity/heat)
    energy_system.add(
        Demand(
            name="demand_el",
            bus_in_electricity=bus_elec,
            input_timeseries=data["demand_elec"],
        )
    )
    return energy_system
