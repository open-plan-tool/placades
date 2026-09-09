from pathlib import Path

import pandas as pd

from oemof.eesyplan import CarrierBus
from oemof.eesyplan import Demand
from oemof.eesyplan import EnergySystem
from oemof.eesyplan import Excess
from oemof.eesyplan import Project
from oemof.eesyplan import WindTurbine
from oemof.eesyplan import optimise
from oemof.tools.logger import define_logging

DATA_PATH = Path("data")

DATA_FILES = {
    "pv": Path("pv_profile.csv"),
    "demand_heat": Path("heat_demand.csv"),
    "wind": Path("wind_profile.csv"),
    "demand_elec": Path("electricity_demand.csv"),
}


def investment_calculation():
    # Read data file
    data = {}
    for key, fn in DATA_FILES.items():
        path = Path(DATA_PATH, fn)
        data[key] = pd.read_csv(path, header=None).squeeze()

    project = Project(name="test", lifetime=20, tax=0, discount_factor=0.10)

    # ####################### initialize the energy system ####################
    energy_system = EnergySystem(2023, number=365)

    # ######################### create energysystem components ################

    # carrier
    bus_elec = CarrierBus(name="electricity")

    energy_system.add(bus_elec)

    energy_system.add(
        WindTurbine(
            name="wind",
            bus_out_electricity=bus_elec,
            project_data=project,
            input_timeseries=[1] * 365,
            optimize_cap=True,
            capex_var=200,
            opex_fix=10,
            lifetime=10,
            installed_capacity=0,
            age_installed=0,
        )
    )

    # demands (electricity/heat)
    energy_system.add(
        Demand(
            name="demand_el",
            bus_in_electricity=bus_elec,
            input_timeseries=[10] * 365,
        )
    )

    energy_system.add(
        Excess(
            name="excess",
            bus_in=bus_elec,
            cost=0,
        )
    )
    return optimise(energy_system), energy_system


if __name__ == "__main__":
    define_logging()
    res, es = investment_calculation()
    # print(type(res))
    # print(res)
    # print(type(res["flow"]))
    #
    # print(nodes_io(res["flow"]).sum().sort_index())
    #
    # fig, sankey_data = sankey(res["flow"], es=es)
    # print ("here")
    # result = sankey(res["flow"], es=es)

    # print(type(result))
    # print(result)

    # fig.show()

    # print (res.keys())
    print(res["investment_costs"])
    print(res["objective"])


