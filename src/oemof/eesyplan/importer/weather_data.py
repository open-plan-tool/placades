from pathlib import Path

import pandas as pd
import pvlib
import requests
from feedinlib import era5
from pyproj import Transformer


class WeatherData:
    """
    Container for TRY (Test Reference Year) weather data.

    This class holds meteorological data from German DWD (Deutscher
    Wetterdienst) Test Reference Year files. Attributes are initialized as
    None and populated via the `from_try_file` class method.

    Attributes
    ----------
    air_temperature_c : pd.Series or None
        Air temperature at 2 m above ground [°C].
    air_pressure_hpa : pd.Series or None
        Air pressure at station height [hPa].
    wind_direction_deg : pd.Series or None
        Wind direction at 10 m above ground [degrees].
        Valid range: 0-360, 999 = variable.
    wind_speed_ms : pd.Series or None
        Wind speed at 10 m above ground [m/s].
    cloud_cover_oktas : pd.Series or None
        Cloud cover [oktas]. Valid range: 0-8, 9 = sky obscured.
    water_vapor_gkg : pd.Series or None
        Water vapor content, mixing ratio [g/kg].
    relative_humidity_percent : pd.Series or None
        Relative humidity at 2 m above ground [%].
        Valid range: 1-100.
    direct_solar_wm2 : pd.Series or None
        Direct solar irradiance on horizontal plane [W/m²].
        Positive = downward.
    diffuse_solar_wm2 : pd.Series or None
        Diffuse solar irradiance on horizontal plane [W/m²].
        Positive = downward.
    atmospheric_radiation_wm2 : pd.Series or None
        Atmospheric longwave radiation on horizontal plane [W/m²].
        Positive = downward.
    terrestrial_radiation_wm2 : pd.Series or None
        Terrestrial longwave radiation [W/m²]. Negative = upward.
    quality_flag : pd.Series or None
        Quality flag regarding selection criteria.

    Notes
    -----
    Data structure follows the DWD "Testreferenzjahr" format.
    """

    def __init__(self):
        self.latitude = None
        self.longitude = None
        self.air_temperature_c = None
        self.air_pressure_hpa = None
        self.wind_direction_deg = None
        self.wind_speed_ms = None
        self.cloud_cover_oktas = None
        self.water_vapor_gkg = None
        self.relative_humidity_percent = None
        self.direct_solar_wm2 = None
        self.diffuse_solar_wm2 = None
        self.atmospheric_radiation_wm2 = None
        self.terrestrial_radiation_wm2 = None
        self.quality_flag = None

    def __len__(self):
        return len(self.air_temperature_c)

    def to_dict(self):
        """serialize to dictionary"""
        return {k: getattr(self, k) for k in self.__dict__}

    @classmethod
    def from_try_file(cls, path):
        """
        Create Weather Data object from try file.

        Parameters
        ----------
        path

        Returns
        -------

        """
        wd = cls()

        table = try_file2df(path)

        wd.latitude, wd.longitude = lat_lon_from_lambert(
            table["RW"].iloc[0], table["HW"].iloc[0]
        )

        wd.air_temperature_c = table["t"]
        wd.air_pressure_hpa = table["p"]
        wd.wind_direction_deg = table["WR"]
        wd.wind_speed_ms = table["WG"]
        wd.cloud_cover_oktas = table["N"]
        wd.water_vapor_gkg = table["x"]
        wd.relative_humidity_percent = table["RF"]
        wd.direct_solar_wm2 = table["B"]
        wd.diffuse_solar_wm2 = table["D"]
        wd.atmospheric_radiation_wm2 = table["A"]
        wd.terrestrial_radiation_wm2 = table["E"]
        wd.quality_flag = table["IL"]

        return wd


def lat_lon_from_lambert(right, height):
    transformer = Transformer.from_crs(
        "EPSG:3034", "EPSG:4326", always_xy=True
    )
    return transformer.transform(right, height)


def try_file2df(file: Path):
    return pd.read_csv(
        filepath_or_buffer=file, skiprows=32, delimiter=r"\s+"
    ).iloc[1:, :]


def request_era5_df(api_host, lat, lon, timeinfo=False):
    """
    Request ERA5 weather data from the weather-data API.
    """
    session = requests.Session()

    csrf_response = session.get(api_host + "get_csrf_token/")
    csrf_token = csrf_response.json()["csrfToken"]

    payload = {"latitude": lat, "longitude": lon}
    headers = {
        "X-CSRFToken": csrf_token,
        "Referer": api_host,
    }

    post_response = session.post(api_host, data=payload, headers=headers)

    if not post_response.ok:
        raise RuntimeError("ERA5 weather data API fetch failed")

    response_data = post_response.json()
    era5_variables_df = pd.DataFrame(response_data["variables"])

    if timeinfo:
        dt_index = pd.date_range(**response_data["time"])
        return era5_variables_df, dt_index

    return era5_variables_df


def build_era5_xarray(era5_variables_df, lat, lon, dt_index):
    era5_units = {
        "d2m": {"units": "K", "long_name": "2 metre dewpoint temperature"},
        "e": {"units": "m", "long_name": "Evaporation (water equivalent)"},
        "fdir": {
            "units": "J/m²",
            "long_name": "Total sky direct solar radiation at surface",
        },
        "fsr": {"units": "1", "long_name": "Fraction of solar radiation"},
        "sp": {"units": "Pa", "long_name": "Surface pressure"},
        "ssrd": {
            "units": "J/m²",
            "long_name": "Surface solar radiation downwards",
        },
        "t2m": {"units": "K", "long_name": "2 metre temperature"},
        "tp": {"units": "m", "long_name": "Total precipitation"},
        "u10": {"units": "m/s", "long_name": "10 metre U wind component"},
        "u100": {"units": "m/s", "long_name": "100 metre U wind component"},
        "v10": {"units": "m/s", "long_name": "10 metre V wind component"},
        "v100": {"units": "m/s", "long_name": "100 metre V wind component"},
    }

    df = era5_variables_df.copy()
    df.index = dt_index
    df.index.name = "time"
    ds = df.to_xarray()

    # Attach scalar coords for the site
    ds = ds.assign_coords(latitude=float(lat), longitude=float(lon))

    # Assign ERA5 variable attributes to xarray dataset
    for var, attrs in era5_units.items():
        if var in ds:
            ds[var] = ds[var].assign_attrs(attrs)

    return ds


def _add_dni_from_ghi_dhi(
    era5_variables_df, latitude, longitude, zenith_col="apparent_zenith"
):
    """
    Return a copy of a pvlib input weather dataframe with a computed `dni` column.

    Requires:
    - DatetimeIndex
    - columns: `ghi`, `dhi`
    """
    if not isinstance(era5_variables_df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have a DatetimeIndex.")

    if (
        "ghi" not in era5_variables_df.columns
        or "dhi" not in era5_variables_df.columns
    ):
        raise ValueError("DataFrame must contain 'ghi' and 'dhi' columns.")

    df = era5_variables_df.copy()

    solar_position = pvlib.solarposition.get_solarposition(
        time=df.index,
        latitude=float(latitude),
        longitude=float(longitude),
    )

    df["dni"] = pvlib.irradiance.dni(
        ghi=df["ghi"],
        dhi=df["dhi"],
        zenith=solar_position[zenith_col],
    ).fillna(0)

    return df


def prepare_pvlib_weather_from_era5(era5_variables_ds):
    df = era5.format_pvlib(era5_variables_ds)
    df = df.reset_index()
    df = df.rename(
        columns={"time": "dt", "latitude": "lat", "longitude": "lon"}
    )
    df = df.set_index(["dt"])

    lat = float(era5_variables_ds.latitude)
    lon = float(era5_variables_ds.longitude)

    df = _add_dni_from_ghi_dhi(df, lat, lon)

    return df


def prepare_pvlib_weather_from_dwd(wd, dt_index):
    if wd.air_temperature_c is None or wd.wind_speed_ms is None:
        raise ValueError(
            "WeatherData must contain air_temperature_c and wind_speed_ms."
        )
    if wd.direct_solar_wm2 is None or wd.diffuse_solar_wm2 is None:
        raise ValueError(
            "WeatherData must contain direct_solar_wm2 and diffuse_solar_wm2."
        )
    if wd.latitude is None or wd.longitude is None:
        raise ValueError("WeatherData must contain latitude and longitude.")

    df = pd.DataFrame(
        {
            "temp_air": wd.air_temperature_c.astype(float),
            "wind_speed": wd.wind_speed_ms.astype(float),
            "dhi": wd.diffuse_solar_wm2.astype(float),
            "ghi": wd.direct_solar_wm2.astype(float)
            + wd.diffuse_solar_wm2.astype(float),
        }
    )

    df = _add_dni_from_ghi_dhi(df, wd.latitude, wd.longitude)
    df.index = dt_index
    df = df[["wind_speed", "temp_air", "ghi", "dhi", "dni"]]

    return df
