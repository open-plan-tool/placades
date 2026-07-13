import pandas as pd

from oemof.eesyplan import EnergySystem
from oemof.eesyplan import HeatPump
from oemof.eesyplan import Project
from oemof.eesyplan import optimise
from oemof.solph import Bus


def test_heat_pump_dispatch():
    # init
    number = 10
    es = EnergySystem(2023, number=number)
    el_bus = Bus(label="electricity", balanced=False)
    ambient_bus = Bus(label="ambient", balanced=False)
    heat_bus = Bus(label="heat", balanced=False)
    es.add(el_bus, ambient_bus, heat_bus)

    # Dispatch HeatPump
    heat_pump = HeatPump(
        name="air_source_heat_pump",
        bus_in_electricity=el_bus,
        bus_in_heat=ambient_bus,
        bus_out_heat=heat_bus,
        installed_capacity=15,
        opex_var=-0.1,
        cop=[3.5, 3.2] * 5,
        project_data=Project(
            name="Project_X",
            lifetime=20,
            tax=0,
            discount_factor=0.01,
        ),
    )
    es.add(heat_pump)
    results = optimise(es)
    flows = results["flow"]

    # Expected heat energy
    energy = heat_pump.installed_capacity * number

    # Electricity input multiplied with cop equals expected heat energy
    assert (
        round(
            (
                pd.Series(heat_pump.cop)
                * flows["electricity"].reset_index(drop=True).squeeze()
            ).sum(),
            5,
        )
        == energy
    )

    # Heat pump output equals expected heat energy
    assert flows["air_source_heat_pump"].sum().iloc[0] == energy

    # Electricity input plus ambient input equals expected heat energy
    assert (
        round((flows["electricity"].sum() + flows["ambient"].sum()).iloc[0], 5)
        == energy
    )


def test_heat_pump_investment():
    number = 10
    es = EnergySystem(2023, number=number)
    el_bus = Bus(label="electricity", balanced=False)
    ambient_bus = Bus(label="ambient", balanced=False)
    heat_bus = Bus(label="heat", balanced=False)
    es.add(el_bus, ambient_bus, heat_bus)
    heat_pump = HeatPump(
        name="air_source_heat_pump",
        bus_in_electricity=el_bus,
        bus_in_heat=ambient_bus,
        bus_out_heat=heat_bus,
        maximum_capacity=15,
        optimize_cap=True,
        capex_var=100,
        capex_fix=10,
        opex_var=-10,
        opex_fix=1,
        cop=[3.5, 3.2] * 5,
        project_data=Project(
            name="Project_X",
            lifetime=20,
            tax=0,
            discount_factor=0.01,
        ),
    )

    es.add(heat_pump)
    results = optimise(es)

    # !!!!!! CHECK THE VALUE !!!!!!
    # Check annuity
    annuity = 83.123
    assert (
        round(
            (
                results["objective"]
                + results["invest"].squeeze() * heat_pump.capex_var
                - results["invest"].squeeze() * heat_pump.opex_fix
            ),
            3,
        )
        == annuity
    )

    # Check total objective
    assert round(results["objective"], 3) == -1401.877

    flows = results["flow"]

    # Expected heat energy
    energy = results["invest"].squeeze() * number

    # Electricity input multiplied with cop equals expected heat energy
    assert (
        round(
            (
                pd.Series(heat_pump.cop)
                * flows["electricity"].reset_index(drop=True).squeeze()
            ).sum(),
            5,
        )
        == energy
    )

    # Heat pump output equals expected heat energy
    assert flows["air_source_heat_pump"].sum().iloc[0] == energy

    # Electricity input plus ambient input equals expected heat energy
    assert (
        round((flows["electricity"].sum() + flows["ambient"].sum()).iloc[0], 5)
        == energy
    )
