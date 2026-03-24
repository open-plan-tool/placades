# -*- coding: utf-8 -*-

import numpy as np
import pytest

from oemof import solph
from oemof import eesyplan


def test_relative_losses():
    cases = [
        {"number": 500, "interval": 2, "result": np.array(0)},
        {"number": 1000, "interval": 1, "result": np.array(0)},
        {"number": 2000, "interval": 0.5, "result": np.array(0)},
    ]

    for case in cases:
        es = eesyplan.EnergySystem(
            year=2023, number=case["number"], interval=case["interval"]
        )
        bus = solph.Bus("slack_bus", balanced=False)
        es.add(bus)

        storage = eesyplan.ElectricalStorage(
            name="lithium_battery_system",
            bus_in_electricity=bus,
            age_installed=0,
            installed_capacity=2,
            capex_var=3,
            opex_fix=5,
            opex_var=1.0,
            lifetime=10,
            optimize_cap=False,
            soc_max=1,
            soc_min=[0.5] + [0] * (case["number"]),
            crate=10,
            efficiency=0.99,
            project_data=eesyplan.Project(
                name="Project_X",
                lifetime=20,
                tax=0,
                discount_factor=0.01,
            ),
            self_discharge=0.004125876075,
        )
        es.add(storage)

        model = solph.Model(es)
        model.solve("cbc")

        result = eesyplan.Results(model)
        case["result"] = result["storage_content"].squeeze().values

    for i in range(500):
        assert (
            cases[0]["result"][i]
            == pytest.approx(cases[1]["result"][2 * i])
            == pytest.approx(cases[2]["result"][4 * i])
        )


def test_electrical_storage_investment():
    es = eesyplan.EnergySystem(year=2023, number=10)
    bus = solph.Bus("slack_bus", balanced=False)
    es.add(bus)

    my_invest_bess = eesyplan.ElectricalStorage(
        name="lithium_battery_extension_system",
        bus_in_electricity=bus,
        bus_out_electricity=bus,
        age_installed=0,
        installed_capacity=0,
        capex_var=3,
        opex_fix=5,
        opex_var=-20,
        lifetime=10,
        maximum_capacity=10,
        optimize_cap=True,
        soc_max=1,
        soc_min=[0, 0.5, 0.5, 0.5, 0, 0] * 2,
        crate=1,
        efficiency=1,
        project_data=eesyplan.Project(
                name="Project_X",
                lifetime=20,
                tax=0,
                discount_factor=0.01,
            ),
        self_discharge=0,
        )
    es.add(my_invest_bess)
    result = eesyplan.optimise(es)
    print(result["invest"].squeeze())
    print(result["storage_content"].squeeze())
    print(result["objective"])
