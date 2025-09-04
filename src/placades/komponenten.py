from oemof.solph import Bus
from oemof.solph import Facade
from oemof.solph.components import Converter
from oemof.solph.components import GenericStorage
from oemof.solph.flows import Flow


class CHP(Facade):
    """Blockheizkraftwerk (BHKW) basierend auf Converter"""

    def __init__(
        self,
        label,
        bus_gas,
        bus_electricity,
        bus_heat,
        electrical_capacity=None,
        electrical_efficiency=0.35,
        thermal_efficiency=0.50,
        opex=0,
    ):
        """
        Blockheizkraftwerk (BHKW) Facade

        Parameters
        ----------
        label : str or tuple
            Eindeutige Bezeichnung des BHKW
        bus_gas : oemof.solph.Bus
            Gas-Bus (Input)
        bus_electricity : oemof.solph.Bus
            Strom-Bus (Output)
        bus_heat : oemof.solph.Bus
            Wärme-Bus (Output)
        electrical_capacity : float, optional
            Elektrische Nennleistung in kW
        electrical_efficiency : float
            Elektrischer Wirkungsgrad (default: 35%)
        thermal_efficiency : float
            Thermischer Wirkungsgrad (default: 50%)
        opex : float, optional
            Betriebskosten in €/kWh_el, alle Arten von spezifischen Kosten
            bezogen auf die Stromproduktion. Auch zusätzliche Abgaben auf
            z.B. Gas können über die Wirkungsgrade umgerechnet und damit auf
            die Stromproduktion umgerechnet werden

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> electricity_bus = Bus(label="my_electricity_bus")
        >>> heat_bus = Bus(label="my_heat_bus")
        >>> gas_bus = Bus(label="my_gas_bus")
        >>> chp = CHP(
        ...     label="chp_plant",
        ...     bus_gas=gas_bus,
        ...     bus_electricity=electricity_bus,
        ...     bus_heat=heat_bus,
        ...     electrical_capacity=1000,  # 1 MW elektrisch
        ...     electrical_efficiency=0.4,
        ...     thermal_efficiency=0.5,
        ... )
        """
        if electrical_efficiency + thermal_efficiency > 1.0:
            raise ValueError("Gesamtwirkungsgrad kann nicht > 100% sein")
        self.bus_gas = bus_gas
        self.bus_electricity = bus_electricity
        self.bus_heat = bus_heat
        self.electrical_capacity = electrical_capacity
        self.electrical_efficiency = electrical_efficiency
        self.thermal_efficiency = thermal_efficiency
        # Todo: Worauf beziehen sich die variablen Kosten? Wahrscheinlich auf
        #  Strom, denn auch die Max Leistung wurde für Strom angegeben.
        self.variable_costs = opex
        super().__init__(label=label, facade_type=type(self))

    def define_subnetwork(self):
        self.subnode(
            Converter,
            inputs={self.bus_gas: Flow()},
            outputs={
                self.bus_electricity: Flow(
                    nominal_capacity=self.electrical_capacity,
                    variable_costs=self.variable_costs,
                ),
                self.bus_heat: Flow(),
            },
            conversion_factors={
                self.bus_electricity: self.electrical_efficiency,
                self.bus_heat: self.thermal_efficiency,
            },
            label="chp_converter",
        )


class Battery(Facade):
    """Batteriespeicher basierend auf GenericStorage"""

    def __init__(
        self,
        label,
        bus_electricity,
        storage_capacity,
        max_charge_rate=1.0,  # C-Rate
        max_discharge_rate=1.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        self_discharge_rate=0.001,  # %/h
        capex_capacity=None,  # €/kWh
        capex_power=None,  # €/kW
        opex=None,
        initial_storage_level=0.5,
    ):
        """
        Batteriespeicher Facade

        Parameters
        ----------
        label : str or tuple
            Eindeutige Bezeichnung der Batterie
        bus_electricity : oemof.solph.Bus
            Strom-Bus für Laden/Entladen
        storage_capacity : float
            Speicherkapazität in kWh
        max_charge_rate : float
            Maximale Laderate als C-Rate (default: 1C = 1h Vollladung)
        max_discharge_rate : float
            Maximale Entladerate als C-Rate
        charge_efficiency : float
            Ladewirkungsgrad (default: 95%)
        discharge_efficiency : float
            Entladewirkungsgrad (default: 95%)
        self_discharge_rate : float
            Selbstentladung pro Stunde in % (default: 0.1%/h)
        capex_capacity : float, optional
            Investitionskosten Speicher in €/kWh
        capex_power : float, optional
            Investitionskosten Leistung in €/kW
        opex : float, optional
            Betriebskosten in €/kWh Durchsatz
        initial_storage_level : float
            Anfänglicher Ladestand (0-1)

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> electricity_bus = Bus(label="my_electricity_bus")
        >>> battery = Battery(
        ...     label="home_battery",
        ...     bus_electricity=electricity_bus,
        ...     storage_capacity=10,  # 10 kWh
        ...     max_charge_rate=0.5,  # 0.5C = 2h Vollladung
        ...     max_discharge_rate=1.0,  # 1C = 1h Entladung
        ...     capex_capacity=400,  # €/kWh
        ...     capex_power=200      # €/kW
        ... )
        """
        self.bus_electricity = bus_electricity
        self.storage_capacity = storage_capacity
        self.max_charge_rate = max_charge_rate
        self.max_discharge_rate = max_discharge_rate
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency
        self.self_discharge_rate = self_discharge_rate
        self.capex_capacity = capex_capacity
        self.capex_power = capex_power
        # Todo: Worauf beziehen sich die variablen Kosten? Wahrscheinlich auf
        #  Strom, denn auch die Max Leistung wurde für Strom angegeben.
        self.variable_costs = opex
        self.initial_storage_level = initial_storage_level
        super().__init__(label=label, facade_type=type(self))

    def define_subnetwork(self):
        # Berechne Leistungen
        max_charge_power = self.storage_capacity * self.max_charge_rate
        max_discharge_power = self.storage_capacity * self.max_discharge_rate

        self.subnode(
            GenericStorage,
            inputs={
                self.bus_electricity: Flow(
                    nominal_capacity=max_charge_power,
                    variable_costs=self.variable_costs,
                )
            },
            outputs={
                self.bus_electricity: Flow(
                    nominal_capacity=max_discharge_power,
                )
            },
            nominal_capacity=self.storage_capacity,
            initial_storage_level=self.initial_storage_level,
            inflow_conversion_factor=self.charge_efficiency,
            outflow_conversion_factor=self.discharge_efficiency,
            loss_rate=self.self_discharge_rate,
            # Konvertierung zu Dezimal
            label="battery_storage",
        )


class CarrierBus(Bus):
    """Bus mit Medium-Attribut"""

    def __init__(self, label, carrier=None, **kwargs):
        """
        Bus mit Energieträger-Information

        Parameters
        ----------
        label : str or tuple
            Eindeutige Bezeichnung des Bus
        carrier : str
            Energieträger/Medium (z.B. 'electricity', 'gas', 'heat', 'hydrogen')
        **kwargs
            Weitere Parameter für Bus

        Examples
        --------
        >>> electricity_bus = CarrierBus(label="grid", carrier="electricity")
        >>> gas_bus = CarrierBus(label="gas_grid", carrier="natural_gas")
        >>> heat_bus = CarrierBus(label="district_heating", carrier="heat")
        >>> h2_bus = CarrierBus(label="h2_network", carrier="hydrogen")
        """
        super().__init__(label=label, **kwargs)
        self.carrier = carrier

    def __repr__(self):
        return f"<CarrierBus '{self.label}' carrier='{self.carrier}'>"
