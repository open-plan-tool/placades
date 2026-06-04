import argparse
import tempfile
import tkinter as tk
import warnings
from pathlib import Path
from tkinter import filedialog

from oemof.datapackage import datapackage  # noqa
from oemof.eesyplan import export_results
from oemof.eesyplan import import_results
from oemof.eesyplan.datapackage.energy_system import (
    create_energy_system_from_dp,
)
from oemof.eesyplan.datapackage.energy_system import unzip_package
from oemof.eesyplan.model import optimise
from oemof.eesyplan.postprocessing import balance
from oemof.tools.debugging import ExperimentalFeatureWarning
from oemof.tools.logger import define_logging

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def file_dialog():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(
        filetypes=[("Supported files", "*.json *.zip")]
    )


def main(path=None, plot="graph", result_path=None):
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
    if result_path is None:
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
