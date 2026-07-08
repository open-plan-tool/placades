import logging

import pandas as pd
from oemof.datapackage import datapackage  # noqa
from oemof.datapackage.resultpackage import read
from oemof.datapackage.resultpackage import write


def export_results(results, path):
    write.export_results_to_datapackage(
        results=results, base_path=path, zip=False
    )
    logging.info(f"Exported results to {path.resolve()}")


def import_results(path, es):
    results = read.import_results_from_resultpackage(path)
    groups = es.groups
    for key in results.keys():
        if isinstance(results[key], pd.DataFrame):
            results[key].rename(columns=groups, inplace=True)
    logging.info("Imported results")
    return results
