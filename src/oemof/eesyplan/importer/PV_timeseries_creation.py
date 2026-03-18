import pandas as pd
import pvlib


def create_pv_production_timeseries(
    # times,
    weather_data,
    azimuth,
    system_eff,
    mounting_type,
    tilt=15.0,
    gcr=1.0,
):
    """
    This is an internal function based on PV-lib. It creates a simple ac-power-timeseries for a PV-plant.
    Based on the given horizontal direct and horizontal diffuse irradiances, the function calculates the irradiation on the defined tilted PV-Array
    Losses are not calculated in detail but as a plain percentage (this includes shading)


    weather_data: .dat
        The weather data currently has to be in the format of a DWD-Reference year
    tilt: numeric
        Tilt angle in degrees (0° is horizontal, 90° is vertical)
    azimuth: numeric
        for fix tilt: Azimuth angle of the module orientation in degrees (North is 0°, East is 90°...)
        for tracker: Azimuth angle of the rotation-axis for tracking systems
    system_efficiency: numeric
        Performace Ratio of the total PV-system (usually around 0,8)
    gcr: numeric
        Ground Coverage Ratio (Ratio of the module-area to the ground-area of
        the modulefield), only needed for tracker
    mounting_type: string
        "fix tilt" for static systems with one orientation,
        "fix tilt two directions back to back" for an east-west like system (only one orientation is given),
        "tracker" for 1-axis tracking systems


    Example
    >>> from oemof.eesyplan import WeatherData
    >>> weather_data = WeatherData.from_try_file("examples/simple_dispatch/data/TRY2015.dat")
    >>> production_timeseries_fix=create_pv_production_timeseries(
    ...     weather_data=weather_data,
    ...     azimuth=180,
    ...     tilt=15,
    ...     system_eff=0.85,
    ...     mounting_type="fix tilt",
    ...     )
    >>> production_timeseries_east_west=create_pv_production_timeseries(
    ...     weather_data=weather_data,
    ...     azimuth=93, #273° added automatically
    ...     tilt=10,
    ...     system_eff=0.85,
    ...     mounting_type="fix tilt two directions back to back",
    ...     )
    >>> production_timeseries_tracker=create_pv_production_timeseries(
    ...     weather_data=weather_data,
    ...     azimuth=180,
    ...     system_eff=0.85,
    ...     mounting_type="tracker",
    ...     gcr = 0.5,
    ...     )
    """

    # create site location and times characteristics

    # todo: get time from project
    times = pd.date_range(
        "2021-01-01 0:00", "2021-12-31 23:00", freq="1h", tz="Europe/Berlin"
    )

    loc = pvlib.location.Location(
        latitude=weather_data.latitude,
        longitude=weather_data.longitude,
        tz=times.tz,
    )

    solar_position = loc.get_solarposition(
        times + pd.Timedelta(minutes=30)
    )  # todo change to general version (+ half the time resolution)
    solar_position.index = times

    dirhi = weather_data.direct_solar_wm2.copy().astype(float)
    diffhi = weather_data.diffuse_solar_wm2.copy().astype(float)
    dirhi.index = times[: len(dirhi)]
    diffhi.index = times[: len(diffhi)]
    ghi = dirhi + diffhi

    axis_tilt = 0
    max_angle = 60
    albedo = 0.25

    # Define mounting system
    if (
        mounting_type == "fix tilt"
        or mounting_type == "fix tilt two directions back to back"
    ):
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

    orientation = mounting_system.get_orientation(
        solar_position["apparent_zenith"], solar_position["azimuth"]
    )

    dni = pvlib.irradiance.dni(
        ghi,
        diffhi,
        solar_position["zenith"],
        dni_clear=None,
        clearsky_tolerance=1.1,
        zenith_threshold_for_zero_dni=85.0,
        zenith_threshold_for_clearsky_limit=80.0,
    )

    dni_extra = pvlib.irradiance.get_extra_radiation(
        times,
        solar_constant=1366.1,
        method="spencer",
        epoch_year=2020,
    )

    irrad = pvlib.irradiance.get_total_irradiance(
        surface_tilt=orientation["surface_tilt"],
        surface_azimuth=orientation["surface_azimuth"],
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
        dni=dni.astype(float),
        ghi=ghi.astype(float),
        dhi=diffhi.astype(float),
        dni_extra=dni_extra,
        airmass=None,
        albedo=albedo,
        surface_type=None,
        model="isotropic",
        model_perez="allsitescomposite1990",
    )

    if mounting_type == "fix tilt two directions back to back":
        irrad2 = pvlib.irradiance.get_total_irradiance(
            surface_tilt=tilt,
            surface_azimuth=((azimuth + 180) % 360),
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"],
            dni=dni.astype(float),
            ghi=ghi.astype(float),
            dhi=diffhi.astype(float),
            dni_extra=dni_extra,
            airmass=None,
            albedo=albedo,
            surface_type=None,
            model="isotropic",
            model_perez="allsitescomposite1990",
        )

    irrad["poa_direct"] = irrad["poa_direct"].fillna(0)
    irrad["poa_global"] = irrad["poa_direct"] + irrad["poa_diffuse"]

    ac = irrad["poa_global"] * system_eff / 1000
    ac.fillna(0, inplace=True)

    if mounting_type == "fix tilt two directions back to back":
        irrad2["poa_direct"] = irrad2["poa_direct"].fillna(0)
        irrad2["poa_global"] = irrad2["poa_direct"] + irrad2["poa_diffuse"]

        ac2 = irrad2["poa_global"] * system_eff / 1000
        ac2.fillna(0, inplace=True)

        ac = (ac + ac2) / 2

    return ac
