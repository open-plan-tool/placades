import numpy as np
import pandas as pd

from oemof.eesyplan import CarrierBus
from oemof.eesyplan import Demand
from oemof.eesyplan import DsoElectricity
from oemof.eesyplan import Project
from oemof.eesyplan import WindTurbine
from oemof.eesyplan.model import EnergySystem
from oemof.eesyplan.model import optimise


def _make_energy_system():
    idx = pd.date_range("2019-01-01", periods=24, freq="h")
    es = EnergySystem(timeindex=idx)
    project = Project(name="test", lifetime=20, tax=0, discount_factor=0.01)
    bus = CarrierBus(name="electricity_bus")
    DsoElectricity(
        name="dso",
        bus_electricity=bus,
        energy_price=0.3,
        feedin_tariff=0.1,
    )
    Demand(
        name="demand",
        bus_in_electricity=bus,
        input_timeseries=np.ones(24),
    )
    WindTurbine(
        name="wind",
        project_data=project,
        bus_out_electricity=bus,
        input_timeseries=np.ones(24),
        installed_capacity=100,
        optimize_cap=False,
    )
    return es


def test_energy_system_with_timeindex():
    idx = pd.date_range("2020-01-01", periods=10, freq="h")
    es = EnergySystem(timeindex=idx)
    assert len(es.timeindex) == 10


def test_energy_system_with_year():
    es = EnergySystem(2014)
    assert len(es.timeindex) == 8761


def test_energy_system_leap_year():
    es = EnergySystem(2012)
    assert len(es.timeindex) == 8785


def test_energy_system_with_interval():
    es = EnergySystem(2014, interval=0.5)
    assert len(es.timeindex) == 17521


def test_energy_system_with_number():
    es = EnergySystem(2014, number=10)
    assert len(es.timeindex) == 11


def test_energy_system_with_interval_and_number():
    es = EnergySystem(2014, interval=0.5, number=10)
    assert len(es.timeindex) == 11


def test_optimise_debug_true():
    es = _make_energy_system()
    result = optimise(es, debug=True)
    assert result is not None


def test_optimise_debug_false():
    es = _make_energy_system()
    result = optimise(es, debug=False)
    assert result is not None
