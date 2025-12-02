def create_pv_production_timeseries(
    lat,
    lon,
    # tz,
    # times,
    # weather_data,
    tilt=15,
    system_eff=0.85,
    azimuth=180,
    gcr=0.8,
    mounting_type="fix tilt",
):
    """
    This is an internal function that can be called within the component.
    The component has an expandable menu that can be called over:
    "Generate PV-timeseries":
    Here additional inputparameters are visible: tilt,azimuth,gcr,
    mounting_type,system_efficiency
    Under these inputs another button saying: "Generate-timeseries now" does
    start this function
    """

    # create site location and times characteristics
    lat = lat  # project input
    lon = lon  # project input
    tz = "Europe/Berlin"  # project input
    times = pd.date_range(
        "2021-01-01", "2021-12-31", freq="1h", tz=tz
    )  # project input
    loc = pvlib.location.Location(latitude=lat, longitude=lon, tz=times.tz)

    solar_position = loc.get_solarposition(times)
    cs = loc.get_clearsky(times)

    # weather data should instead be used from PF script (this here is
    # cs=clear sky so it is not suitable)
    dni = cs["dni"]  # =direct normal irradiation
    ghi = cs["ghi"]  # =global horizontal irradiation
    dhi = cs["dhi"]  # =diffuse horizontal irradiation

    axis_tilt = 0  # default
    azimuth = azimuth  # user input
    gcr = gcr  # user input
    max_angle = 60  # default
    tilt = tilt  # user input
    system_eff = system_eff  # user input = performance ratio (PR)
    # albedo = 0.25  # default
    mounting_type = (
        mounting_type  # user input dropdown menu with: fix tilt // tracker
    )

    # Define mounting system
    if mounting_type == "fix tilt":
        mounting_system = pvlib.pvsystem.FixedMount(
            surface_tilt=tilt, surface_azimuth=azimuth
        )
    elif mounting_type == "tracker":
        mounting_system = pvlib.pvsystem.SingleAxisTrackerMount(
            axis_tilt=axis_tilt,
            axis_azimuth=azimuth,
            max_angle=max_angle,
            backtrack=True,
            gcr=gcr,
        )
    else:
        raise NotImplementedError(f"Type {mounting_type} does not exist.")

    # Calculate orientation of tracker
    orientation = mounting_system.get_orientation(
        solar_position["apparent_zenith"], solar_position["azimuth"]
    )

    # Calculate irradiation on plane (no shading model)
    irrad = pvlib.irradiance.get_total_irradiance(
        surface_tilt=orientation["surface_tilt"],
        surface_azimuth=orientation["surface_azimuth"],
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
        dni=dni,
        ghi=ghi,
        dhi=dhi,
        dni_extra=None,
        airmass=None,
        albedo=0.25,
        surface_type=None,
        model="king",
        model_perez="allsitescomposite1990",
    )

    # Calculate AC power with plain system_eff
    ac = irrad["poa_global"] * system_eff / 1000
    ac.fillna(0, inplace=True)
    return ac


#
# from demandlib import bdew
# def create_heat_demand(timeframe,
# outdoor_temperature,
# profile_type,annual_heat_demand,building_year,wind_class=0):
#
#     match wind_class:
#         case "not windy":
#             wind_class=0
#         case "windy":
#             wind_class=1
#
#     if profile_type != 'residential':
#         building_class = 0
#     else:
#         match building_year:
#             case y if y <= 1918:
#                 building_class = 1
#             case y if 1919 <= y <= 1948:
#                 building_class = 2
#             case y if 1949 <= y <= 1957:
#                 building_class = 3
#             case y if 1958 <= y <= 1968:
#                 building_class = 4
#             case y if 1969 <= y <= 1978:
#                 building_class = 5
#             case y if 1979 <= y <= 1983:
#                 building_class = 6
#             case y if 1984 <= y <= 1994:
#                 building_class = 7
#             case y if 1995 <= y <= 1999:
#                 building_class = 8
#             case y if 2000 <= y <= 2006:
#                 building_class = 9
#             case y if 2007 <= y <= 2010:
#                 building_class = 10
#             case y if y >= 2011:
#                 building_class = 11
#
#     match profile_type:
#         case 'single-family house':
#             profile_type = 'EFH'
#         case 'apartment building':
#             profile_type = 'MFH'
#         case 'Commerce/Services general':
#             profile_type = 'GHD'
#         case 'restaurants':
#             profile_type = 'GGA'
#         case 'retail and wholesale':
#             profile_type = 'GBH'
#         case 'metal and automotive':
#             profile_type = 'GMK'
#         case 'household-like business enterprises':
#             profile_type = 'GMF'
#         case 'accommodation':
#             profile_type = 'GBH'
#         case 'Local authorities, credit institutions and insurancecompanies':
#             profile_type = 'GKO'
#         case 'other operational services':
#             profile_type = 'GBD'
#         case 'laundries, dry cleaning':
#             profile_type = 'GWA'
#         case 'horticulture':
#             profile_type = 'GGB'
#         case 'bakery':
#             profile_type = 'GBA'
#         case 'paper and printing':
#             profile_type = 'GPD'
#
#     holidays = { #ToDo: Create table based on location of project
#         datetime.date(2010, 5, 24): "Whit Monday",
#         datetime.date(2010, 4, 5): "Easter Monday",
#         datetime.date(2010, 5, 13): "Ascension Thursday",
#         datetime.date(2010, 1, 1): "New year",
#         datetime.date(2010, 10, 3): "Day of German Unity",
#         datetime.date(2010, 12, 25): "Christmas Day",
#         datetime.date(2010, 5, 1): "Labour Day",
#         datetime.date(2010, 4, 2): "Good Friday",
#         datetime.date(2010, 12, 26): "Second Christmas Day",
#     }
#
#     demand_profile = bdew.HeatBuilding(
#         timeframe.index,
#         holidays=holidays,
#         temperature=outdoor_temperature,
#         shlp_type=profile_type,
#         building_class=building_class,
#         wind_class=wind_class,
#         annual_heat_demand=annual_heat_demand,
#         name="",
#     ).get_bdew_profile()
#
#     return demand_profile
