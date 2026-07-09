import json
import shutil
import warnings
from pathlib import Path

import pytest

from oemof.eesyplan.datapackage import energy_system as es
from oemof.tools.debugging import ExperimentalFeatureWarning

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)

DATA_PATH = Path(
    Path(__file__).parent, "test_data", "openPlan_every_component"
)

with Path.open(DATA_PATH / "datapackage.json") as f:
    _FULL_DATAPACKAGE = json.load(f)

_SHARED_RESOURCES = {"bus", "project", "profiles"}
_COMPONENT_TYPES = [
    resource["name"]
    for resource in _FULL_DATAPACKAGE["resources"]
    if resource["name"] not in _SHARED_RESOURCES
]


def _build_single_component_package(tmp_path, component_type):
    """Copy the fixture and slice its datapackage.json down to one
    component resource plus the shared bus/project/profiles resources,
    so a failure is attributable to a single component type."""
    package_path = tmp_path / component_type
    shutil.copytree(DATA_PATH, package_path)

    resources = [
        resource
        for resource in _FULL_DATAPACKAGE["resources"]
        if resource["name"] in _SHARED_RESOURCES | {component_type}
    ]
    with Path.open(package_path / "datapackage.json", "w") as f:
        json.dump({**_FULL_DATAPACKAGE, "resources": resources}, f)

    return package_path


@pytest.mark.parametrize("component_type", _COMPONENT_TYPES)
def test_component_builds_from_openplan_datapackage(tmp_path, component_type):
    """
    Assert that the OpenPlan components (instantiated through the
    openPlan_every_component datapackage) match the eesyplan API. On
    failure, a parameter has changed, needing to prompt a change on the
    OpenPlan side and/or add a FutureWarning.
    """
    package_path = _build_single_component_package(tmp_path, component_type)
    es.create_energy_system_from_dp(package_path)
