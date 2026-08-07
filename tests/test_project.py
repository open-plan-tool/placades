import pytest

from oemof.eesyplan.project import Project
from oemof.eesyplan.io import unzip_package


class TestProject:
    """Tests for the unzip_package function."""

    @pytest.fixture
    def basic_project(self):
        """Create a temporary zip file with sample content."""
        yield Project(name="tester", lifetime=20, tax=0, discount_factor=0.01)

    def test_basic_project(self, basic_project):
        """Verified with different annuity calculators."""
        assert (
            round(basic_project.calculate_epc(100, 20, 0, method="mvs"), 3)
            == 5.542
        )
        assert (
            round(basic_project.calculate_epc(100, 20, 0, method="oemof"), 3)
            == 5.542
        )

    def test_basic_project_with_tax(self, basic_project):
        """NOt verified!"""
        assert (
            round(
                basic_project.calculate_epc(
                    100, 20, age_installed=10, method="mvs"
                ),
                3,
            )
            == 5  # Todo: Wrong
        )
        basic_project.tax = 0.05
        assert (
            round(basic_project.calculate_epc(100, 20, 0, method="mvs"), 3)
            == 5  # Todo: Wrong
        )
