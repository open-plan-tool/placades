import logging
from pathlib import Path

import pandas as pd
from oemof.solph import EnergySystem
from oemof.solph import Flow
from oemof.solph import Model
from oemof.solph import Results
from oemof.solph import create_time_index
from oemof.solph.components import Source
from oemof.tools.logger import define_logging

from placades import CarrierBus
from placades import Demand
from placades import Excess
from placades import Project
from placades import PvPlant
from placades import WindTurbine


def main():
    # Read data file
    project = Project(name="test", lifetime=20, tax=0, discount_factor=0)
    define_logging()
    filename = Path(Path(__file__).parent, "input_data.csv")
    data = pd.read_csv(filename)

    solver = "cbc"

    # ####################### initialize the energy system ####################
    datetimeindex = create_time_index(2024, number=len(data))
    energy_system = EnergySystem(
        timeindex=datetimeindex, infer_last_interval=False
    )

    # ######################### create energysystem components ################

    # carrier
    bus_gas = CarrierBus(label="gas")
    bus_elec = CarrierBus(label="electricity")
    # bus_heat = CarrierBus(label="heat")

    energy_system.add(bus_gas, bus_elec)

    # an excess and a shortage variable can help to avoid infeasible problems
    energy_system.add(Excess(label="excess_el", bus=bus_elec))

    energy_system.add(
        Source(
            label="shortage_el", outputs={bus_elec: Flow(variable_costs=9999)}
        )
    )

    # sources
    energy_system.add(
        WindTurbine(
            label="wind",
            bus_out_electricity=bus_elec,
            wind_profile=data["wind"],
            installed_capacity=66.3,
            project_data=project,
            expandable=False,
        )
    )

    energy_system.add(
        PvPlant(
            "pv",
            bus_elec,
            installed_capacity=50,
            pv_production_timeseries=data["pv"],
            expandable=False,
        )
    )

    # demands (electricity/heat)
    energy_system.add(
        Demand(label="demand_el", bus=bus_elec, profile=data["demand_el"] * 10)
    )

    # energy_system.add(
    #     Battery(
    #         label="battery",
    #         bus_electricity=bus_elec,
    #         storage_capacity=500,
    #     )
    # )
    # ################################ optimization ###########################
    # create optimization model based on energy_system
    logging.info("Create model")
    optimization_model = Model(energysystem=energy_system)

    # solve problem
    logging.info("Solve model")
    optimization_model.solve(
        solver=solver, solve_kwargs={"tee": True, "keepfiles": False}
    )
    results = Results(optimization_model)
    print(results.to_df("flow").sum())


if __name__ == "__main__":
    main()
