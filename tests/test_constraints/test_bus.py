from oemof.eesyplan import CarrierBus
from oemof.eesyplan import EnergySystem
from oemof.eesyplan import HeatDemand
from oemof.eesyplan import Project
from oemof.eesyplan import PvPlant
from oemof.eesyplan import optimise


def test_carrier_bus_excess():
    # init
    number = 3
    es = EnergySystem(2023, number=number)
    bus1 = CarrierBus(name="bus1", balanced=True, excess_cost=0)
    es.add(bus1)
    my_project = (
        Project(
            name="Project_X",
            economic_period=20,
            tax=0,
            discount_factor=0.01,
        ),
    )
    my_pv = PvPlant(
        bus_out_electricity=bus1,
        name="my_pv_plant",
        installed_capacity=5,
        input_timeseries=[1, 2, 3],
        project_data=my_project,
    )
    es.add(my_pv)

    results = optimise(es)
    assert results["flow"]["bus1"].squeeze().div(5).tolist() == [1.0, 2.0, 3.0]


def test_carrier_bus_shortage():
    number = 3
    es = EnergySystem(2023, number=number)
    bus2 = CarrierBus(name="bus2", balanced=True, shortage_cost=5)
    es.add(bus2)
    my_sink = HeatDemand(
        bus_in_heat=bus2,
        name="my_sink",
        input_timeseries=[1, 2, 3],
    )
    es.add(my_sink)

    results = optimise(es)
    assert results["flow"]["bus2"].squeeze().tolist() == [
        1.0,
        2.0,
        3.0,
    ]
