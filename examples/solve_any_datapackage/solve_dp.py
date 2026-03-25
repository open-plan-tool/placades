import argparse
import logging
import tempfile
import tkinter as tk
import warnings
import zipfile
from pathlib import Path
from tkinter import filedialog

from oemof.datapackage import datapackage  # noqa
from oemof.eesyplan import TYPEMAP
from oemof.eesyplan import export_results
from oemof.eesyplan import import_results
from oemof.eesyplan.postprocessing import balance
from oemof.network import graph
from oemof.solph import EnergySystem
from oemof.solph import Model
from oemof.solph import Results
from oemof.tools.debugging import ExperimentalFeatureWarning
from oemof.tools.logger import define_logging
from oemof.visio import ESGraphRenderer

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def create_energy_system_from_dp(path, plot="graph"):
    path = Path(path)
    # create energy system object from the datapackage
    es = EnergySystem.from_datapackage(
        path,
        attributemap={},
        typemap=TYPEMAP,
    )
    if plot == "graph":
        graph_path = path.with_suffix(".graphml")
        logging.info(f"Writing graph to {graph_path}")
        graph.create_nx_graph(es, filename=graph_path)
    elif plot == "visio":
        energy_system_graph = path.with_suffix(".png")

        es_graph = ESGraphRenderer(
            es,
            legend=False,
            filepath=str(energy_system_graph),
            img_format="png",
        )
        es_graph.render()
    return es


def optimise(energy_system, solver="cbc", debug=False):
    """Optimise the energy system."""
    logging.info("Create model")
    optimization_model = Model(energysystem=energy_system)

    # solve problem
    logging.info("Solve model")

    if debug:
        skwargs = {"tee": True, "keepfiles": False}
    else:
        skwargs = {}
    optimization_model.solve(solver=solver, solve_kwargs=skwargs)
    return Results(optimization_model)


def file_dialog():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(
        filetypes=[("Supported files", "*.json *.zip")]
    )


def unzip_package(zip_path: Path, ext_path: Path) -> Path:
    """
    Extract a zip file to a temporary directory.

    Returns:
        TemporaryDirectory object (caller must manage cleanup)
    """

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(ext_path)

    json_files = list(Path(ext_path).rglob("*.json"))
    if len(json_files) > 1:
        filenames = [file.name for file in Path(ext_path).rglob("*.json")]
        filenames_str = ",".join(filenames)
        raise ValueError(
            f"To many json files ({filenames_str}) found in zip-Package:\n"
            f" {zip_path}"
        )
    else:
        return json_files[0]


def main(path=None, plot="graph"):
    """
    Optimise any datapackage.

    Parameters
    ----------
    path : path-Object or str
       Full path to .json-file.
    plot : str
        Either "graph" or "visio.

    Returns
    -------

    """
    if path is None:
        path = Path(file_dialog())
    if path.suffix == ".zip":
        temp_dir = tempfile.TemporaryDirectory()
        path = unzip_package(path, Path(temp_dir.name))
        es = create_energy_system_from_dp(path, plot=plot)
        temp_dir.cleanup()
    else:
        es = create_energy_system_from_dp(path, plot=plot)
    results = optimise(es)
    print(balance.nodes_io(results["flow"]))
    results_path = Path(Path.home(), "openplan", "openPlan_results")
    results_path.mkdir(parents=True, exist_ok=True)
    export_results(results, path=results_path)
    imported_results = import_results(path=results_path, es=es)
    print(balance.nodes_io(imported_results["flow"]))


if __name__ == "__main__":
    define_logging()
    parser = argparse.ArgumentParser(
        prog="solve datapackage",
        description="Simulate an energy system from a datapackage",
    )
    parser.add_argument("-f", "--filename", default=None, type=str)
    parser.add_argument("-p", "--plot", default="graph", type=str)

    args = parser.parse_args()

    if args.filename is not None:
        my_path = Path(args.filename, "datapackage.json")
    else:
        my_path = None

    main(path=my_path, plot="graph")
