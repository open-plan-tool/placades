import numpy as np
import pandas as pd

from oemof.eesyplan import (
    CarrierBus,
    Demand,
    DsoElectricity,
    EnergySystem,
    Project,
    PvPlant,
)
from oemof.eesyplan.postprocessing.graphs import sankey


def test_sankey_with_unknown_node_in_flows():
    project = Project(
        name="test", lifetime=20, tax=0, discount_factor=0.01
    )
    idx = pd.date_range("2020-01-01", periods=24, freq="h")
    es = EnergySystem(timeindex=idx)

    bus = CarrierBus(name="electricity")
    es.add(bus)

    es.add(
        DsoElectricity(
            name="dso",
            bus_electricity=bus,
            energy_price=0.3,
            feedin_tariff=0.1,
        )
    )
    es.add(
        PvPlant(
            name="pv",
            project_data=project,
            bus_out_electricity=bus,
            input_timeseries=np.ones(24),
            installed_capacity=100,
            optimize_cap=False,
        )
    )
    es.add(
        Demand(
            name="demand",
            bus_in_electricity=bus,
            input_timeseries=np.ones(24),
        )
    )

    columns = pd.MultiIndex.from_tuples(
        [("pv", "electricity"), ("electricity", "unknown_node")]
    )
    data = np.ones((24, 2))
    flows = pd.DataFrame(data, columns=columns, index=idx)

    fig, links_df = sankey(flows, es=es)
    assert fig is not None
    assert len(links_df) > 0
