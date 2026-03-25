import tempfile
import zipfile
from pathlib import Path
from shutil import rmtree
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from oemof.eesyplan.importer import heat_demand as heat
from oemof.eesyplan.importer import weather_data as weather


def create_test_heat_demand_data(periods=48, seed=42):
    """Create test heat demand data with random values using a seed"""
    np.random.seed(seed)
    dates = pd.date_range(start="2022-01-01", periods=periods, freq="h")
    values = np.random.uniform(low=1.0, high=3.5, size=periods)
    df = pd.DataFrame({"Gesamtsumme": values}, index=dates)
    return df


@pytest.fixture
def heat_demand_zip_file():
    """Create a temporary zip file with test heat demand data."""
    tmp_path = tempfile.TemporaryDirectory()

    # Create test data with fixed seed
    df = create_test_heat_demand_data(periods=48, seed=42)

    internal_path = Path("TestHeat", "Netz", "Tabelle_Netz1.xlsx")
    excel_path = Path(tmp_path.name, internal_path)
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(Path(excel_path), sheet_name="Lastprofil")
    zip_path = Path(tmp_path.name, "test_heat.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(
            Path(tmp_path.name, internal_path), arcname=str(internal_path)
        )
    rmtree(excel_path.parent.parent)

    yield zip_path

    tmp_path.cleanup()
    assert ~Path(tmp_path.name).exists()


def test_f_heat_importer_with_network_parameter(heat_demand_zip_file):
    """Test heat demand import with explicit network parameter."""
    df = heat.import_heat_demand_f_heat(heat_demand_zip_file, "Netz1")
    # Expected sum with seed=42 and 48 periods
    assert round(df.sum(), 2) == 101.91


def test_f_heat_importer_with_mocked_select_value(heat_demand_zip_file):
    """Test heat demand import with mocked select_value."""
    with patch(
        "oemof.eesyplan.importer.heat_demand.select_value"
    ) as mock_select_value:
        mock_select_value.return_value = "Netz1"
        df = heat.import_heat_demand_f_heat(heat_demand_zip_file)

    assert round(df.sum(), 2) == 101.91
    mock_select_value.assert_called_once()


PROFILE_TYPES_HEAT_BDEW = heat.PROFILE_TYPES_HEAT_BDEW
WIND_CLASS = ["Windy", "Not windy"]


@pytest.mark.parametrize("profile_type", PROFILE_TYPES_HEAT_BDEW)
@pytest.mark.parametrize("wind_class", WIND_CLASS)
def test_heat_demand_profile_by_bdew(profile_type, wind_class):
    weather_data = weather.WeatherData.from_try_file(
        "examples/simple_script/data/TRY2015.dat"
    )
    heat_demand = heat.create_heat_demand(
        outdoor_temperature=weather_data.air_temperature_c,
        profile_type=profile_type,
        annual_heat_demand=231,
        building_year=1992,
        wind_class=wind_class,
    )
    assert round(heat_demand.sum(), 0) == 231
