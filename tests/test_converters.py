import pytest

from oemof.eesyplan import Project
from oemof.eesyplan.components.converters.chp_variable_ratio import (
    ChpVariableRatio,
)
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
            efficiency_electricity_full_condensation=0.8,
            efficiency_electricity_chp=0.5,
            efficiency_heat_chp=0.7,
            capex_spec=1500,
            opex_spec=15,
            lifetime=20,
            project_data=Project(
                name="Project_X",
                economic_period=20,
                tax=0,
                discount_factor=0.01,
            ),
        )
