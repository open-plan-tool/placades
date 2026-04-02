import pandas as pd

from oemof.eesyplan.importer import PV_timeseries_creation as pv
from oemof.eesyplan.importer import weather_data as weather


def test_pv_timeseries_creation():
    """The import of the test weather file failed."""
    times = pd.date_range(
        "2019-01-01 03:00", "2020-01-01 01:00", freq="1h", tz="Europe/Berlin"
    )
    # can handle year changes and periods smaller than one year

    weather_data = weather.WeatherData.from_try_file(
        "examples/simple_dispatch/data/TRY2015.dat"
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
    assert round(production_timeseries_fix.sum(), 0) == 865
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
    assert round(production_timeseries_east_west.sum(), 0) == 796
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
    assert round(production_timeseries_tracker.sum(), 0) == 889
