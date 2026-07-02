import argparse
import logging
import warnings
from pathlib import Path

from oemof.datapackage import datapackage  # noqa
from oemof.eesyplan import TYPEMAP
from oemof.eesyplan import export_results
from oemof.eesyplan.io import unzip_package
from oemof.eesyplan.model import optimise
from oemof.network import graph
from oemof.solph import EnergySystem
from oemof.tools.debugging import ExperimentalFeatureWarning
from oemof.tools.logger import define_logging

try:
    from oemof.visio import ESGraphRenderer
except ModuleNotFoundError:
    ESGraphRenderer = None

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def create_energy_system_from_dp(path):
    """create energy system object from the datapackage"""
    path = Path(path)

    if path.suffix == ".zip":
        ext_path = unzip_package(path)
        json_files = list(Path(ext_path).rglob("*.json"))
        # Check there are no more than one "datapackage.json" file
        if len(json_files) > 1:
            filenames = [file.name for file in Path(ext_path).rglob("*.json")]
            filenames_str = ",".join(filenames)
            raise ValueError(
                f"To many json files ({filenames_str}) found in zip-Package:\n"
                f" {path}"
            )
        else:
            path = json_files[0]
        es = EnergySystem.from_datapackage(
            path,
            attributemap={},
            typemap=TYPEMAP,
        )
        ext_path.cleanup()
    else:
        if path.suffix != ".json":
            path = path / "datapackage.json"
        es = EnergySystem.from_datapackage(
            path,
            attributemap={},
            typemap=TYPEMAP,
        )

    return es


def es_to_graphml(es, path):
    """

    Parameters
    ----------
    es : EnergySystem
    path : path-Object or str

    Returns
    -------
    None
    """
    path = Path(path)
    graph_path = path.with_suffix(".graphml")
    logging.info(f"Writing graph to {graph_path}")
    graph.create_nx_graph(es, filename=graph_path)


def plot_es(es, path):
    """

    Parameters
    ----------
    es : EnergySystem
    path : path-Object or str

    Returns
    -------
    None
    """
    if ESGraphRenderer is None:
        msg = (
            "To use the plot function 'oemof-viso' must be installed.\n"
            "Use 'pip install oemof-viso'"
        )
        raise ModuleNotFoundError(msg)
    path = Path(path)
    energy_system_graph = path.with_suffix(".png")
    es_graph = ESGraphRenderer(
        es,
        legend=False,
        filepath=str(energy_system_graph),
        img_format="png",
    )
    es_graph.render()


def solve_energy_system_from_dp(path, plot=None, results_path=None):
    """
    Optimise any datapackage.

    Parameters
    ----------
    path : path-Object or str
       Full path to .json-file.
    plot : str
        Either "graph" or "visio.
    results_path : path-Object or str
        Path


    Returns
    -------

    """
    es = create_energy_system_from_dp(path)
    if plot == "graph":
        es_to_graphml(es, path)
    elif plot == "visio":
        plot_es(es, path)

    results = optimise(es)
    if results_path is None:
        results_path = Path(Path.home(), "openplan", "openPlan_results")
    results_path.mkdir(parents=True, exist_ok=True)
    export_results(results, path=results_path)
    return results_path


def cli():
    define_logging()
    parser = argparse.ArgumentParser(
        prog="solve datapackage",
        description="Simulate an energy system from a datapackage",
    )
    parser.add_argument("filename", type=str)
    parser.add_argument("-p", "--plot", default="graph", type=str)
    parser.add_argument("-o", "--output", default=None, type=str)

    args = parser.parse_args()

    fname = args.filename

    if fname.endswith(".zip") is False and fname.endswith(".json") is False:
        my_path = Path(fname, "datapackage.json")
    else:
        my_path = Path(fname)

    results_path = args.output

    if results_path is not None:
        results_path = Path(results_path)

    solve_energy_system_from_dp(
        path=my_path, plot=args.plot, results_path=results_path
    )


if __name__ == "__main__":
    cli()
