import shutil
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from oemof.datapackage import datapackage  # noqa
from oemof.tools.debugging import ExperimentalFeatureWarning

from oemof.eesyplan import import_results
from oemof.eesyplan.datapackage import energy_system as es

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def test_simple_datapackage():
    path = Path(Path(__file__).parent, "test_data", "openPlan_package")
    results_path = Path(Path.home(), "openplan")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        result_path = es.solve_energy_system_from_dp(
            path, plot="graph", results_path=results_path
        )

    assert Path(path.parent, "openPlan_package.graphml").exists()
    Path(path.parent, "openPlan_package.graphml").unlink()
    import_results(path=result_path, es=es.create_energy_system_from_dp(path))
    shutil.rmtree(result_path)
    assert not result_path.exists()


@patch("oemof.eesyplan.datapackage.energy_system.ESGraphRenderer", None)
def test_visio_not_installed_trigger_helpful_error_message():
    dir_name = Path(Path(__file__).parent, "test_data", "openPlan_package")
    dummy_es = None
    with pytest.raises(
        ModuleNotFoundError,
        match="To use the plot function 'oemof-viso' must be installed",
    ):
        es.plot_es(dummy_es, dir_name)


def test_zip_datapackage():
    dir_name = Path(Path(__file__).parent, "test_data", "openPlan_package")
    filename = Path(Path(__file__).parent, "test_data", "openPlan_package")
    shutil.make_archive(str(filename), "zip", dir_name)
    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=FutureWarning)
        result_path = Path(Path.home(), ".oemof", "test_eesyplan_567263FG")
        es.solve_energy_system_from_dp(filename, results_path=result_path)
        es.solve_energy_system_from_dp(
            filename.with_suffix(".zip"), plot="graph"
        )
        mzip = zipfile.ZipFile(filename.with_suffix(".zip"), "a")
        mzip.write(Path(Path(__file__).parent, "test_data", "dp2.json"))
        mzip.close()
    with pytest.raises(ValueError, match="To many json files"):
        es.solve_energy_system_from_dp(filename.with_suffix(".zip"))
    Path(dir_name.parent, "openPlan_package.graphml").unlink()
    filename.with_suffix(".zip").unlink()
