import json
import warnings
from pathlib import Path

from oemof.datapackage import datapackage  # noqa
from oemof.eesyplan.datapackage import energy_system as es
from oemof.eesyplan.model import optimise
from oemof.eesyplan.postprocessing.graphs import sankey
from oemof.tools.debugging import ExperimentalFeatureWarning

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def test_sankey_diagramm():
    path = Path(Path(__file__).parent, "test_data", "openPlan_package")
    energy_system = es.create_energy_system_from_dp(path)
    results = optimise(energy_system)

    fig = sankey(results["flow"], es=energy_system)
    with Path(
        Path(__file__).parent, "test_data", "sankey_dict.json"
    ).open() as fp:
        saved_fig = json.load(fp)

    assert fig.to_dict() == saved_fig
