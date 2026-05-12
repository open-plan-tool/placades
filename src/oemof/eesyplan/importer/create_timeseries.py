# import datetime
#
# import pandas as pd
# import pvlib
# from demandlib import bdew
#
#
# def apply_curtailability_if_wanted(timeseries, curtailable):
#     """
#     This function is called to define if a source is curtailable.
#
#     .. include:: docstring_parameter_description.rst
#     Arguments:
#     timeseries : timeseries
#         |timeseries|
#     curtailable:    bool
#         |curtailable|
#
#     """
#
#     if curtailable:
#         fix = None
#         vmax = timeseries
#     else:
#         fix = timeseries
#         vmax = 1
#     return fix, vmax
#
#
# def create_pv_production_timeseries(
#     lat,
#     lon,
#     # tz,
#     # times,
#     # weather_data,
#     tilt=15,
#     system_eff=0.85,
#     azimuth=180,
#     gcr=0.8,
#     mounting_type="fix tilt",
# ):
#     """
#     This is an internal function that can be called within the component.
#     The component has an expandable menu that can be called over:
#     "Generate PV-timeseries":
#     Here additional inputparameters are visible: tilt,azimuth,gcr,
#     mounting_type,system_efficiency
#     Under these inputs another button saying: "Generate-timeseries now" does
#     start this function
#
#     latitude: numeric
#         latitude of the PV-plant (decimal degrees)
#     longitude: numeric
#         longitude of the PV-plant (decimal degrees)
#     tilt: numeric
#         Tilt angle in degrees (90° is vertical)
#     system_efficiency: numeric
#         Performace Ratio of the system (usually around 0,8)
#     azimuth: numeric
#         Azimuth angle of the module orientation in degrees (North is 0°)
#         Azimut angle of the rotation-axis for tracking systems
#     gcr: numeric
#         Ground Coverage Ratio (Ratio of the module-area to the ground-area of
#         the modulefield)
#     mounting_type: string
#         "fix tilt" for static systems or "tracker" for 1-axis tracking systems
#
#
#     Example
#
#     >>> production_timeseries=create_pv_production_timeseries(
#     ...     lat=50.587031,
#     ...     lon=50.587031,
#     ...     tilt=15,
#     ...     system_eff=0.85,
#     ...     azimuth=180,
#     ...     gcr=0.8,
#     ...     mounting_type="fix tilt")
#     """
#
#     # create site location and times characteristics
#     lat = lat  # project input
#     lon = lon  # project input
#     tz = "Europe/Berlin"  # project input
#     times = pd.date_range(
#         "2021-01-01", "2021-12-31", freq="1h", tz=tz
#     )  # project input
#     loc = pvlib.location.Location(latitude=lat, longitude=lon, tz=times.tz)
#
#     solar_position = loc.get_solarposition(times)
#     cs = loc.get_clearsky(times)
#
#     # weather data should instead be used from PF script (this here is
#     # cs=clear sky so it is not suitable)
#     dni = cs["dni"]  # =direct normal irradiation
#     ghi = cs["ghi"]  # =global horizontal irradiation
#     dhi = cs["dhi"]  # =diffuse horizontal irradiation
#
#     axis_tilt = 0  # default
#     azimuth = azimuth  # user input
#     gcr = gcr  # user input
#     max_angle = 60  # default
#     tilt = tilt  # user input
#     system_eff = system_eff  # user input = performance ratio (PR)
#     # albedo = 0.25  # default
#     mounting_type = (
#         mounting_type  # user input dropdown menu with: fix tilt // tracker
#     )
#
#     # Define mounting system
#     if mounting_type == "fix tilt":
#         mounting_system = pvlib.pvsystem.FixedMount(
#             surface_tilt=tilt, surface_azimuth=azimuth
#         )
#     elif mounting_type == "tracker":
#         mounting_system = pvlib.pvsystem.SingleAxisTrackerMount(
#             axis_tilt=axis_tilt,
#             axis_azimuth=azimuth,
#             max_angle=max_angle,
#             backtrack=True,
#             gcr=gcr,
#         )
#     else:
#         raise NotImplementedError(f"Type {mounting_type} does not exist.")
#
#     # Calculate orientation of tracker
#     orientation = mounting_system.get_orientation(
#         solar_position["apparent_zenith"], solar_position["azimuth"]
#     )
#
#     # Calculate irradiation on plane (no shading model)
#     irrad = pvlib.irradiance.get_total_irradiance(
#         surface_tilt=orientation["surface_tilt"],
#         surface_azimuth=orientation["surface_azimuth"],
#         solar_zenith=solar_position["apparent_zenith"],
#         solar_azimuth=solar_position["azimuth"],
#         dni=dni,
#         ghi=ghi,
#         dhi=dhi,
#         dni_extra=None,
#         airmass=None,
#         albedo=0.25,
#         surface_type=None,
#         model="king",
#         model_perez="allsitescomposite1990",
#     )
#
#     # Calculate AC power with plain system_eff
#     ac = irrad["poa_global"] * system_eff / 1000
#     ac.fillna(0, inplace=True)
#     return ac
#
#
