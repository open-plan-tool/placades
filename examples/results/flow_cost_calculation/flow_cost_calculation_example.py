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
from oemof.eesyplan.postprocessing import sankey_for_flow_costs
from oemof.eesyplan.postprocessing import sankey_from_results

DATA_PATH = Path(__file__).parent


def get_data_from_file_path(file_path: str):
    try:
        data = pd.read_csv(file_path)
    except FileNotFoundError:
        data = pd.read_csv(Path(DATA_PATH, file_path))
    return data


def create_energysystem():
    file_name = "time_series_month.csv"
    data = get_data_from_file_path(file_name)

    number_of_time_steps = len(data)

    logging.info("Initialize the energy system")
    date_time_index = create_time_index(2012, number=number_of_time_steps)

    energysystem = EnergySystem(
        timeindex=date_time_index, infer_last_interval=False
    )

    bus_gas = buses.Bus(label="natural_gas")
    bus_electricity = buses.Bus(label="electricity")
    bus_heat = buses.Bus(label="bus_heat")

    energysystem.add(bus_gas, bus_electricity, bus_heat)

    energysystem.add(
        components.Source(
            label="rgas",
            outputs={bus_gas: flows.Flow(variable_costs=0.1)},
        )
    )

    energysystem.add(
        components.Source(
            label="wind",
            outputs={
                bus_electricity: flows.Flow(
                    max=data["wind"],
                    nominal_capacity=oemof.solph.Investment(
                        ep_costs=1100 / 12
                    ),
                    variable_costs=0.001,
                )
            },
        )
    )

    energysystem.add(
        components.Source(
            label="pv",
            outputs={
                bus_electricity: flows.Flow(
                    max=data["pv"],
                    nominal_capacity=oemof.solph.Investment(ep_costs=800 / 12),
                    variable_costs=0.001,
                )
            },
        )
    )

    energysystem.add(
        components.Sink(
            label="demand_el",
            inputs={
                bus_electricity: flows.Flow(
                    fix=data["demand_el"], nominal_capacity=1
                )
            },
        )
    )

    energysystem.add(
        components.Sink(
            label="demand_heat",
            inputs={
                bus_heat: flows.Flow(
                    fix=data["demand_heat"], nominal_capacity=0.1
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
        components.Sink(
            label="sold",
            inputs={bus_electricity: flows.Flow(variable_costs=-0.1)},
        )
    )

    energysystem.add(
        components.Converter(
            label="pp_gas",
            inputs={bus_gas: flows.Flow()},
            outputs={
                bus_electricity: flows.Flow(
                    nominal_capacity=oemof.solph.Investment(ep_costs=600 / 12),
                    variable_costs=0.01,
                ),
                bus_heat: flows.Flow(),
            },
            conversion_factors={bus_electricity: 0.3, bus_heat: 0.5},
        )
    )

    energysystem.add(
        components.Converter(
            label="backwards",
            inputs={bus_heat: flows.Flow()},
            outputs={
                bus_gas: flows.Flow(
                    nominal_capacity=oemof.solph.Investment(
                        ep_costs=60 / 12, maximum=100
                    ),
                    variable_costs=-10,
                )
            },
            conversion_factors={bus_gas: 1},
        )
    )

    nominal_capacity = oemof.solph.Investment(ep_costs=1 / 12, maximum=100)
    gas_storage = components.GenericStorage(
        nominal_capacity=nominal_capacity,
        label="gas_storage",
        inputs={bus_gas: flows.Flow()},
        outputs={
            bus_gas: flows.Flow(
                nominal_capacity=nominal_capacity, variable_costs=-1
            )
        },
        loss_rate=0.00,
        initial_storage_level=None,
        inflow_conversion_factor=1,
        outflow_conversion_factor=1,
    )
    energysystem.add(gas_storage)

    nominal_capacity = oemof.solph.Investment(ep_costs=10 / 12)
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

    nominal_capacity = oemof.solph.Investment(ep_costs=0.1 / 12)
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
        outflow_conversion_factor=0.9,
    )
    energysystem.add(heat_storage)

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
        if f[0].label == "bus_heat" and f[1].label == "demand_heat"
    )
    heat_df = all_flow_dict[heat_key]["flow_df"]
    lcoh_heat = (
        heat_df["var_c_tot_p"].sum() + heat_df["fix_c_tot_p"].sum()
    ) / all_flow_dict[heat_key]["tot_flow"]
    print(f"LCOH heat = {lcoh_heat:.6f} EUR/kWh")

    el_key = next(
        f
        for f in all_flow_dict
        if f[0].label == "electricity" and f[1].label == "demand_el"
    )
    el_df = all_flow_dict[el_key]["flow_df"]
    lcoe_el = (
        el_df["var_c_tot_p"].sum() + el_df["fix_c_tot_p"].sum()
    ) / all_flow_dict[el_key]["tot_flow"]
    print(f"LCOE electricity = {lcoe_el:.6f} EUR/kWh")

    fig, _ = sankey_from_results(results)
    fig.write_html("sankey.html")
    print("Sankey saved to sankey.html")
    fig.show()

    fig_cost, links_cost_df = sankey_for_flow_costs(results)
    fig_cost.write_html("cost_sankey.html")
    fig_cost.show()
    print("Cost Sankey saved to cost_sankey.html")
    print(
        f"Cost-sankey links: {len(links_cost_df)}, "
        f"total costs: {links_cost_df['value'].clip(lower=0).sum():,.2f} EUR, "
        f"revenues: {links_cost_df['value'].clip(upper=0).sum():,.2f} EUR"
    )



    return results, all_flow_dict


if __name__ == "__main__":
    main()
