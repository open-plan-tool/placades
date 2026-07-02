import shutil
import warnings
import zipfile
from pathlib import Path

import pytest

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


def test_zip_datapackage():
    dir_name = Path(Path(__file__).parent, "test_data", "openPlan_package")
    filename = Path(Path(__file__).parent, "test_data", "openPlan_package")
    shutil.make_archive(str(filename), "zip", dir_name)
    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=FutureWarning)
        result_path = Path(Path.home(), ".oemof", "test_eesyplan_567263FG")
        es.solve_energy_system_from_dp(filename, results_path=result_path)
        es.solve_energy_system_from_dp(filename.with_suffix(".zip"))
        mzip = zipfile.ZipFile(filename.with_suffix(".zip"), "a")
        mzip.write(Path(Path(__file__).parent, "test_data", "dp2.json"))
        mzip.close()
    with pytest.raises(ValueError, match="To many json files"):
        es.solve_energy_system_from_dp(filename.with_suffix(".zip"))

    Path(dir_name, "datapackage.graphml").unlink()
    filename.with_suffix(".zip").unlink()
