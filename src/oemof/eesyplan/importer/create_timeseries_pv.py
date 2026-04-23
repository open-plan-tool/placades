import numpy as np
import pandas as pd
import pvlib


def create_pv_production_timeseries(
    latitude,
    longitude,
    direct_irradiation_horizontal,
    diffuse_irradiation_horizontal,
    azimuth=180,
    tilt=15.0,
    system_eff=0.80,
    mounting_type="fix tilt",
    start_datetime="2021-01-01 0:00",
    tz="Europe/Berlin",
    gcr=0.5,
    max_angle=60,
    albedo=0.25,
):
    """
    This is an internal function based on PV-lib. It creates a simple
    AC-power-timeseries for a PV-plant with 1 kWp DC-Power.
    Based on the given horizontal direct and horizontal diffuse irradiances,
    the function calculates the irradiation on the defined tilted PV-Array.
    Losses are not calculated in detail but as a plain percentage with the
    given Performance Ratio / system efficiency (this includes shading).

    For the calculations the sun position and therefore a datetime for each
    timestep is needed. For this a start datetime is given for the first
    datapoint of the weatherdata. The length of the resulting timeseries is
    the automatically set to the length of the weatherdata.

    start_datetime : str in datetime format
        timestamp in , (default: "2021-01-01 0:00")
    tz : str in datetime format
        timezone, (default: "Europe/Berlin")
    direct_solar_wm2 : array-like with hourly timestep
        direct solar radiation on the horizontal plane in W/m²
    diffuse_solar_wm2 : array-like with hourly timestep
        diffuse solar radiation on the horizontal plane in W/m²
    tilt: numeric
        Tilt angle in degrees (0° is horizontal, 90° is vertical)
    azimuth: numeric
        for fix tilt: Azimuth angle of the module orientation in degrees
        (North is 0°, East is 90°...)
        for tracker: Azimuth angle of the rotation-axis for tracking systems
    system_efficiency: numeric
        Performace Ratio of the total PV-system (usually around 0,8)
    gcr: numeric
        Ground Coverage Ratio (Ratio of the module-area to the ground-area of
        the modulefield), only needed for tracker
    mounting_type: string
        "fix tilt" for static systems with one orientation,
        "fix tilt two directions back to back" for an east-west like system
        (only one orientation is given, the other one is set up automatically),
        "tracker" for 1-axis tracking systems
    albedo: numeric
        Reflection fraction of sunligth in the surrounding area (default: 0.25)
    max_angle: numeric
        Maximum tilt angle for tracking system (default: 60°). This value is
        only used for 'tracker' systems.


    Example
    >>> from oemof.eesyplan import WeatherData
    >>> weather_data = WeatherData()
    >>> weather_data.latitude = 52
    >>> weather_data.longitude = 13
    >>> weather_data.direct_solar_wm2=[100, 100, 100, 100, 100]
    >>> weather_data.diffuse_solar_wm2=[100, 100, 100, 100, 100]
    >>> pts = create_pv_production_timeseries(
    ...     latitude=weather_data.latitude,
    ...     longitude=weather_data.longitude,
    ...     direct_irradiation_horizontal=weather_data.direct_solar_wm2,
    ...     diffuse_irradiation_horizontal=weather_data.diffuse_solar_wm2,
    ...     azimuth=180,
    ...     tilt=30.0,
    ...     system_eff=1,
    ...     mounting_type="fix tilt",
    ...     start_datetime="2021-01-01 6:00",
    ...     tz="Europe/Berlin",
    ...     gcr=0.5,
    ...     max_angle=60,
    ...     albedo=0.25,
    ...     )
    >>> round(float(pts.sum()),1)
    1.2
    >>> production_timeseries_east_west=create_pv_production_timeseries(
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
    steps = len(direct_irradiation_horizontal)

    time_series = pd.date_range(
        start_datetime, periods=steps, freq="1h", tz=tz
    )

    loc = pvlib.location.Location(
        latitude=latitude,
        longitude=longitude,
        tz=time_series.tz,
    )
    direct_irradiation_horizontal = pd.Series(
        data=np.asarray(direct_irradiation_horizontal), index=time_series
    )
    diffuse_irradiation_horizontal = pd.Series(
        data=np.asarray(diffuse_irradiation_horizontal), index=time_series
    )

    # todo: How do we actually want to handle leap years?

    # for better calculation of DNI
    solar_position = loc.get_solarposition(
        time_series + pd.Timedelta(minutes=30)
    )
    solar_position.index = time_series

    # global (total) irradiation on horizonal plane
    ghi = direct_irradiation_horizontal + diffuse_irradiation_horizontal

    # default parameters the user cant change:
    axis_tilt = 0  # Tilt of the rotation axis of a tracking sytem

    # Define mounting system fix tilt
    match mounting_type:
        case "fix tilt" | "fix tilt two directions back to back":
            mounting_system = pvlib.pvsystem.FixedMount(
                surface_tilt=tilt, surface_azimuth=azimuth
            )
        case "tracker":
            mounting_system = pvlib.pvsystem.SingleAxisTrackerMount(
                axis_tilt=axis_tilt,
                axis_azimuth=azimuth,
                max_angle=max_angle,
                backtrack=True,
                gcr=gcr,
            )
        case _:  # pragma: no cover
            msg = (
                f"Mounting system '{mounting_type}' not recognized.\nUse: "
                f"'fix tilt', 'fix tilt two directions back to back' or "
                f"'tracker'. See Documentation for more information."
            )
            raise ValueError(msg)

    orientation = mounting_system.get_orientation(
        solar_position["apparent_zenith"], solar_position["azimuth"]
    )

    # Calculating the direct normal irradiance
    dni = pvlib.irradiance.dni(
        ghi,
        diffuse_irradiation_horizontal,
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
    irradiation = pvlib.irradiance.get_total_irradiance(
        surface_tilt=orientation["surface_tilt"],
        surface_azimuth=orientation["surface_azimuth"],
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
        dni=dni.astype(float),
        ghi=ghi.astype(float),
        dhi=diffuse_irradiation_horizontal.astype(float),
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
    irradiation["poa_direct"] = irradiation["poa_direct"].fillna(0)
    irradiation["poa_global"] = (
        irradiation["poa_direct"] + irradiation["poa_diffuse"]
    )

    # Total AC-Power is then simply calculated by the total system efficiency
    ac = irradiation["poa_global"] * system_eff / 1000
    ac.fillna(0, inplace=True)

    # Calculating the total irradiation on the indirectly defined tilted 2nd
    # plane in case of a two-direction b2b-system
    if mounting_type == "fix tilt two directions back to back":
        irradiation_back = pvlib.irradiance.get_total_irradiance(
            surface_tilt=tilt,
            surface_azimuth=((azimuth + 180) % 360),
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"],
            dni=dni.astype(float),
            ghi=ghi.astype(float),
            dhi=diffuse_irradiation_horizontal.astype(float),
            dni_extra=dni_extra,
            airmass=None,
            albedo=albedo,
            surface_type=None,
            model="isotropic",
            model_perez="allsitescomposite1990",
        )

        # In case of a two-direction b2b-system AC-Power is calculated by the
        # irradiation of both orientations
        irradiation_back["poa_direct"] = irradiation_back["poa_direct"].fillna(
            0
        )
        irradiation_back["poa_global"] = (
            irradiation_back["poa_direct"] + irradiation_back["poa_diffuse"]
        )

        ac2 = irradiation_back["poa_global"] * system_eff / 1000
        ac2.fillna(0, inplace=True)

        ac = (ac + ac2) / 2

    return ac.reset_index(drop=True)
