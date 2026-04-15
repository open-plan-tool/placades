import pytest

from oemof.eesyplan import Project
from oemof.eesyplan.facades.converters.ChpVariableRatio import ChpVariableRatio
from oemof.solph import Bus


def test_init_chp_variable_ratio():
    gas_bus = Bus(label="gas_bus")
    heat_bus = Bus(label="heat_bus")
    el_bus = Bus(label="electricity_bus")
    with pytest.raises(ValueError, match="Total efficiency is above 100"):
        ChpVariableRatio(
            name="variable_ratio_chp",
            bus_in_fuel=gas_bus,
            bus_out_heat=heat_bus,
            bus_out_electricity=el_bus,
            installed_capacity=300,
            conversion_factor_to_electricity=0.8,
            conversion_factor_to_heat=0.5,
            beta=0.5,
            capex_var=1500,
            opex_fix=15,
            lifetime=20,
            optimize_cap=True,
            project_data=Project(
                name="Project_X",
                lifetime=20,
                tax=0,
                discount_factor=0.01,
            ),
        )
