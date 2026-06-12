from unittest.mock import patch

import pytest

from oemof.eesyplan.importer import cop


def test_tespy_not_installed():
    with patch.object(cop, "Network", None):
        with pytest.raises(ModuleNotFoundError, match="TESPy is required"):
            cop.calculate_cop_tespy(10, 40)
