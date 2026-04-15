from pathlib import Path

import pandas as pd
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
