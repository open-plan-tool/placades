from oemof.network import Node
from oemof.solph.flows import Flow


class PvPlant(Node):
    def __init__(
        self,
        label,
        bus_electricity,
        pv_profile,
        age_installed=0,
        installed_capacity=0,
        capex_fix=1000,
        capex_var=1000,
        opex_fix=10,
        opex_var=0.01,
        lifetime=20,
        optimize_cap=False,
        maximum_capacity=None,
        renewable_asset=True,
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
        capex_var : float, default=1000
            Specific investment costs of the asset related to the
            installed capacity (CAPEX).
        opex_fix : float, default=10
            Specific operational and maintenance costs of the asset
            related to the installed capacity (OPEX_fix).
        opex_var : float, default=0.01
            Costs associated with a flow through/from the asset
            (OPEX_var or fuel costs).
        lifetime : int, default=20
            Number of operational years of the asset until it has to
            be replaced.
        optimize_cap : bool, default=False
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
        self.name = label
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_fix = capex_fix
        self.capex_var = capex_var
        self.opex_fix = opex_fix
        self.opex_var = opex_var
        self.lifetime = lifetime
        self.optimize_cap = optimize_cap
        self.maximum_capacity = maximum_capacity
        self.renewable_asset = renewable_asset
        self.input_timeseries = pv_profile

        outputs = {
            bus_electricity: Flow(
                fix=pv_profile,
                nominal_capacity=installed_capacity,
            )
        }

        super().__init__(label=label, outputs=outputs)


class PV(Node):
    def __init__(
        self,
        label,
        bus_electricity,
        peak_capacity,
        normalised_output,
        fix=True,
    ):
        """
        Short description

        Long description about the facade and how to use it.

        .. important ::
            Some important informatio about this facade.

        :Structure:
          *output*
            1. bus_electricity : electricity
            2. bus_heat : heat
          *input*
            1. bus_gas : gas
            2. bus_coal : coal

        Parameters
        ----------
        label : str or tuple
            Unique identifier of the instance.
        bus_electricity : oemof.solph.Bus
            Valid network bus with the carrier: electricity
        peak_capacity : float
            Capacity of the PV plant at its peak point.
        normalised_output : iterable
            Output time series, normalised to one unit of the peak capacity.

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> ebus = Bus(label="my_electricity_bus")
        >>> pv = PV(
        ...     label="my_pv",
        ...     bus_electricity=ebus,
        ...     peak_capacity=15,
        ...     normalised_output=[0.2, 0.4, 0.3]
        ... )
        >>> pv.fix
        True

        """
        self.peak_capacity = peak_capacity
        self.normalised_output = normalised_output
        self.bus_electricity = bus_electricity
        self.fix = fix

        if self.fix:
            fix = self.normalised_output
            vmax = None
        else:
            fix = None
            vmax = self.normalised_output

        outputs = {
            self.bus_electricity: Flow(
                max=vmax,
                fix=fix,
                nominal_capacity=self.peak_capacity,
            )
        }

        super().__init__(label=label, outputs=outputs)


class WindTurbine(Node):
    """Windkraftanlage basierend auf Source"""

    def __init__(
        self,
        label,
        bus_electricity,
        installed_capacity,
        wind_profile,
        fix=True,
    ):
        """
        Windkraftanlage (WKA) Facade

        Parameters
        ----------
        label : str or tuple
            Eindeutige Bezeichnung der WKA
        bus_electricity : oemof.solph.Bus
            Stromnetz-Bus
        installed_capacity : float
            Nennleistung der WKA in kW
        wind_profile : iterable
            Normalisierte Windleistung (0-1) als Zeitreihe
        fix : bool
            True = feste Erzeugung, False = flexible Abregelung möglich

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> ebus = Bus(label="my_electricity_bus")
        >>> wind = WindTurbine(
        ...     label="wind_farm_north",
        ...     bus_electricity=ebus,
        ...     installed_capacity=5000,  # 5 MW
        ...     wind_profile=[0.2, 0.7, 0.9, 0.4, 0.1],   # €/kW/a
        ... )
        >>> wind.fix
        True
        >>> wind2 = WindTurbine(
        ...     label="wind_farm_north",
        ...     bus_electricity=ebus,
        ...     installed_capacity=5000,  # 5 MW
        ...     wind_profile=[0.2, 0.7, 0.9, 0.4, 0.1],   # €/kW/a
        ...     fix=False,
        ... )
        >>> wind2.fix
        False
        """
        self.bus_electricity = bus_electricity
        self.installed_capacity = installed_capacity
        self.wind_profile = wind_profile
        self.fix = fix
        if self.fix:
            fix = self.wind_profile
            vmax = None
        else:
            fix = None
            vmax = self.wind_profile

        outputs = {
            self.bus_electricity: Flow(
                max=vmax,
                fix=fix,
                nominal_capacity=self.installed_capacity,
            )
        }
        super().__init__(label=label, outputs=outputs)
