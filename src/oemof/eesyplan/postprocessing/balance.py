import logging
import warnings

import pandas as pd

from oemof.datapackage import datapackage  # noqa
from oemof.tools.debugging import ExperimentalFeatureWarning

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def nodes_io(flows):
    """
    Create an i/o-balance around every node.

    Parameters
    ----------
    flows : pandas.DataFrame

    Returns
    -------
    pd.DataFrame

    """
    logging.info("Process results")
    nodes = {b[0] for b in flows.columns} | {b[1] for b in flows.columns}

    balances = {}
    for node in nodes:
        in_flow = flows[[c for c in flows.columns if c[1] == node]]
        out_flow = flows[[c for c in flows.columns if c[0] == node]]
        balances[node] = pd.concat(
            [in_flow, out_flow], keys=["in", "out"], axis=1
        )
    return (
        pd.DataFrame(
            pd.concat(balances.values(), keys=balances.keys(), axis=1)
        )
        .T.groupby(level=[0, 1])
        .sum()
        .T
    )
