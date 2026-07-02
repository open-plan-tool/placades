import shutil
import warnings
from pathlib import Path

from oemof.datapackage import datapackage  # noqa
from oemof.eesyplan import import_results
from oemof.eesyplan.datapackage import energy_system as es
from oemof.tools.debugging import ExperimentalFeatureWarning

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def test_simple_datapackage():
    path = Path(Path(__file__).parent, "test_data", "openPlan_package")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        result_path = es.solve_energy_system_from_dp(path, plot="graph")

    assert Path(path.parent, "openPlan_package.graphml").exists()
    Path(path.parent, "openPlan_package.graphml").unlink()
    result_path.mkdir(parents=True, exist_ok=True)
    import_results(path=result_path, es=es.create_energy_system_from_dp(path))
    shutil.rmtree(result_path)
    assert ~result_path.exists()
