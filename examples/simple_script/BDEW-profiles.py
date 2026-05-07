import pandas as pd
import plotly.graph_objects as go

from oemof.eesyplan.importer import electricity_demand as el

PROFILE_TYPES_EL_BDEW_ABBR = el.PROFILE_TYPES_EL_BDEW_ABBR
PROFILE_TYPES_EL_BDEW = el.PROFILE_TYPES_EL_BDEW

fig = go.Figure()
times = pd.date_range(
    "2021-01-01 0:00", "2021-12-31 23:00", freq="1h", tz="Europe/Berlin"
)

for profile in PROFILE_TYPES_EL_BDEW:
    print(profile)
    demand = el.create_el_demand(
        profile_type=profile, annual_electricity_demand=3000, resolution="h"
    )

    y = demand.iloc[:, 0]

    fig.add_trace(go.Scatter(x=times, y=y, name=profile))

fig.show()
