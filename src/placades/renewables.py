from oemof.network import Node
from oemof.solph.flows import Flow


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

        super().__init__(label=label)

        if self.fix:
            self.outputs.update(
                {
                    self.bus_electricity: Flow(
                        fix=self.normalised_output,
                        nominal_capacity=self.peak_capacity,
                    )
                },
            )
        else:
            self.outputs.update(
                {
                    self.bus_electricity: Flow(
                        max=self.normalised_output,
                        nominal_capacity=self.peak_capacity,
                    )
                },
            )


class WindTurbine(Node):
    """Windkraftanlage basierend auf Source"""

    def __init__(
        self,
        label,
        bus_electricity,
        installed_capacity,
        normalised_output,
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
        normalised_output : iterable
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
        ...     normalised_output=[0.2, 0.7, 0.9, 0.4, 0.1],   # €/kW/a
        ... )
        >>> wind.fix
        True
        >>> wind2 = WindTurbine(
        ...     label="wind_farm_north",
        ...     bus_electricity=ebus,
        ...     installed_capacity=5000,  # 5 MW
        ...     normalised_output=[0.2, 0.7, 0.9, 0.4, 0.1],   # €/kW/a
        ...     fix=False,
        ... )
        >>> wind2.fix
        False
        """
        self.bus_electricity = bus_electricity
        self.nominal_capacity = installed_capacity
        self.wind_profile = normalised_output
        self.fix = fix
        if self.fix:
            outputs = (
                {
                    self.bus_electricity: Flow(
                        fix=self.wind_profile,
                        nominal_capacity=self.nominal_capacity,
                    )
                },
            )
        else:
            outputs = (
                {
                    self.bus_electricity: Flow(
                        max=self.wind_profile,
                        nominal_capacity=self.nominal_capacity,
                    )
                },
            )
        super().__init__(label=label, outputs=outputs)
