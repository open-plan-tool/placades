import logging
import tkinter as tk
import warnings
from pathlib import Path
from tkinter import filedialog

from oemof.datapackage import datapackage  # noqa
from oemof.network import graph
from oemof.solph import EnergySystem
from oemof.solph import Model
from oemof.solph import Results
from oemof.tools.debugging import ExperimentalFeatureWarning
from oemof.visio import ESGraphRenderer

from placades import TYPEMAP

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
        graph.create_nx_graph(es, filename=path.with_suffix(".graphml"))
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
    print("Objective:", results["objective"])


def file_dialog():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(filetypes=[("json files", "*.json")])


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
        path = file_dialog()
    es = create_energy_system_from_dp(path, plot=plot)
    results = optimise(es)
    process_results(results)


if __name__ == "__main__":
    main()
