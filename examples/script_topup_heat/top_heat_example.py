import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from oemof.eesyplan import CarrierBus
from oemof.eesyplan import Demand
from oemof.eesyplan import EnergySystem
from oemof.eesyplan import HeatPump
from oemof.eesyplan import Project
from oemof.eesyplan import ThermalStorage
from oemof.eesyplan import optimise
from oemof.eesyplan.components.converters.AuxiliaryHeat import (
    AuxiliaryHeatSplit,
)
from oemof.eesyplan.components.production.commodity import Commodity
from oemof.eesyplan.components.transport.heat import HeatingNetwork
from oemof.eesyplan.components.transport.heat import HeatingPipe
from oemof.eesyplan.importer.cop import calculate_cop_simple
from oemof.eesyplan.postprocessing.balance import nodes_io
from oemof.eesyplan.postprocessing.graphs import sankey
from oemof.network import graph
from oemof.solph import Flow
from oemof.solph.components import Sink
from oemof.solph.components import Source
from oemof.tools.logger import define_logging


def simple_script():
    # Read data file
    heat = pd.Series([9, 9, 3, 3, 7, 7, 2, 2, 5, 5, 4, 4, 8, 8, 2, 2])

    project = Project(name="test", lifetime=20, tax=0, discount_factor=0)

    # ####################### initialize the energy system ####################
    energy_system = EnergySystem(2023, number=len(heat))

    # ######################### create energysystem components ################

    bus_electricity = CarrierBus(
        name="electricity bus", carrier="electricity", balanced=True
    )
    low_temperature_bus = CarrierBus(
        name="low_temperature_bus", carrier="heat"
    )

    energy_system.add(bus_electricity, low_temperature_bus)

    energy_system.add(
        Commodity(
            name="electricity",
            variable_cost=2,
            bus_out=bus_electricity,
        )
    )

    ht_east = HeatingNetwork(
        name="HeatingNetwork - East",
    )

    ht_west = HeatingNetwork(name="HeatingNetwork - West")
    energy_system.add(ht_east, ht_west)

    # sources
    energy_system.add(
        Source(label="Source", outputs={ht_west: Flow(variable_costs=999)})
    )

    energy_system.add(
        Source(
            label="Hochtemperatur Abwärme",
            outputs={
                ht_west: Flow(
                    nominal_capacity=2,
                    fix=heat,
                    variable_costs=1,
                )
            },
        )
    )

    energy_system.add(
        Sink(label="Sink", inputs={ht_west: Flow(variable_costs=999)})
    )

    energy_system.add(
        HeatingPipe(
            name="HeatPipe w-e",
            bus_1_heat=ht_west,
            bus_2_heat=ht_east,
            return_pipe=False,
            absolute_losses=0,
        )
    )

    energy_system.add(
        HeatingPipe(
            name="HeatPipe e-w",
            bus_1_heat=ht_east,
            bus_2_heat=ht_west,
            return_pipe=False,
            absolute_losses=0,
        )
    )

    my_storage = ThermalStorage(
        name="HeatStorage",
        bus_in_heat=ht_east,
        bus_out_heat=low_temperature_bus,
        age_installed=0,
        installed_capacity=1000,
        capex_var=3.0,
        opex_fix=0.0,
        opex_var=0.0,
        lifetime=30.0,
        optimize_cap=False,
        soc_max=1,
        soc_min=0,
        theoretical_time_charge=1.0,
        theoretical_time_discharge=1.0,
        efficiency_charge=1,
        efficiency_discharge=1,
        project_data=project,
        thermal_losses_relative=0.000,
        thermal_losses_absolute=0,
        thermal_losses_absolute_investment=0,
    )
    energy_system.add(my_storage)

    t_in = [10] * len(heat)
    t_out = [80] * len(heat)
    t_supply = [100] * len(heat)

    topheatbus = CarrierBus(name="TopHeatBus", carrier="heat_supply")
    energy_system.add(topheatbus)

    energy_system.add(
        Source(
            label="Irgendein Wärmeerzeuger mit hoher Temperatur",
            outputs={
                topheatbus: Flow(
                    nominal_capacity=2,
                    variable_costs=1,
                )
            },
        )
    )

    heat_pump = HeatPump(
        name="HeatPump",
        project_data=project,
        installed_capacity=5,
        bus_out_heat=topheatbus,
        bus_in_electricity=bus_electricity,
        cop=calculate_cop_simple(
            temperature_source=20,
            temperature_supply=t_supply,
            quality_factor=0.55,
        ),
    )

    energy_system.add(heat_pump)
    print(heat_pump.cop)

    energy_system.add(
        AuxiliaryHeatSplit(
            name="AuxiliaryHeatSplit",
            installed_capacity=10000,
            bus_in_heat=low_temperature_bus,
            bus_in_heat_auxiliary=topheatbus,
            bus_out_heat=ht_east,
            project_data=project,
            temp_in_low=t_in,
            temp_out_low=t_out,
            temp_supply=t_supply,
        )
    )

    # demands (electricity/heat)
    energy_system.add(
        Demand(
            name="demand_heat_west",
            bus_in=ht_west,
            input_timeseries=np.roll(heat, 2),
        )
    )
    energy_system.add(
        Demand(
            name="demand_heat_east",
            bus_in=ht_east,
            input_timeseries=np.roll(heat, 2),
        )
    )

    graph.create_nx_graph(energy_system, filename="testgraph.graphml")
    return optimise(energy_system), energy_system


def hide_and_rename(df, depth=0):
    filtered = df.loc[
        :,
        [
            column
            for column in df.columns
            if any(
                level.depth == depth
                for level in (
                    column if isinstance(column, tuple) else (column,)
                )
            )
        ],
    ]

    for n in range(df.columns.nlevels):
        filtered.rename(
            columns={
                obj: obj.parent
                for c in filtered.columns
                for obj in [(c if isinstance(c, tuple) else (c,))[n]]
                if obj.parent is not None
            },
            level=n,
            inplace=True,
        )
    return filtered


if __name__ == "__main__":
    define_logging()
    res, es = simple_script()
    flows = hide_and_rename(res["flow"])
    print(nodes_io(flows).sum().sort_index())
    print(res["storage_losses"].sum())
    print(res["storage_content"].plot())
    print(flows.sum())
    print(flows)
    flows.loc[:, (flows.sum() > 0.1)].plot()
    fig = sankey(flows, es=es)
    fig[0].show()
    plt.show()
