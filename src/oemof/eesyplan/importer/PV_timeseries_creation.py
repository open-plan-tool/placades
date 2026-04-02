import numpy as np
import pandas as pd
import pvlib


def create_pv_production_timeseries(
    time_series,
    latitude,
    longitude,
    direct_irradiation_horizontal,
    diffuse_irradiation_horizontal,
    azimuth,
    system_eff,
    mounting_type,
    tilt=15.0,
    gcr=1.0,
):
    """
    This is an internal function based on PV-lib. It creates a simple AC-power-timeseries for a PV-plant.
    Based on the given horizontal direct and horizontal diffuse irradiances, the function calculates the irradiation on the defined tilted PV-Array
    Losses are not calculated in detail but as a plain percentage (this includes shading)

    time_series: pandas.Series
        Time series (DatetimeIndex) of the times for which a production timesseries is to be created
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
    >>> times = pd.date_range("2021-01-01 0:00", "2021-12-31 23:00", freq="1h", tz="Europe/Berlin")
    >>> weather_data = WeatherData.from_try_file("examples/simple_dispatch/data/TRY2015.dat")
    >>> production_timeseries_fix=create_pv_production_timeseries(
    ...     times,
    ...     latitude=weather_data.latitude,
    ...     longitude=weather_data.longitude,
    ...     direct_irradiation_horizontal=weather_data.direct_solar_wm2,
    ...     diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
    ...     azimuth=180,
    ...     tilt=15,
    ...     system_eff=0.85,
    ...     mounting_type="fix tilt",
    ...     )
    >>> production_timeseries_east_west=create_pv_production_timeseries(
    ...     times,
    ...     latitude=weather_data.latitude,
    ...     longitude=weather_data.longitude,
    ...     direct_irradiation_horizontal=weather_data.direct_solar_wm2,
    ...     diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
    ...     azimuth=93, #273° added automatically
    ...     tilt=10,
    ...     system_eff=0.85,
    ...     mounting_type="fix tilt two directions back to back",
    ...     )
    >>> production_timeseries_tracker=create_pv_production_timeseries(
    ...     times,
    ...     latitude=weather_data.latitude,
    ...     longitude=weather_data.longitude,
    ...     direct_irradiation_horizontal=weather_data.direct_solar_wm2,
    ...     diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
    ...     azimuth=180,
    ...     system_eff=0.85,
    ...     mounting_type="tracker",
    ...     gcr = 0.5,
    ...     )
    """

    loc = pvlib.location.Location(
        latitude=latitude,
        longitude=longitude,
        tz=time_series.tz,
    )

    # if not isinstance(time_series, pd.DatetimeIndex):
    #    time_series = pd.DatetimeIndex(time_series)

    ts = (
        time_series.tz_localize(None)
        if time_series.tz is not None
        else time_series
    )

    # todo: How do we actually want to handle leap years?
    # if len(ts) > 8760:
    #    raise ValueError(
    #        "DWD reference year weather data only contains 8760 values"
    #    )

    # for better calculation of DNI
    solar_position = loc.get_solarposition(
        time_series + pd.Timedelta(minutes=30)
    )
    solar_position.index = time_series

    # Get Values from weather_data
    dirhi_vals = np.asarray(direct_irradiation_horizontal, dtype=float)
    diffhi_vals = np.asarray(diffuse_irradiation_horizontal, dtype=float)

    hour_of_year = (ts.dayofyear - 1) * 24 + ts.hour - 1

    dirhi = pd.Series(dirhi_vals[hour_of_year], index=time_series)
    diffhi = pd.Series(diffhi_vals[hour_of_year], index=time_series)

    ghi = dirhi + diffhi  # global (total) irradiation on horizonal plane

    # default parameters the user cant change:
    axis_tilt = 0  # Tilt of the rotation axis of a tracking sytem
    max_angle = 60  # Maximum tilt angle for tracking system (60° is standard for most systems)
    albedo = 0.25  # Reflection fraction of sunligth (25% is a typical value when not knowing better)

    # Define mounting system fix tilt
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

    # Calculating the direct normal irradiance
    dni = pvlib.irradiance.dni(
        ghi,
        diffhi,
        solar_position["zenith"],
        dni_clear=None,
        clearsky_tolerance=1.1,
        zenith_threshold_for_zero_dni=85.0,
        zenith_threshold_for_clearsky_limit=80.0,
    )

    # Calculating the extraterrestrial direct normal irradiance
    dni_extra = pvlib.irradiance.get_extra_radiation(
        time_series,
        solar_constant=1366.1,
        method="spencer",
        epoch_year=2020,
    )

    # Calculating the total irradiation on the defined tilted plane
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

    # Calculating the total irradiation on the indirectly defined tilted 2nd plane in case of a two-direction b2b-system
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

    # Currently some values fo the poa_direct and therefore poa_global will get
    # NA-values, so we ensure that instead these values are set to 0 and we
    # manually calculate the global irradiation
    irrad["poa_direct"] = irrad["poa_direct"].fillna(0)
    irrad["poa_global"] = irrad["poa_direct"] + irrad["poa_diffuse"]

    # Total AC-Power is then simply calculated by the total system efficiency
    ac = irrad["poa_global"] * system_eff / 1000
    ac.fillna(0, inplace=True)

    # In case of a two-direction b2b-system AC-Power is calculated by the
    # irradiation of both orientations
    if mounting_type == "fix tilt two directions back to back":
        irrad2["poa_direct"] = irrad2["poa_direct"].fillna(0)
        irrad2["poa_global"] = irrad2["poa_direct"] + irrad2["poa_diffuse"]

        ac2 = irrad2["poa_global"] * system_eff / 1000
        ac2.fillna(0, inplace=True)

        ac = (ac + ac2) / 2

    return ac.reset_index(drop=True)
