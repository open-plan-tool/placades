import logging
from pathlib import Path

import pandas as pd
from oemof.solph import EnergySystem
from oemof.solph import Model
from oemof.solph import Results
from oemof.solph import create_time_index
from oemof.tools.logger import define_logging

from placades import DSO
from placades import CarrierBus
from placades import Demand
from placades import Project
from placades import PvPlant
from placades import WindTurbine


def create_energy_system_sc():
    # Read data file
    project = Project(name="test", lifetime=20, tax=0, discount_factor=0)
    filename = Path(
        Path(__file__).parent, "../scripted_examples/data/input_data.csv"
    )
    data = pd.read_csv(filename)

    # ####################### initialize the energy system ####################
    datetimeindex = create_time_index(2024, number=len(data))
    energy_system = EnergySystem(
        timeindex=datetimeindex, infer_last_interval=False
    )

    # ######################### create energysystem components ################

    # carrier
    bus_elec = CarrierBus(name="electricity")

    energy_system.add(bus_elec)

    energy_system.add(
        DSO(
            name="My_DSO",
            to_bus=bus_elec,
            energy_price=0.1,
            feedin_tariff=0.04,
        )
    )

    # sources
    energy_system.add(
        WindTurbine(
            name="wind",
            to_bus=bus_elec,
            input_timeseries=data["wind"],
            installed_capacity=6.63,
            project_data=project,
            optimize_cap=False,
        )
    )

    energy_system.add(
        PvPlant(
            name="pv",
            to_bus=bus_elec,
            project_data=project,
            installed_capacity=5.0,
            input_timeseries=data["pv"],
            optimize_cap=False,
        )
    )

    # demands (electricity/heat)
    energy_system.add(
        Demand(
            name="demand_el",
            from_bus=bus_elec,
            input_timeseries=data["demand_el"],
        )
    )

    # energy_system.add(
    #     Battery(
    #         label="battery",
    #         bus_electricity=bus_elec,
    #         storage_capacity=500,
    #     )
    # )
    return energy_system


def main():
    solver = "cbc"

    # ################################ optimization ###########################
    energy_system = create_energy_system_sc()
    # create optimization model based on energy_system
    logging.info("Create model")
    optimization_model = Model(energysystem=energy_system)

    # solve problem
    logging.info("Solve model")
    optimization_model.solve(
        solver=solver, solve_kwargs={"tee": True, "keepfiles": False}
    )
    results = Results(optimization_model)
    rdf = results.to_df("flow")

    for n, m in [(0, 1), (1, 0)]:
        rdf.rename(
            columns={
                c[n]: c[n].label[-1]
                for c in rdf.columns
                if isinstance(c[n].label, tuple)
                and not isinstance(c[m].label, tuple)
            },
            level=n,
            inplace=True,
        )
    elec_in = rdf[[c for c in rdf.columns if c[0] == "electricity"]]
    elec_out = rdf[[c for c in rdf.columns if c[1] == "electricity"]]
    print(elec_in.sum())
    print(elec_out.sum())
    print("*****************")
    print("Input:", round(elec_in.sum().sum()))
    print("Output:", round(elec_out.sum().sum()))


if __name__ == "__main__":
    main()
