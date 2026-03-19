from pathlib import Path

import requests
import pandas as pd
import numpy as np
from pyproj import Transformer
import pvlib
from feedinlib import era5
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.pvsystem import PVSystem
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS


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


def request_era5_df(WEATHER_DATA_API_HOST, lat, lon):
    session = requests.Session()

    # TODO one shouldn't need a csrftoken for server to server
    # fetch CSRF token
    csrf_response = session.get(WEATHER_DATA_API_HOST + "get_csrf_token/")
    csrftoken = csrf_response.json()["csrfToken"]

    payload = {"latitude": lat, "longitude": lon}

    # headers = {"content-type": "application/json"}
    headers = {
        "X-CSRFToken": csrftoken,
        "Referer": WEATHER_DATA_API_HOST,
    }

    post_response = session.post(WEATHER_DATA_API_HOST, data=payload, headers=headers)
    # TODO here would be best to return a token but this requires celery on the weather_data API side
    # If we get a high request amount we might need to do so anyway
    if post_response.ok:
        response_data = post_response.json()
        df = pd.DataFrame(response_data["variables"])
        logger.info("The weather data API fetch worked successfully")

        if timeinfo is True:
            timeindex = response_data["time"]
    else:
        df = pd.DataFrame()
        logger.error("The weather data API fetch did not work")

    if timeinfo is False:
        return df
    else:
        return df, timeindex


def build_xarray_for_pvlib(lat, lon, dt_index):
    era5_units = {
        "d2m": {"units": "K", "long_name": "2 metre dewpoint temperature"},
        "e": {"units": "m", "long_name": "Evaporation (water equivalent)"},
        "fdir": {
            "units": "J/m²",
            "long_name": "Total sky direct solar radiation at surface",
        },
        "fsr": {"units": "1", "long_name": "Fraction of solar radiation"},
        "sp": {"units": "Pa", "long_name": "Surface pressure"},
        "ssrd": {"units": "J/m²", "long_name": "Surface solar radiation downwards"},
        "t2m": {"units": "K", "long_name": "2 metre temperature"},
        "tp": {"units": "m", "long_name": "Total precipitation"},
        "u10": {"units": "m/s", "long_name": "10 metre U wind component"},
        "u100": {"units": "m/s", "long_name": "100 metre U wind component"},
        "v10": {"units": "m/s", "long_name": "10 metre V wind component"},
        "v100": {"units": "m/s", "long_name": "100 metre V wind component"},
    }

    df = request_weather_data(lat, lon)
    df.index = dt_index
    df.index.name = "time"
    ds = df.to_xarray()

    # Attach scalar coords for the site
    ds = ds.assign_coords(latitude=float(lat), longitude=float(lon))

    # Add ERA5-style attributes expected by pvlib
    for var, attrs in era5_units.items():
        if var in ds:
            ds[var] = ds[var].assign_attrs(attrs)

    return ds

def prepare_weather_data(data_xr):
    df = era5.format_pvlib(data_xr)
    df = df.reset_index()
    df = df.rename(columns={"time": "dt", "latitude": "lat", "longitude": "lon"})
    df = df.set_index(["dt"])
    df["dni"] = np.nan
    lat = float(data_xr.latitude)
    lon = float(data_xr.longitude)
    solar_position = pvlib.solarposition.get_solarposition(
        time=df.index,
        latitude=lat,
        longitude=lon,
    )
    df["dni"] = pvlib.irradiance.dni(
        ghi=df["ghi"],
        dhi=df["dhi"],
        zenith=solar_position["apparent_zenith"],
    ).fillna(0)
    df = df.reset_index()
    df["dt"] = df["dt"] - pd.Timedelta("30min")
    df["dt"] = df["dt"].dt.tz_convert("UTC").dt.tz_localize(None)
    df.iloc[:, 3:] = (df.iloc[:, 3:] + 0.0000001).round(1)
    df.loc[:, "lon"] = df.loc[:, "lon"].round(3)
    df.loc[:, "lat"] = df.loc[:, "lat"].round(7)
    df = df.set_index("dt")
    return df
