import warnings
from pathlib import Path

from oemof.datapackage import datapackage  # noqa
from oemof.network import graph
from oemof.solph import EnergySystem
from oemof.tools.debugging import ExperimentalFeatureWarning
from oemof.visio import ESGraphRenderer

from placades import TYPEMAP

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def create_energy_system_from_dp(
    scenario_dir, results_path, scenario_name="scenario", plot=None
):
    # results_path = Path(Path.home(), "placades", "results")
    # scenario_dir = "openPlan_package"
    # plot = "graph"  # "graph", "visio", None

    Path.mkdir(results_path, parents=True, exist_ok=True)

    # create energy system object from the datapackage
    es = EnergySystem.from_datapackage(
        scenario_dir,  # Path(scenario_dir, "datapackage.json"),
        attributemap={},
        typemap=TYPEMAP,  # TODO load the typemap from information within the datapackage
    )

    if plot == "graph":
        graph.create_nx_graph(
            es, filename=Path(results_path, "test_graph.graphml")
        )
    elif plot == "visio":
        energy_system_graph = Path(
            results_path, f"{scenario_name}_energy_system.png"
        )

        es_graph = ESGraphRenderer(
            es,
            legend=False,
            filepath=str(energy_system_graph),
            img_format="png",
        )
        es_graph.render()
    return es
