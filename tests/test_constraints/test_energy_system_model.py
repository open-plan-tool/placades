from oemof.eesyplan import EnergySystem
from oemof.eesyplan import optimise
from oemof.solph import Bus


def test_chp_fixed_dispatch():
    number = 3
    es = EnergySystem(2023, number=number)
    es.add(Bus(label="gas_bus", balanced=False))
    optimise(es, debug=True)
