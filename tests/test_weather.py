import importlib
import logging
import sys
from pathlib import Path

from oemof.eesyplan.weather import weather_data


def test_weather_file_import():
    """The import of the test weather file failed."""
    path = Path(
        Path(__file__).parent, "test_data", "TRY2015_39065002972500_Jahr.dat"
    )
    w_obj = weather_data.WeatherData.from_try_file(path)
    assert round(w_obj.air_temperature_c.mean(), 3) == 9.921
    assert len(w_obj) == 8760
    assert round(w_obj.to_dict()["air_temperature_c"].mean(), 3) == 9.921


def test_weather_object():
    wd = weather_data.WeatherData()
    assert isinstance(wd, weather_data.WeatherData)


def test_import_without_pyproj(monkeypatch, caplog):
    weather_module = "oemof.eesyplan.weather.weather_data"
    monkeypatch.setitem(sys.modules, "pyproj", None)

    # force re-import so module-level try/except runs again
    sys.modules.pop(weather_module, None)

    with caplog.at_level(logging.WARNING):
        module = importlib.import_module("oemof.eesyplan.weather.weather_data")

    assert hasattr(module, "Transformer")
    assert module.Transformer.__module__ == weather_module
    assert "have to install extra dependencies" in caplog.text
