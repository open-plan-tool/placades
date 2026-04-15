from pathlib import Path

import pandas as pd
import pytest

from oemof.eesyplan.importer import create_timeseries_pv as pv
from oemof.eesyplan.weather import weather_data as weather


def test_pv_timeseries_creation():
    """The import of the test weather file failed."""
    times = pd.date_range(
        "2019-01-01 03:00", "2020-01-01 01:00", freq="1h", tz="Europe/Berlin"
    )
    # can handle year changes and periods smaller than one year

    weather_data = weather.WeatherData.from_try_file(
        Path(
            Path(__file__).parent,
            "test_data",
            "TRY2015_39065002972500_Jahr.dat",
        )
    )

    production_timeseries_fix = pv.create_pv_production_timeseries(
        times,
        latitude=weather_data.latitude,
        longitude=weather_data.longitude,
        direct_irradiation_horizontal=weather_data.direct_solar_wm2,
        diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
        azimuth=180,
        tilt=15,
        system_eff=0.85,
        mounting_type="fix tilt",
    )
    assert round(production_timeseries_fix.sum(), 0) == 933
    production_timeseries_east_west = pv.create_pv_production_timeseries(
        times,
        latitude=weather_data.latitude,
        longitude=weather_data.longitude,
        direct_irradiation_horizontal=weather_data.direct_solar_wm2,
        diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
        azimuth=180,  # 0° added automatically
        tilt=15,
        system_eff=0.85,
        mounting_type="fix tilt two directions back to back",
    )
    assert round(production_timeseries_east_west.sum(), 0) == 848
    production_timeseries_tracker = pv.create_pv_production_timeseries(
        times,
        latitude=weather_data.latitude,
        longitude=weather_data.longitude,
        direct_irradiation_horizontal=weather_data.direct_solar_wm2,
        diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
        azimuth=180,
        system_eff=0.85,
        mounting_type="tracker",
        gcr=0.7,
    )
    assert round(production_timeseries_tracker.sum(), 0) == 956
    with pytest.raises(ValueError, match="Mounting system 'no_type' not"):
        pv.create_pv_production_timeseries(
            times,
            latitude=weather_data.latitude,
            longitude=weather_data.longitude,
            direct_irradiation_horizontal=weather_data.direct_solar_wm2,
            diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
            azimuth=180,
            system_eff=0.85,
            mounting_type="no_type",
            gcr=0.7,
        )
