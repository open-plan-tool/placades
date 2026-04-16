import pandas as pd
import plotly.graph_objects as go

from oemof.eesyplan import WeatherData
from oemof.eesyplan.importer import create_timeseries_pv as pv


weather_data = WeatherData.from_try_file("simple_script/data/TRY2015.dat")
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
production_timeseries_east_west = pv.create_pv_production_timeseries(
    latitude=weather_data.latitude,
    longitude=weather_data.longitude,
    direct_irradiation_horizontal=weather_data.direct_solar_wm2,
    diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
    azimuth=93,  # 273° added automatically
    tilt=45,
    system_eff=0.85,
    mounting_type="fix tilt two directions back to back",
)
production_timeseries_tracker = pv.create_pv_production_timeseries(
    latitude=weather_data.latitude,
    longitude=weather_data.longitude,
    direct_irradiation_horizontal=weather_data.direct_solar_wm2,
    diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
    azimuth=180,
    system_eff=0.85,
    mounting_type="tracker",
    gcr=0.5,
)

production_timeseries_east = pv.create_pv_production_timeseries(
    latitude=weather_data.latitude,
    longitude=weather_data.longitude,
    direct_irradiation_horizontal=weather_data.direct_solar_wm2,
    diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
    azimuth=93,  # 273° added automatically
    tilt=45,
    system_eff=0.85,
    mounting_type="fix tilt",
)
production_timeseries_west = pv.create_pv_production_timeseries(
    latitude=weather_data.latitude,
    longitude=weather_data.longitude,
    direct_irradiation_horizontal=weather_data.direct_solar_wm2,
    diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
    azimuth=273,  # 273° added automatically
    tilt=45,
    system_eff=0.85,
    mounting_type="fix tilt",
)

print(production_timeseries_fix.sum())
exit(0)

fig = go.Figure()

times = pd.date_range(
    "2021-01-01 0:00", "2021-12-31 23:00", freq="1h", tz="Europe/Berlin"
)

fig.add_trace(
    go.Scatter(x=times, y=production_timeseries_fix, name="fix tilt")
)

fig.add_trace(
    go.Scatter(x=times, y=production_timeseries_east_west, name="east west")
)

fig.add_trace(
    go.Scatter(x=times, y=production_timeseries_tracker, name="tracker")
)

fig.add_trace(go.Scatter(x=times, y=production_timeseries_east, name="east"))

fig.add_trace(go.Scatter(x=times, y=production_timeseries_west, name="west"))

fig.show()
