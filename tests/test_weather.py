import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from oemof.eesyplan.importer import weather_data


def test_weather_try_file_import():
    """The import of the test weather file failed."""
    path = Path(
        Path(__file__).parent, "test_data", "TRY2015_39065002972500_Jahr.dat"
    )
    w_obj = weather_data.WeatherData.from_try_file(path)
    assert round(w_obj.air_temperature_c.mean(), 3) == 9.921
    assert len(w_obj) == 8760
    assert round(w_obj.to_dict()["air_temperature_c"].mean(), 3) == 9.921


def test_weather_netcdf_file_import():
    """The import of the test weather file failed."""
    path = Path(
        Path(__file__).parent, "test_data", "era5_feedinlib_berlin_2017.nc"
    )
    w_obj = weather_data.WeatherData.from_era5_netcdf_file(
        path, latitude=52.8, longitude=13.1
    )
    assert round(w_obj.air_temperature_c.mean(), 3) == 9.976
    assert len(w_obj) == 8760
    assert round(w_obj.to_dict()["air_temperature_c"].mean(), 3) == 9.976


def test_rebuild_netcdf_file_from_api_data():
    """The import of the test weather file failed."""
    path = Path(
        Path(__file__).parent, "test_data", "api_weather_data_52.8_13.1.json"
    )
    with Path.open(path) as era5_json_data:
        d = json.load(era5_json_data)

    era5_variables_df = pd.DataFrame(d["variables"])
    dt_index = pd.date_range(**d["time"])
    lat = 52.8
    lon = 13.1

    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmpdir:
        netcdf_filepath = weather_data.__rebuild_netcdf_file_from_df(
            era5_variables_df, lat, lon, dt_index, tmpdir
        )

        assert Path(netcdf_filepath).exists()

        with xr.open_dataset(netcdf_filepath) as ds:
            assert float(ds.latitude.values) == lat
            assert float(ds.longitude.values) == lon

            # dimensions
            assert "time" in ds.dims
            assert ds.dims["time"] == len(dt_index)

            # variables from input dataframe are present
            for col in era5_variables_df.columns:
                assert col in ds.data_vars

            # selected attrs are attached
            assert ds["t2m"].attrs["units"] == "K"
            assert ds["sp"].attrs["units"] == "Pa"

            # sample values survived roundtrip
            assert ds["t2m"].values[0] == era5_variables_df["t2m"].iloc[0]
            assert ds["sp"].values[-1] == era5_variables_df["sp"].iloc[-1]


def test_weather_netcdf_file_import_from_api_data():
    """The import of the test weather file failed."""
    path = Path(
        Path(__file__).parent, "test_data", "era5_vars_from_api_52.8_13.1.nc"
    )

    lat = 52.8
    lon = 13.1
    w_obj = weather_data.WeatherData.from_era5_netcdf_file(
        path, latitude=lat, longitude=lon
    )

    assert round(w_obj.air_temperature_c.mean(), 3) == 10.824
    assert len(w_obj) == 8760
    assert round(w_obj.to_dict()["air_temperature_c"].mean(), 3) == 10.824


def test_weather_object():
    wd = weather_data.WeatherData()
    assert isinstance(wd, weather_data.WeatherData)


def test_extract_coordinates_from_era5():
    path = Path(
        Path(__file__).parent, "test_data", "era5_feedinlib_berlin_2017.nc"
    )
    coords = weather_data.extract_coordinates_from_era5(path)
    assert np.round(coords.x.unique(), 3).tolist() == [13.1, 13.35, 13.6]
    assert np.round(coords.y.unique(), 3).tolist() == [52.8, 52.55, 52.3]
