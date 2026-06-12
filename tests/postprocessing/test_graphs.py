import json
import warnings
from pathlib import Path

import pandas as pd

from oemof.datapackage import datapackage  # noqa
from oemof.eesyplan import CarrierBus
from oemof.eesyplan import Demand
from oemof.eesyplan import DsoElectricity
from oemof.eesyplan import ElectricalStorage
from oemof.eesyplan import EnergySystem
from oemof.eesyplan import Project
from oemof.eesyplan import PvPlant
from oemof.eesyplan import WindTurbine
from oemof.eesyplan import optimise
from oemof.eesyplan.datapackage import energy_system as es
from oemof.eesyplan.postprocessing.graphs import capacities_graph
from oemof.eesyplan.postprocessing.graphs import sankey
from oemof.tools.debugging import ExperimentalFeatureWarning

DATA_PATH = Path("../test_data", "simple_script_data")

DATA_FILES = {
    "pv": Path("pv_profile.csv"),
    "demand_heat": Path("heat_demand.csv"),
    "wind": Path("wind_profile.csv"),
    "demand_elec": Path("electricity_demand.csv"),
}


def simple_script(pv_installed_cap=1.0, optimize_battery=False):
    # Read data file
    data = {}
    for key, fn in DATA_FILES.items():
        path = Path(Path(__file__).parent, DATA_PATH, fn)
        data[key] = pd.read_csv(path, header=None).squeeze()

    project = Project(name="test", lifetime=20, tax=0, discount_factor=0)

    # ####################### initialize the energy system ####################
    energy_system = EnergySystem(2023, number=10)

    # ######################### create energysystem components ################

    # carrier
    bus_elec = CarrierBus(name="electricity")

    energy_system.add(bus_elec)

    energy_system.add(
        DsoElectricity(
            name="My_DSO",
            bus_electricity=bus_elec,
            energy_price=5,
            feedin_tariff=0.04,
        )
    )

    # sources
    energy_system.add(
        WindTurbine(
            name="wind",
            bus_out_electricity=bus_elec,
            input_timeseries=data["wind"],
            installed_capacity=0.25,
            project_data=project,
            optimize_cap=True,
        )
    )

    energy_system.add(
        PvPlant(
            name="pv",
            bus_out_electricity=bus_elec,
            project_data=project,
            capex_var=0.01,
            installed_capacity=pv_installed_cap,
            input_timeseries=data["pv"],
            optimize_cap=True,
        )
    )

    energy_system.add(
        ElectricalStorage(
            name="Batterie",
            bus_in_electricity=bus_elec,
            age_installed=0,
            installed_capacity=10,
            capex_var=3.0,
            opex_fix=5.0,
            opex_var=0.0,
            lifetime=10.0,
            optimize_cap=optimize_battery,
            soc_max=1,
            soc_min=0,
            crate=1.0,
            efficiency=0.99,
            project_data=project,
            self_discharge=0.000,
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
    return optimise(energy_system), energy_system


def test_graph_capacities():
    res, esys = simple_script()

    capacities_graph(res["invest"], esys)


warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def test_sankey_diagram():
    path = Path(Path(__file__).parent, "../test_data", "openPlan_package")
    energy_system = es.create_energy_system_from_dp(path)
    results = optimise(energy_system)

    fig, _ = sankey(results["flow"], es=energy_system)

    with Path(
        Path(__file__).parent, "../test_data", "sankey_dict.json"
    ).open() as fp:
        saved_fig = json.load(fp)

    assert fig.to_dict() == saved_fig
