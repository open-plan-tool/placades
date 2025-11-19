import pandas as pd
import pvlib


class PvPlant(Source):
    def __init__(
        self,
        label, #automatic/default?
        bus_out_electricity,
        pv_production_timeseries,
        age_installed=0,
        installed_capacity=0, #
        #capex_fix=None, should be removed if we don't have nonlinear objects
        capex_specific=None,
        #opex_fix=None, should be removed if we don't have nonlinear objects
        opex_specific=None,
        dispatch_costs=0,
        lifetime=25,
        expandable=True,
        maximum_capacity=999999999,
        project_data=None,
        fix=False,
    ):
        """
        Photovoltaic power plant for solar electricity generation.

        This class represents a photovoltaic plant that converts solar
        irradiation into electrical energy using photovoltaic panels.

        .. important ::
            This is a renewable energy source that contributes to the
            renewable share of the system.

        :Structure:
          *output*
            1. to_bus : Electricity

        Parameters
        ----------
        name : str
            Name of the asset.
        age_installed : int, default=0
            Number of years the asset has already been in operation.
        installed_capacity : float, default=0
            Already existing installed capacity.
        capex_fix : float, default=1000
            Specific investment costs of the asset related to the
            installed capacity (CAPEX).
        capex_specifc : float, default=1000
            Specific investment costs of the asset related to the
            installed capacity (CAPEX).
        opex_fix : float, default=10
            Specific operational and maintenance costs of the asset
            related to the installed capacity (OPEX_fix).
        opex_specific : float, default=0.01
            Costs associated with a flow through/from the asset
            (OPEX_var or fuel costs).
        lifetime : int, default=25
            Number of operational years of the asset until it has to
            be replaced.
        expandable : bool, default=True
            Choose if capacity optimization should be performed for
            this asset.
        maximum_capacity : float or None, default=None
            Maximum total capacity of an asset that can be installed
            at the project site.
        renewable_asset : bool, default=True
            Choose if this asset should be considered as renewable.
        input_timeseries : str or None, default=None
            Name of the csv file containing the input generation or
            demand timeseries.

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> ebus = Bus(label="electricity_bus")
        >>> my_pv = PvPlant(
        ...     name="rooftop_pv",
        ...     installed_capacity=100,
        ...     input_timeseries="solar_irradiation.csv",
        ... )

        """

        """
        PV-timeseries

        Creates a timeseries for the AC-power output of a 1 kWp PV-power plant
        The model is chosen to be simple and fast so the user does not need to wait
        Irradiance on plane is calculated for specified location, weather data and PV-Module orientation and multiplied with system efficieny
        """

        nv = create_invest_if_wanted(
            optimise_cap=expandable,
            capex_specific=capex_specific,
            capex_fix=capex_fix,
            opex_specific=opex_specific,
            opex_fix=opex_fix,
            lifetime=lifetime,
            age_installed=age_installed,
            existing_capacity=installed_capacity,
            project_data=project_data,
        )

        #
        if fix:
            fix = self.normalised_output
            vmax = None
        else:
            fix = None
            vmax = self.normalised_output

        outputs = {
            bus_electricity: Flow(
                fix=fix,
                max=vmax,
                nominal_capacity=nv,
            )
        }

        self.name = label
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_fix = capex_fix
        self.capex_specific = capex_specific
        self.opex_fix = opex_fix
        self.opex_specific = opex_specific
        self.dispatch_costs = dispatch_costs
        self.lifetime = lifetime
        self.optimize_cap = expandable
        self.maximum_capacity = maximum_capacity
        self.renewable_asset = True
        self.normalised_output = pv_production_timeseries
        self.fix = fix

        super().__init__(label=label, outputs=outputs)


def create_pv_production_timeseries(lat,lon,tz,times,weather_data,tilt=15,system_eff=0.85,azimuth=180,gcr=0.8,mounting_type="fix tilt"):

    #This is an internal function that can be called within the component.
    #The component has an expandable menu that can be called over: "Generate PV-timeseries":
    #Here additional inputparameters are visible: tilt,azimuth,gcr,mounting_type,system_efficiency
    #Under these inputs another button saying: "Generate-timeseries now" does start this function

    # create site location and times characteristics
    lat = lat  # project input
    lon = lon  # project input
    tz = 'Europe/Berlin'  # project input
    times = pd.date_range('2021-01-01', '2021-12-31', freq='1h', tz=tz)  # project input
    loc = pvlib.location.Location(latitude=lat, longitude=lon, tz=times.tz)

    solar_position = loc.get_solarposition(times)
    cs = loc.get_clearsky(times)

    # weather data should instead be used from PF script (this here is cs=clear sky so its not suitable)
    dni = cs['dni']  # =direct normal irradiation
    ghi = cs['ghi']  # =global horizontal irradiation
    dhi = cs['dhi']  # =diffuse horizontal irradiation

    axis_tilt = 0  # default
    azimuth = azimuth  # user input
    gcr = gcr  # user input
    max_angle = 60  # default
    tilt = tilt  # user input
    system_eff = system_eff  # user input = performance ratio (PR)
    albedo = 0.25  # default
    mounting_type = mounting_type  # user input dropdown menu with: fix tilt // tracker

    # Define mounting system
    if mounting_type == "fix tilt":
        mounting_system = pvlib.pvsystem.FixedMount(
            surface_tilt=tilt,
            surface_azimuth=azimuth)

    if mounting_type == 'tracker':
        mounting_system = pvlib.pvsystem.SingleAxisTrackerMount(
            axis_tilt=axis_tilt,
            axis_azimuth=azimuth,
            max_angle=max_angle,
            backtrack=True,
            gcr=gcr)

    # Calculate orientation of tracker
    orientation = mounting_system.get_orientation(
        solar_position['apparent_zenith'],
        solar_position['azimuth'])

    # Calculate irradiation on plane (no shading model)
    irrad = pvlib.irradiance.get_total_irradiance(
        surface_tilt=orientation['surface_tilt'],
        surface_azimuth=orientation['surface_azimuth'],
        solar_zenith=solar_position['apparent_zenith'],
        solar_azimuth=solar_position['azimuth'],
        dni=dni,
        ghi=ghi,
        dhi=dhi,
        dni_extra=None,
        airmass=None,
        albedo=0.25,
        surface_type=None,
        model='king',
        model_perez='allsitescomposite1990')

    # Calculate AC power with plain system_eff
    ac = irrad["poa_global"] * system_eff / 1000
    ac.fillna(0, inplace=True)
    return ac





