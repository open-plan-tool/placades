import warnings
from pathlib import Path

from oemof.datapackage import datapackage  # noqa
from oemof.solph import EnergySystem
from oemof.tools.debugging import ExperimentalFeatureWarning

from oemof.eesyplan.typemap import TYPEMAP

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)


def create_energy_system_from_dp(scenario_dir):
    """create energy system object from the datapackage"""

    # TODO load the typemap from information within the datapackage
    return EnergySystem.from_datapackage(
        Path(scenario_dir, "datapackage.json"),
        attributemap={},
        typemap=TYPEMAP,
    )
