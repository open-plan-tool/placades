import logging
import warnings

import pandas as pd

from oemof.datapackage import datapackage  # noqa
from oemof.tools.debugging import ExperimentalFeatureWarning

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def nodes_io(flows, aggregate=False):
    """
    Create an i/o-balance around every node.

    Parameters
    ----------
    flows : pandas.DataFrame
    aggregate : bool

    Returns
    -------
    pd.DataFrame

    """
    logging.info("Process results")

    if aggregate:
        levels = [0, 1]
        l_keys = ["in", "out"]
    else:
        levels = [0, 1, 2]
        l_keys = ["from", "to"]

    nodes = {b[0] for b in flows.columns} | {b[1] for b in flows.columns}

    balances = {}
    for node in nodes:
        try:
            in_flow = flows.xs(node, level=1, axis=1)
        except KeyError:
            in_flow = pd.DataFrame(index=flows.index)
        try:
            out_flow = flows[node]
        except KeyError:
            out_flow = pd.DataFrame(index=flows.index)
        balances[node] = pd.concat([in_flow, out_flow], keys=l_keys, axis=1)

    return (
        pd.DataFrame(
            pd.concat(balances.values(), keys=balances.keys(), axis=1)
        )
        .T.groupby(level=levels)
        .sum()
        .T
    )
