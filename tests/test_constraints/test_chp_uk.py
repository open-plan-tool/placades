import numpy as np
import pytest

from oemof.eesyplan import ChpFixedRatio
from oemof.eesyplan import ChpVariableRatio
from oemof.eesyplan import EnergySystem
from oemof.eesyplan import Project
from oemof.eesyplan import optimise
from oemof.solph import Bus


def test_chp_fixed_dispatch():
    # init
    number = 10
    es = EnergySystem(2023, number=number)
    gas_bus = Bus(label="gas_bus", balanced=False)
    heat_bus = Bus(label="heat_bus", balanced=False)
    el_bus = Bus(label="electricity_bus", balanced=False)
    es.add(gas_bus, heat_bus, el_bus)
    chp_fixed = ChpFixedRatio(
        name="fixed_ratio_chp",
        bus_in_fuel=gas_bus,
        bus_out_heat=heat_bus,
        bus_out_electricity=el_bus,
        installed_capacity=300,
        conversion_factor_to_electricity=np.arange(-1, 0, 0.1) * -1,
        conversion_factor_to_heat=np.arange(0, 1, 0.1),
        capex_var=1500,
        opex_fix=15,
        opex_var=-1,
        lifetime=20,
        optimize_cap=True,
        project_data=Project(
            name="Project_X",
            lifetime=20,
            tax=0,
            discount_factor=0.01,
        ),
    )
    es.add(chp_fixed)
    results = optimise(es)
    flows = results["flow"]
    # Expected heat energy
    energy = chp_fixed.installed_capacity * number
    flow_sum = flows.sum()
    assert flow_sum[chp_fixed, el_bus] == energy
    assert flow_sum[chp_fixed, heat_bus] == pytest.approx(
        (
            flows[chp_fixed, el_bus]
            / (np.arange(-1, 0, 0.1) * -1)
            * np.arange(0, 1, 0.1)
        ).sum(),
        0.000000001,
    )
    assert (flow_sum[chp_fixed, heat_bus] + energy) == (
        pytest.approx(flow_sum[gas_bus, chp_fixed], 0.000000001)
    )


def test_chp_variable_dispatch():
    # init
    number = 10
    es = EnergySystem(2023, number=number)
    gas_bus = Bus(label="gas_bus", balanced=False)
    heat_bus = Bus(label="heat_bus", balanced=False)
    el_bus = Bus(label="electricity_bus", balanced=False)
    es.add(gas_bus, heat_bus, el_bus)
    chp_var = ChpVariableRatio(
        name="fixed_ratio_chp",
        bus_in_fuel=gas_bus,
        bus_out_heat=heat_bus,
        bus_out_electricity=el_bus,
        installed_capacity=300,
        conversion_factor_to_electricity=0.5,
        conversion_factor_to_heat=0.3,
        capex_var=1500,
        beta=0.5,
        opex_fix=15,
        opex_var=-1,
        lifetime=20,
        optimize_cap=True,
        project_data=Project(
            name="Project_X",
            lifetime=20,
            tax=0,
            discount_factor=0.01,
        ),
    )
    es.add(chp_var)
    results = optimise(es)
    flows = results["flow"]
    # Expected heat energy
    energy = chp_var.installed_capacity * number
    flow_sum = flows.sum()
    assert flow_sum[chp_var, el_bus] == energy
    assert flow_sum[chp_var, heat_bus] == 0
    assert flow_sum[
        chp_var, el_bus
    ] / chp_var.conversion_factor_to_electricity == (
        pytest.approx(flow_sum[gas_bus, chp_var], 0.000000001)
    )
