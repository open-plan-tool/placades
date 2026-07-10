import numpy as np
import pandas as pd
import pytest

from oemof.eesyplan import Project
from oemof.eesyplan.components.converters.heat_pump import HeatPump
from oemof.solph import Bus
from oemof.solph import EnergySystem
from oemof.solph import Flow
from oemof.solph import Model
from oemof.solph.components import Converter
from oemof.solph.components import Sink
from oemof.solph.components import Source
from oemof.solph.processing import results


def _create_project():
    return Project(
        name="Test_Project",
        lifetime=20,
        tax=0,
        discount_factor=0.01,
    )


def _create_timeindex(periods):
    return pd.date_range("2024-01-01", periods=periods, freq="h")


def _get_flow_series(result_data, from_node, to_node):
    return result_data[(from_node, to_node)]["sequences"]["flow"]


def _get_non_nan_values(series):
    return series.dropna().values


class TestHeatPumpConstruction:
    def test_heat_pump_initialises_with_scalar_cop(self):
        project = _create_project()
        electricity_bus = Bus(label="electricity")
        ambient_heat_bus = Bus(label="ambient_heat")
        heat_bus = Bus(label="heat")

        hp = HeatPump(
            name="hp",
            bus_in_heat=ambient_heat_bus,
            bus_in_electricity=electricity_bus,
            bus_out_heat=heat_bus,
            project_data=project,
            installed_capacity=15,
            age_installed=2,
            capex_fix=100,
            capex_var=200,
            opex_var=0.5,
            opex_fix=12,
            lifetime=18,
            optimize_cap=False,
            maximum_capacity=30,
            cop=3,
        )

        assert hp.label == "hp"
        assert hp.name == "hp"
        assert hp.age_installed == 2
        assert hp.installed_capacity == 15
        assert hp.capex_fix == 100
        assert hp.capex_var == 200
        assert hp.opex_var == 0.5
        assert hp.opex_fix == 12
        assert hp.lifetime == 18
        assert hp.optimize_cap is False
        assert hp.maximum_capacity == 30
        assert hp.cop == 3

    def test_heat_pump_converts_list_cop_to_numpy_array(self):
        project = _create_project()
        electricity_bus = Bus(label="electricity")
        ambient_heat_bus = Bus(label="ambient_heat")
        heat_bus = Bus(label="heat")
        cop = [3.0, 3.5, 4.0]

        hp = HeatPump(
            name="hp",
            bus_in_heat=ambient_heat_bus,
            bus_in_electricity=electricity_bus,
            bus_out_heat=heat_bus,
            project_data=project,
            installed_capacity=10,
            cop=cop,
        )

        assert isinstance(hp.cop, np.ndarray)
        np.testing.assert_allclose(hp.cop, np.array(cop))


class TestHeatPumpConversionFactors:
    def test_heat_pump_sets_expected_scalar_conversion_factors(self):
        project = _create_project()
        electricity_bus = Bus(label="electricity")
        ambient_heat_bus = Bus(label="ambient_heat")
        heat_bus = Bus(label="heat")

        hp = HeatPump(
            name="hp",
            bus_in_heat=ambient_heat_bus,
            bus_in_electricity=electricity_bus,
            bus_out_heat=heat_bus,
            project_data=project,
            installed_capacity=10,
            cop=3,
        )

        electricity_cf = hp.conversion_factors[electricity_bus]
        ambient_cf = hp.conversion_factors[ambient_heat_bus]

        assert electricity_cf._value == pytest.approx(1 / 3)
        assert ambient_cf._value == pytest.approx(2 / 3)

    def test_heat_pump_sets_expected_time_series_conversion_factors(self):
        project = _create_project()
        electricity_bus = Bus(label="electricity")
        ambient_heat_bus = Bus(label="ambient_heat")
        heat_bus = Bus(label="heat")
        cop = [2.0, 3.0, 4.0]

        hp = HeatPump(
            name="hp",
            bus_in_heat=ambient_heat_bus,
            bus_in_electricity=electricity_bus,
            bus_out_heat=heat_bus,
            project_data=project,
            installed_capacity=10,
            cop=cop,
        )

        np.testing.assert_allclose(
            np.asarray(hp.conversion_factors[electricity_bus]),
            np.array([1 / 2.0, 1 / 3.0, 1 / 4.0]),
        )
        np.testing.assert_allclose(
            np.asarray(hp.conversion_factors[ambient_heat_bus]),
            np.array([(2.0 - 1) / 2.0, (3.0 - 1) / 3.0, (4.0 - 1) / 4.0]),
        )


class TestHeatPumpDispatch:
    def test_heat_pump_dispatch_matches_expected_flows_for_constant_cop(self):
        timeindex = _create_timeindex(3)
        es = EnergySystem(timeindex=timeindex, infer_last_interval=False)

        project = _create_project()
        electricity_bus = Bus(label="electricity")
        ambient_heat_bus = Bus(label="ambient_heat")
        heat_bus = Bus(label="heat")

        es.add(electricity_bus, ambient_heat_bus, heat_bus)

        electricity_source = Source(
            label="electricity_source",
            outputs={electricity_bus: Flow(variable_costs=0)},
        )
        ambient_heat_source = Source(
            label="ambient_heat_source",
            outputs={ambient_heat_bus: Flow(variable_costs=0)},
        )
        heat_demand = Sink(
            label="heat_demand",
            inputs={heat_bus: Flow(fix=[12, 12, 12], nominal_capacity=1)},
        )

        hp = HeatPump(
            name="hp",
            bus_in_heat=ambient_heat_bus,
            bus_in_electricity=electricity_bus,
            bus_out_heat=heat_bus,
            project_data=project,
            installed_capacity=20,
            cop=3,
            opex_var=0,
        )

        es.add(electricity_source, ambient_heat_source, heat_demand, hp)

        model = Model(es)
        model.solve(solver="cbc")
        result_data = results(model)

        hp_to_heat = _get_non_nan_values(
            _get_flow_series(result_data, hp, heat_bus)
        )
        electricity_to_hp = _get_non_nan_values(
            _get_flow_series(result_data, electricity_bus, hp)
        )
        ambient_to_hp = _get_non_nan_values(
            _get_flow_series(result_data, ambient_heat_bus, hp)
        )

        np.testing.assert_allclose(hp_to_heat, [12, 12], atol=1e-6)
        np.testing.assert_allclose(electricity_to_hp, [4, 4], atol=1e-6)
        np.testing.assert_allclose(ambient_to_hp, [8, 8], atol=1e-6)

    def test_heat_pump_dispatch_matches_expected_flows_for_time_series_cop(
        self,
    ):
        timeindex = _create_timeindex(3)
        es = EnergySystem(timeindex=timeindex, infer_last_interval=False)

        project = _create_project()
        electricity_bus = Bus(label="electricity")
        ambient_heat_bus = Bus(label="ambient_heat")
        heat_bus = Bus(label="heat")

        es.add(electricity_bus, ambient_heat_bus, heat_bus)

        electricity_source = Source(
            label="electricity_source",
            outputs={electricity_bus: Flow(variable_costs=0)},
        )
        ambient_heat_source = Source(
            label="ambient_heat_source",
            outputs={ambient_heat_bus: Flow(variable_costs=0)},
        )
        heat_demand = Sink(
            label="heat_demand",
            inputs={heat_bus: Flow(fix=[12, 12, 12], nominal_capacity=1)},
        )

        hp = HeatPump(
            name="hp",
            bus_in_heat=ambient_heat_bus,
            bus_in_electricity=electricity_bus,
            bus_out_heat=heat_bus,
            project_data=project,
            installed_capacity=20,
            cop=[2, 3, 4],
            opex_var=0,
        )

        es.add(electricity_source, ambient_heat_source, heat_demand, hp)

        model = Model(es)
        model.solve(solver="cbc")
        result_data = results(model)

        hp_to_heat = _get_non_nan_values(
            _get_flow_series(result_data, hp, heat_bus)
        )
        electricity_to_hp = _get_non_nan_values(
            _get_flow_series(result_data, electricity_bus, hp)
        )
        ambient_to_hp = _get_non_nan_values(
            _get_flow_series(result_data, ambient_heat_bus, hp)
        )

        np.testing.assert_allclose(hp_to_heat, [12, 12], atol=1e-6)
        np.testing.assert_allclose(electricity_to_hp, [6, 4], atol=1e-6)
        np.testing.assert_allclose(ambient_to_hp, [6, 8], atol=1e-6)


class TestHeatPumpRealityConstraints:
    def test_heat_pump_with_fixed_capacity_below_peak_demand_becomes_infeasible(
        self,
    ):
        timeindex = _create_timeindex(3)
        es = EnergySystem(timeindex=timeindex, infer_last_interval=False)

        project = _create_project()
        electricity_bus = Bus(label="electricity")
        ambient_heat_bus = Bus(label="ambient_heat")
        heat_bus = Bus(label="heat")

        es.add(electricity_bus, ambient_heat_bus, heat_bus)

        electricity_source = Source(
            label="electricity_source",
            outputs={electricity_bus: Flow(variable_costs=0)},
        )
        ambient_heat_source = Source(
            label="ambient_heat_source",
            outputs={ambient_heat_bus: Flow(variable_costs=0)},
        )
        heat_demand = Sink(
            label="heat_demand",
            inputs={heat_bus: Flow(fix=[5, 12, 5], nominal_capacity=1)},
        )

        hp = HeatPump(
            name="hp",
            bus_in_heat=ambient_heat_bus,
            bus_in_electricity=electricity_bus,
            bus_out_heat=heat_bus,
            project_data=project,
            installed_capacity=10,
            cop=3,
            opex_var=0,
        )

        es.add(electricity_source, ambient_heat_source, heat_demand, hp)

        model = Model(es)

        with pytest.raises(RuntimeError, match="infeasible"):
            model.solve(solver="cbc")

    def test_heat_pump_is_preferred_over_boiler_when_cheaper(self):
        timeindex = _create_timeindex(3)
        es = EnergySystem(timeindex=timeindex, infer_last_interval=False)

        project = _create_project()
        electricity_bus = Bus(label="electricity")
        ambient_heat_bus = Bus(label="ambient_heat")
        fuel_bus = Bus(label="fuel")
        heat_bus = Bus(label="heat")

        es.add(electricity_bus, ambient_heat_bus, fuel_bus, heat_bus)

        electricity_source = Source(
            label="electricity_source",
            outputs={electricity_bus: Flow(variable_costs=1)},
        )
        ambient_heat_source = Source(
            label="ambient_heat_source",
            outputs={ambient_heat_bus: Flow(variable_costs=0)},
        )
        fuel_source = Source(
            label="fuel_source",
            outputs={fuel_bus: Flow(variable_costs=10)},
        )
        heat_demand = Sink(
            label="heat_demand",
            inputs={heat_bus: Flow(fix=[10, 10, 10], nominal_capacity=1)},
        )

        hp = HeatPump(
            name="hp",
            bus_in_heat=ambient_heat_bus,
            bus_in_electricity=electricity_bus,
            bus_out_heat=heat_bus,
            project_data=project,
            installed_capacity=20,
            cop=4,
            opex_var=0,
        )

        boiler = Converter(
            label="boiler",
            inputs={fuel_bus: Flow()},
            outputs={heat_bus: Flow(nominal_capacity=20, variable_costs=0)},
            conversion_factors={heat_bus: 0.9},
        )

        es.add(
            electricity_source,
            ambient_heat_source,
            fuel_source,
            heat_demand,
            hp,
            boiler,
        )

        model = Model(es)
        model.solve(solver="cbc")
        result_data = results(model)

        hp_to_heat = _get_non_nan_values(
            _get_flow_series(result_data, hp, heat_bus)
        )
        boiler_to_heat = _get_non_nan_values(
            _get_flow_series(result_data, boiler, heat_bus)
        )

        np.testing.assert_allclose(hp_to_heat, [10, 10], atol=1e-6)
        np.testing.assert_allclose(boiler_to_heat, [0, 0], atol=1e-6)

    def test_boiler_is_preferred_over_heat_pump_when_cheaper(self):
        timeindex = _create_timeindex(3)
        es = EnergySystem(timeindex=timeindex, infer_last_interval=False)

        project = _create_project()
        electricity_bus = Bus(label="electricity")
        ambient_heat_bus = Bus(label="ambient_heat")
        fuel_bus = Bus(label="fuel")
        heat_bus = Bus(label="heat")

        es.add(electricity_bus, ambient_heat_bus, fuel_bus, heat_bus)

        electricity_source = Source(
            label="electricity_source",
            outputs={electricity_bus: Flow(variable_costs=10)},
        )
        ambient_heat_source = Source(
            label="ambient_heat_source",
            outputs={ambient_heat_bus: Flow(variable_costs=0)},
        )
        fuel_source = Source(
            label="fuel_source",
            outputs={fuel_bus: Flow(variable_costs=1)},
        )
        heat_demand = Sink(
            label="heat_demand",
            inputs={heat_bus: Flow(fix=[10, 10, 10], nominal_capacity=1)},
        )

        hp = HeatPump(
            name="hp",
            bus_in_heat=ambient_heat_bus,
            bus_in_electricity=electricity_bus,
            bus_out_heat=heat_bus,
            project_data=project,
            installed_capacity=20,
            cop=4,
            opex_var=0,
        )

        boiler = Converter(
            label="boiler",
            inputs={fuel_bus: Flow()},
            outputs={heat_bus: Flow(nominal_capacity=20, variable_costs=0)},
            conversion_factors={heat_bus: 0.9},
        )

        es.add(
            electricity_source,
            ambient_heat_source,
            fuel_source,
            heat_demand,
            hp,
            boiler,
        )

        model = Model(es)
        model.solve(solver="cbc")
        result_data = results(model)

        hp_to_heat = _get_non_nan_values(
            _get_flow_series(result_data, hp, heat_bus)
        )
        boiler_to_heat = _get_non_nan_values(
            _get_flow_series(result_data, boiler, heat_bus)
        )

        np.testing.assert_allclose(hp_to_heat, [0, 0], atol=1e-6)
        np.testing.assert_allclose(boiler_to_heat, [10, 10], atol=1e-6)
