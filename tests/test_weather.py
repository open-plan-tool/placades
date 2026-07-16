from pathlib import Path

from oemof.eesyplan.weather import weather_data


def test_weather_file_import():
    path = Path(
        Path(__file__).parent,
        "test_data",
        "TRY2015_39065002972500_Jahr.dat",
    )
    w_obj = weather_data.WeatherData.from_try_file(path)
    assert round(w_obj.air_temperature_c.mean(), 3) == 9.921
    assert len(w_obj) == 8760
    assert round(w_obj.to_dict()["air_temperature_c"].mean(), 3) == 9.921


def test_weather_object():
    wd = weather_data.WeatherData()
    assert isinstance(wd, weather_data.WeatherData)


def test_weather_to_dict():
    wd = weather_data.WeatherData()
    d = wd.to_dict()
    assert isinstance(d, dict)
    assert "latitude" in d
    assert "longitude" in d
    assert "air_temperature_c" in d


def test_weather_len_before_data():
    wd = weather_data.WeatherData()
    try:
        len(wd)
    except TypeError:
        pass
