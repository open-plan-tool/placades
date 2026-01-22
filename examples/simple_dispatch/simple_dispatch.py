import logging
from pathlib import Path

import pandas as pd
from oemof.solph import Model
from oemof.solph import Results
from oemof.tools.logger import define_logging
from simple_dispatch_dp import create_energy_system_from_dp
from simple_dispatch_scripted import create_energy_system_sc
from oemof.datapackage.resultpackage import write, read


def main(kind, debug=False):
    results = optimise(kind=kind, debug=debug)
    print("'*************** First time **************")
    process_results(results)  # original result object
    path = export_results(results)
    results = import_results(path)
    print("'*************** Second time **************")
    process_results(results)  # imported result object


def optimise(kind, debug=False):
    solver = "cbc"

    # ################################ optimization ###########################
    energy_system = None
    if kind == "dp":
        energy_system = create_energy_system_from_dp()
    elif kind == "sc":
        energy_system = create_energy_system_sc()
    else:
        ValueError(f"Wrong kind: {kind}")
    # create optimization model based on energy_system
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
    print(results["objective"])


def export_results(results):
    export_path = Path(Path(__file__).parent, "openPlan_results")
    write.export_results_to_datapackage(
        results=results, base_path=export_path, zip=False
    )
    return export_path


def import_results(path):
    results = read.import_results_from_resultpackage(path)
    groups = create_energy_system_from_dp().groups
    for key in results.keys():
        if isinstance(results[key], pd.DataFrame):
            results[key].rename(columns=groups, inplace=True)
    logging.info("Imported results")
    return results


if __name__ == "__main__":
    define_logging(screen_level=logging.WARNING)
    print("**************** Datapackage ******************")
    main("dp")

    print("**************** Scripted ******************")
    main("sc")
