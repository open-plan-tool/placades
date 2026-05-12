from pathlib import Path

import pytest

from oemof.eesyplan.importer import create_timeseries_pv as pv
from oemof.eesyplan.weather import weather_data as weather


@pytest.fixture
def weather_data():
    return weather.WeatherData.from_try_file(
        Path(
            Path(__file__).parent,
            "test_data",
            "TRY2015_39065002972500_Jahr.dat",
        )
    )


def test_pv_timeseries_fix_tilt(weather_data):
    """The import of the test weather file failed."""

    production_timeseries_fix = pv.create_pv_production_timeseries(
        latitude=weather_data.latitude,
        longitude=weather_data.longitude,
        direct_irradiation_horizontal=weather_data.direct_solar_wm2,
        diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
        azimuth=180,
        tilt=15,
        system_eff=0.85,
        mounting_type="fix tilt",
    )
    assert round(production_timeseries_fix.sum(), 0) == 936


def test_pv_timeseries_first_half(weather_data):
    production_timeseries_fix_half = pv.create_pv_production_timeseries(
        latitude=weather_data.latitude,
        longitude=weather_data.longitude,
        direct_irradiation_horizontal=weather_data.direct_solar_wm2[:4343],
        diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2[:4343],
        azimuth=180,  # 273° added automatically
        tilt=15,
        system_eff=0.85,
        mounting_type="fix tilt",
    )
    assert len(production_timeseries_fix_half) == 4343
    assert round(production_timeseries_fix_half.sum(), 0) == 502


def test_pv_timeseries_second_half(weather_data):
    production_timeseries_fix_half = pv.create_pv_production_timeseries(
        start_datetime="2021-07-01 0:00",
        latitude=weather_data.latitude,
        longitude=weather_data.longitude,
        direct_irradiation_horizontal=weather_data.direct_solar_wm2[4343:],
        diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2[4343:],
        azimuth=180,  # 273° added automatically
        tilt=15,
        system_eff=0.85,
        mounting_type="fix tilt",
    )
    assert len(production_timeseries_fix_half) == 4417
    assert round(production_timeseries_fix_half.sum(), 0) == 434


def test_pv_timeseries_back_to_back(weather_data):
    production_timeseries_east_west = pv.create_pv_production_timeseries(
        latitude=weather_data.latitude,
        longitude=weather_data.longitude,
        direct_irradiation_horizontal=weather_data.direct_solar_wm2,
        diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
        azimuth=180,  # 0° added automatically
        tilt=15,
        system_eff=0.85,
        mounting_type="fix tilt two directions back to back",
    )
    assert round(production_timeseries_east_west.sum(), 0) == 850


def test_pv_timeseries_tracker(weather_data):
    production_timeseries_tracker = pv.create_pv_production_timeseries(
        latitude=weather_data.latitude,
        longitude=weather_data.longitude,
        direct_irradiation_horizontal=weather_data.direct_solar_wm2,
        diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
        azimuth=180,
        system_eff=0.85,
        mounting_type="tracker",
        gcr=0.7,
    )
    assert round(production_timeseries_tracker.sum(), 0) == 961


def test_pv_timeseries_wrong_type(weather_data):
    with pytest.raises(ValueError, match="Mounting system 'no_type' not"):
        pv.create_pv_production_timeseries(
            latitude=weather_data.latitude,
            longitude=weather_data.longitude,
            direct_irradiation_horizontal=weather_data.direct_solar_wm2,
            diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
            azimuth=180,
            system_eff=0.85,
            mounting_type="no_type",
            gcr=0.7,
        )
