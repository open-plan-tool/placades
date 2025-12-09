from pathlib import Path

from placades.import_functions.WeatherData import import_TRJ


def main():
    filename = Path(Path(__file__).parent, "data/TRY2015.dat")
    weather_data = import_TRJ(filename)
    for k, v in vars(weather_data).items():
        if isinstance(v, list):
            print(f"{k}: list[{len(v)}]")
        else:
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
