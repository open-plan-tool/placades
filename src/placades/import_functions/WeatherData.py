class WeatherData:
    """
    Container for TRY weather data.
    Attributes are empty until populated by import_TRY().
    Expects data-structure like the "TestReferenzJahr" which can be downloaded
    from DWD
    """

    def __init__(self):
        self.east_coordinate_m = []
        self.north_coordinate_m = []
        self.month = []
        self.day = []
        self.hour_mez = []
        self.air_temperature_C = []
        self.air_pressure_hPa = []
        self.wind_direction_deg = []
        self.wind_speed_ms = []
        self.cloud_cover_oktas = []
        self.water_vapor_gkg = []
        self.relative_humidity_percent = []
        self.direct_solar_Wm2 = []
        self.diffuse_solar_Wm2 = []
        self.atmospheric_radiation_Wm2 = []
        self.terrestrial_radiation_Wm2 = []
        self.quality_flag = []

    def __len__(self):
        return len(self.air_temperature_C)

    def to_dict(self):
        """serialize to dictionary"""
        return {k: getattr(self, k) for k in self.__dict__}


def import_TRJ(path):
    wd = WeatherData()

    with open(path, encoding="utf-8") as f:
        for line in f:
            # skip blank or comment/header lines
            if (
                line.strip() == ""
                or line.lstrip().startswith("*")
                or line.lstrip().startswith("RW")
            ):
                continue

            parts = line.split()

            # skip lines where first column is not numeric
            if not parts[0].replace("-", "").isdigit():
                continue

            if len(parts) < 17:
                continue

            wd.east_coordinate_m.append(int(parts[0]))
            wd.north_coordinate_m.append(int(parts[1]))
            wd.month.append(int(parts[2]))
            wd.day.append(int(parts[3]))
            wd.hour_mez.append(int(parts[4]))
            wd.air_temperature_C.append(float(parts[5]))
            wd.air_pressure_hPa.append(float(parts[6]))
            wd.wind_direction_deg.append(float(parts[7]))
            wd.wind_speed_ms.append(float(parts[8]))
            wd.cloud_cover_oktas.append(float(parts[9]))
            wd.water_vapor_gkg.append(float(parts[10]))
            wd.relative_humidity_percent.append(float(parts[11]))
            wd.direct_solar_Wm2.append(float(parts[12]))
            wd.diffuse_solar_Wm2.append(float(parts[13]))
            wd.atmospheric_radiation_Wm2.append(float(parts[14]))
            wd.terrestrial_radiation_Wm2.append(float(parts[15]))
            wd.quality_flag.append(int(parts[16]))

    return wd
