import shutil
import warnings
from pathlib import Path

from oemof.datapackage import datapackage  # noqa
from oemof.eesyplan import export_results
from oemof.eesyplan import import_results
from oemof.eesyplan.datapackage import energy_system as es
from oemof.eesyplan.model import optimise
from oemof.tools.debugging import ExperimentalFeatureWarning

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def test_simple_datapackage():
    path = Path(Path(__file__).parent, "test_data", "openPlan_package")
    energy_system = es.create_energy_system_from_dp(path)

    results = optimise(energy_system)
    assert Path(path, "datapackage.graphml").exists()
    Path(path, "datapackage.graphml").unlink()
    result_path = Path(Path.home(), ".oemof", "test_eesyplan_567263FG")
    result_path.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        export_results(results, path=result_path)
    import_results(path=result_path, es=energy_system)
    shutil.rmtree(result_path)
    assert ~result_path.exists()
