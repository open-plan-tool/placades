import logging
from pathlib import Path

import oemof.solph
import pandas as pd
from oemof.solph import EnergySystem
from oemof.solph import Model
from oemof.solph import Results
from oemof.solph import buses
from oemof.solph import components
from oemof.solph import create_time_index
from oemof.solph import flows
from oemof.tools import logger

from oemof.eesyplan.postprocessing import calculate_costs_of_all_flows
from oemof.eesyplan.postprocessing import plot_all_flows_plotly
from oemof.eesyplan.postprocessing import plot_flow_cost_breakdown
from oemof.eesyplan.postprocessing import print_flow_cost_summary

DATA_PATH = Path(__file__).parent


'''This is a simple example for optimizing a single household heat and electricity supply with a PV-plant, a heat pump and a heat storage'''

def get_data_from_file_path(file_path: str):
    try:
        data = pd.read_csv(file_path)
    except FileNotFoundError:
        data = pd.read_csv(Path(DATA_PATH, file_path))
    return data


def create_energysystem():
    file_name = "singe_household_year.csv"
    data = get_data_from_file_path(file_name)

    number_of_time_steps = len(data)

    logging.info("Initialize the energy system")
    date_time_index = create_time_index(2012, number=number_of_time_steps)

    energysystem = EnergySystem(
        timeindex=date_time_index, infer_last_interval=False
    )


    bus_electricity = buses.Bus(label="electricity")
    bus_heat = buses.Bus(label="bus_heat")
    bus_heat_low = buses.Bus(label="heat_low")

    energysystem.add(bus_electricity, bus_heat, bus_heat_low)

    energysystem.add(
        components.Source(
            label="DSO_el_buy",
            outputs={bus_electricity: flows.Flow(variable_costs= 0.39)},#data["electricity_price_buy"])},
        )
    )

    energysystem.add(
        components.Sink(
            label="DSO_el_sell",
            inputs={bus_electricity: flows.Flow(
                nominal_capacity=oemof.solph.Investment(ep_costs=0, maximum=1),
                variable_costs=-0.08 #-data["electricity_price_sell"]
                )},
        )
    )

    energysystem.add(
        components.Source(
            label="PV",
            outputs={
                bus_electricity: flows.Flow(
                    max=data["PV"],
                    nominal_capacity=oemof.solph.Investment(ep_costs=1200*0.065, maximum=30),
                    variable_costs=0.001,
                )
            },
        )
    )

    energysystem.add(
        components.Sink(
            label="electricity_demand",
            inputs={
                bus_electricity: flows.Flow(
                    fix=data["electricity_demand"], nominal_capacity=1
                )
            },
        )
    )

    energysystem.add(
        components.Sink(
            label="heat_demand",
            inputs={
                bus_heat: flows.Flow(
                    fix=data["heat_demand"], nominal_capacity=1
                )
            },
        )
    )

    energysystem.add(
        components.Sink(
            label="heat_excess",
            inputs={bus_heat: flows.Flow()},
        )
    )

    energysystem.add(
        components.Source(
            label="Heat-Air",
            outputs={bus_heat_low: flows.Flow(variable_costs=0.001)},
        )
    )


    energysystem.add(
        components.Converter(
            label="HP-Air",
            inputs={bus_electricity: flows.Flow(),
                    bus_heat_low: flows.Flow(),},
            outputs={
                bus_heat: flows.Flow(
                    nominal_capacity=oemof.solph.Investment(ep_costs=800*0.096),
                    variable_costs=0.01,
                ),
            },
            conversion_factors={
                bus_electricity: 1/data["COP_AIR-HP"],
                bus_heat_low: 1-1/data["COP_AIR-HP"]
            },
        )
    )

    nominal_capacity = oemof.solph.Investment(ep_costs=10*0.065)
    heat_storage = components.GenericStorage(
        nominal_capacity=nominal_capacity,
        label="heat_storage",
        inputs={bus_heat: flows.Flow()},
        outputs={
            bus_heat: flows.Flow(
                nominal_capacity=nominal_capacity, variable_costs=0.001
            )
        },
        loss_rate=0.00,
        initial_storage_level=None,
        inflow_conversion_factor=1,
        outflow_conversion_factor=1,
    )
    energysystem.add(heat_storage)

    nominal_capacity = oemof.solph.Investment(ep_costs=200*0.096, maximum=20)
    battery_storage = components.GenericStorage(
        nominal_capacity=nominal_capacity,
        label="battery_storage",
        inputs={bus_electricity: flows.Flow()},
        outputs={
            bus_electricity: flows.Flow(
                nominal_capacity=nominal_capacity, variable_costs=0.001
            )
        },
        loss_rate=0.00,
        initial_storage_level=None,
        inflow_conversion_factor=1,
        outflow_conversion_factor=1,
    )
    energysystem.add(battery_storage)

    return energysystem


def optimize_energysystem(energysystem):
    logging.info("Optimise the energy system")

    energysystem_model = Model(energysystem)

    solver = "cbc"
    solver_verbose = False

    logger.define_logging(
        logfile="oemof_example.log",
        screen_level=logging.INFO,
        file_level=logging.INFO,
    )

    logging.info("Solve the optimization problem")
    energysystem_model.solve(
        solver=solver, solve_kwargs={"tee": solver_verbose}
    )

    logging.info("Store the energy system with the results.")

    results = Results(energysystem_model)
    print("Energy System Optimized")

    return results


def main():
    energysystem = create_energysystem()
    results = optimize_energysystem(energysystem)

    all_flow_dict = calculate_costs_of_all_flows(results)

    try:
        storage_content = results.to_df("storage_content")
    except KeyError:
        storage_content = None

    plot_all_flows_plotly(all_flow_dict, storage_content, specific=True)
    plot_all_flows_plotly(all_flow_dict, storage_content, specific=False)
    plot_flow_cost_breakdown(
        all_flow_dict,
        specific=True,
        filename="flow_cost_breakdown_specific.html",
    )
    plot_flow_cost_breakdown(
        all_flow_dict,
        specific=False,
        filename="flow_cost_breakdown_total.html",
    )

    print_flow_cost_summary(all_flow_dict)

    print(results.keys())
    print("Objective:", results["objective"])

    heat_key = next(
        f
        for f in all_flow_dict
        if f[0].label == "bus_heat" and f[1].label == "heat_demand"
    )
    heat_df = all_flow_dict[heat_key]["flow_df"]
    lcoh_heat = (
        heat_df["var_c_tot_p"].sum() + heat_df["fix_c_tot_p"].sum()
    ) / all_flow_dict[heat_key]["tot_flow"]
    print(f"LCOH heat = {lcoh_heat:.6f} EUR/kWh")

    el_key = next(
        f
        for f in all_flow_dict
        if f[0].label == "electricity" and f[1].label == "electricity_demand"
    )
    el_df = all_flow_dict[el_key]["flow_df"]
    lcoe_el = (
        el_df["var_c_tot_p"].sum() + el_df["fix_c_tot_p"].sum()
    ) / all_flow_dict[el_key]["tot_flow"]
    print(f"LCOE electricity = {lcoe_el:.6f} EUR/kWh")

    return results, all_flow_dict


if __name__ == "__main__":
    main()
