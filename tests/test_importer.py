import importlib
import sys
from unittest.mock import patch

import pytest

from oemof.eesyplan.importer import cop


def test_tespy_not_installed():
    """Set Network to None."""
    with patch.object(cop, "Network", None):
        with pytest.raises(ModuleNotFoundError, match="TESPy is required"):
            cop.calculate_cop_tespy(10, 40)


def test_tespy_not_installed_via_import():
    """As if tespy would not exist."""
    with patch.dict(
        sys.modules,
        {
            "tespy": None,
            "tespy.components": None,
            "tespy.connections": None,
            "tespy.networks": None,
        },
    ):
        importlib.reload(cop)

        with pytest.raises(ModuleNotFoundError, match="TESPy is required"):
            cop.calculate_cop_tespy(10, 40)
