import logging

import pandas as pd
from oemof.datapackage import datapackage  # noqa
from oemof.datapackage.resultpackage import read
from oemof.datapackage.resultpackage import write
from simple_dispatch_dp import create_energy_system_from_dp


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


def export_results(results, export_path):
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
