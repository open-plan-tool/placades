import pandas as pd
import plotly.graph_objects as go

import oemof.eesyplan.importer.heat_demand as heat
from oemof.eesyplan import WeatherData

times = pd.date_range(
    "2021-01-01 0:00", "2021-12-31 23:00", freq="1h", tz="Europe/Berlin"
)
weather_data = WeatherData.from_try_file("simple_script/data/TRY2015.dat")

heat_demand_EFH = heat.create_heat_demand(
    outdoor_temperature=weather_data.air_temperature_c,
    profile_type="Single-family house",
    annual_heat_demand=231,
    building_year=1992,
    wind_class="Not windy",
)

heat_demand_bakery = heat.create_heat_demand(
    outdoor_temperature=weather_data.air_temperature_c,
    profile_type="Bakery",
    annual_heat_demand=231,
    building_year=1992,
    wind_class="Not windy",
)

fig = go.Figure()

fig.add_trace(go.Scatter(x=times, y=heat_demand_EFH, name="EFH"))
fig.add_trace(go.Scatter(x=times, y=heat_demand_bakery, name="Bakery"))

fig.show()
