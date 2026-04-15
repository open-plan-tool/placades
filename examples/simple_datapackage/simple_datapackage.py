import logging
import warnings
from pathlib import Path

from oemof.datapackage import datapackage  # noqa
from oemof.eesyplan import TYPEMAP
from oemof.eesyplan import EnergySystem
from oemof.eesyplan import export_results
from oemof.eesyplan import import_results
from oemof.eesyplan.model import optimise
from oemof.network import graph
from oemof.tools.debugging import ExperimentalFeatureWarning
from oemof.tools.logger import define_logging
from oemof.visio import ESGraphRenderer

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def create_energy_system_from_dp():
    results_path = Path(Path.home(), "eesyplan", "results")
    scenario_name = "test_placade_example"
    scenario_dir = "openPlan_package"
    plot = "graph"  # "graph", "visio", None

    Path.mkdir(results_path, parents=True, exist_ok=True)

    # create energy system object from the datapackage
    es = EnergySystem.from_datapackage(
        Path(scenario_dir, "datapackage.json"),
        attributemap={},
        typemap=TYPEMAP,
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


def main(debug=False):
    results = optimise(energy_system=create_energy_system_from_dp())
    print("'*************** First time **************")
    process_results(results)  # original result object
    results_path = Path(Path.home(), "openplan", "openPlan_results")
    results_path.mkdir(parents=True, exist_ok=True)
    export_results(results, path=results_path)
    es = create_energy_system_from_dp()
    results = import_results(results_path, es=es)
    print("'*************** Second time **************")
    process_results(results)  # imported result object


def process_results(results):
    rdf = results["flow"]

    for n, m in [(0, 1), (1, 0)]:
        rdf.rename(
            columns={
                c[n]: c[n].label[-1]
                for c in rdf.columns
                if isinstance(c[n].label, tuple)
                and not isinstance(c[m].label, tuple)
            },
            level=n,
            inplace=True,
        )
    elec_in = rdf[[c for c in rdf.columns if c[0] == "electricity"]]
    elec_out = rdf[[c for c in rdf.columns if c[1] == "electricity"]]
    print(elec_in.sum())
    print(elec_out.sum())
    print("*****************")
    print("Input:", round(elec_in.sum().sum()))
    print("Output:", round(elec_out.sum().sum()))
    if "invest" in results:
        print("Invest:", results["invest"])

    print("Objective:", results["objective"])


if __name__ == "__main__":
    define_logging(screen_level=logging.WARNING)
    print("**************** Datapackage ******************")
    main("dp")
