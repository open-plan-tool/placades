from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import xarray as xr
from feedinlib import era5
from pyproj import Transformer
from shapely.geometry import Point


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
    wind_speed_10m_ms : pd.Series or None
        Wind speed at 10 m above ground [m/s].
    wind_speed_100m_ms : pd.Series or None
        Wind speed at 100 m above ground [m/s].
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
    roughness_length_m : pd.Series or None
        Surface roughness length [m].
    global_solar_wm2 : pd.Series or None
        Global solar irradiance on horizontal plane [W/m²]. Negative = upward.
    quality_flag : pd.Series or None
        Quality flag regarding selection criteria.

    Notes
    -----
    Data structure follows the DWD "Testreferenzjahr" format.
    """

    def __init__(self):
        self.latitude = None
        self.longitude = None
        # TODO question: should we save the dt_index for netcdf files? Currently we drop it from the variable series and save it here once
        self.dt_index = None
        self.air_temperature_c = None
        self.air_pressure_hpa = None
        self.wind_direction_deg = None
        self.wind_speed_10m_ms = None
        self.wind_speed_100m_ms = (
            None  # added because given by era5 and why not?
        )
        self.cloud_cover_oktas = None
        self.water_vapor_gkg = None
        self.relative_humidity_percent = None
        self.direct_solar_wm2 = None
        self.diffuse_solar_wm2 = None
        self.atmospheric_radiation_wm2 = None
        self.terrestrial_radiation_wm2 = None
        self.roughness_length_m = (
            None  # added because required by windpowerlib modelchain
        )
        self.global_solar_wm2 = (
            None  # added because required by pvlib modelchain
        )
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
        wd.wind_speed_10m_ms = table["WG"]
        wd.cloud_cover_oktas = table["N"]
        wd.water_vapor_gkg = table["x"]
        wd.relative_humidity_percent = table["RF"]
        wd.direct_solar_wm2 = table["B"]
        wd.diffuse_solar_wm2 = table["D"]
        wd.atmospheric_radiation_wm2 = table["A"]
        wd.terrestrial_radiation_wm2 = table["E"]
        wd.quality_flag = table["IL"]

        return wd

    @classmethod
    def from_era5_netcdf_file(cls, path, latitude, longitude):
        """
        Create WeatherData object from ERA5 NetCDF file.

        Assumptions
        -----------
        - Standard ERA5 variable names are used.
        - We use all-sky direct radiation ('fdir'), not clear-sky ('cdir').
        - Diffuse shortwave is derived as global downward shortwave minus direct.
        - Terrestrial longwave is derived from net thermal radiation and downward
          thermal radiation, with negative = upward to match this class.
        - ERA5 radiation variables are assumed to be accumulations in J/m² and are
          converted to W/m² using the timestep length.
        """
        wd = cls()

        with xr.open_dataset(path) as ds:
            # select single area if era5 data has multiple grid points
            if "latitude" in ds.dims and "longitude" in ds.dims:
                ds = era5.select_area(ds, lat=latitude, lon=longitude)

            wd.latitude = latitude
            wd.longitude = longitude
            wd.dt_index = pd.to_datetime(ds["time"].values)
            dt_seconds = (wd.dt_index[1] - wd.dt_index[0]).total_seconds()

            def rad_flux(name):
                return ds[name] / dt_seconds

            # adapt units to wd object convention
            if "t2m" in ds:
                wd.air_temperature_c = (
                    (ds["t2m"] - 273.15).to_series().reset_index(drop=True)
                )

            if "sp" in ds:
                wd.air_pressure_hpa = (
                    (ds["sp"] / 100.0).to_series().reset_index(drop=True)
                )

            if "u10" in ds and "v10" in ds:
                u = ds["u10"]
                v = ds["v10"]
                wd.wind_speed_10m_ms = (
                    np.sqrt(u**2 + v**2)
                    .to_series()
                    .rename("wind_speed_10m_ms")
                    .reset_index(drop=True)
                )
                wd.wind_direction_deg = (
                    ((180.0 + np.degrees(np.arctan2(u, v))) % 360.0)
                    .to_series()
                    .rename("wind_direction_deg")
                    .reset_index(drop=True)
                )

            if "u100" in ds and "v100" in ds:
                wd.wind_speed_100m_ms = (
                    np.sqrt(ds["u100"] ** 2 + ds["v100"] ** 2)
                    .to_series()
                    .rename("wind_speed_100m_ms")
                    .reset_index(drop=True)
                )

            if "tcc" in ds:
                wd.cloud_cover_oktas = (
                    round(ds["tcc"] * 8.0).to_series().reset_index(drop=True)
                )

            if "fdir" in ds:
                wd.direct_solar_wm2 = (
                    rad_flux("fdir").to_series().reset_index(drop=True)
                )

            if "ssrd" in ds:
                wd.global_solar_wm2 = (
                    rad_flux("ssrd").to_series().reset_index(drop=True)
                )

            if "ssrd" in ds and "fdir" in ds:
                wd.diffuse_solar_wm2 = (
                    (rad_flux("ssrd") - rad_flux("fdir"))
                    .to_series()
                    .reset_index(drop=True)
                )

            if "strd" in ds:
                wd.atmospheric_radiation_wm2 = (
                    rad_flux("strd").to_series().reset_index(drop=True)
                )

            if "str" in ds and "strd" in ds:
                wd.terrestrial_radiation_wm2 = (
                    (rad_flux("str") - rad_flux("strd"))
                    .to_series()
                    .reset_index(drop=True)
                )

            if "fsr" in ds:
                wd.roughness_length_m = (
                    ds["fsr"].to_series().reset_index(drop=True)
                )

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


def __request_era5_df_from_api(api_host, lat, lon):
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

    dt_index = pd.date_range(**response_data["time"])
    return era5_variables_df, dt_index


def __rebuild_netcdf_file_from_df(
    era5_variables_df, lat, lon, dt_index, tmpdirname
):
    era5_units = {
        "d2m": {"units": "K", "long_name": "2 metre dewpoint temperature"},
        "e": {"units": "m", "long_name": "Evaporation (water equivalent)"},
        "fdir": {
            "units": "J/m²",
            "long_name": "Total sky direct solar radiation at surface",
        },
        "fsr": {"units": "1", "long_name": "Forecast surface roughness"},
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

    # export the rebuilt xarray to a temp nc file for creating the weatherdata object
    filepath = Path(tmpdirname) / f"era5_vars_{lat}_{lon}.nc"
    ds.to_netcdf(filepath)
    ds.close()
    return filepath


def extract_coordinates_from_era5(era5_netcdf_filename):
    """
    Extract all coordinates from a er5 netCDf-file and return them as a
    geopandas.Series
    """
    ds = xr.open_dataset(era5_netcdf_filename)

    # Extract all points from the netCDF-file:
    points = []
    for x in ds.longitude:
        for y in ds.latitude:
            points.append(Point(x, y))
    return gpd.GeoSeries(points)
