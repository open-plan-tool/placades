import pytest
from oemof.solph import Bus

# Annahme: Das Modul heißt 'energy_components'
from placades.komponenten import CHP
from placades.komponenten import Battery
from placades.komponenten import CarrierBus


class TestCHP:
    """Tests für die CHP Klasse"""

    @pytest.fixture
    def buses(self):
        """Fixture für Test-Busse"""
        return {
            "gas": Bus(label="gas_bus"),
            "electricity": Bus(label="electricity_bus"),
            "heat": Bus(label="heat_bus"),
        }

    def test_chp_initialization_minimal(self, buses):
        """Test minimale CHP Initialisierung"""
        chp = CHP(
            label="test_chp",
            bus_gas=buses["gas"],
            bus_electricity=buses["electricity"],
            bus_heat=buses["heat"],
        )

        assert chp.label.label == "test_chp"
        assert chp.bus_gas == buses["gas"]
        assert chp.bus_electricity == buses["electricity"]
        assert chp.bus_heat == buses["heat"]
        assert chp.electrical_capacity is None
        assert chp.electrical_efficiency == 0.35
        assert chp.thermal_efficiency == 0.50
        assert chp.variable_costs == 0

    def test_chp_initialization_full(self, buses):
        """Test vollständige CHP Initialisierung"""
        chp = CHP(
            label="test_chp_full",
            bus_gas=buses["gas"],
            bus_electricity=buses["electricity"],
            bus_heat=buses["heat"],
            electrical_capacity=1000,
            electrical_efficiency=0.40,
            thermal_efficiency=0.45,
            opex=0.02,
        )

        assert chp.electrical_capacity == 1000
        assert chp.electrical_efficiency == 0.40
        assert chp.thermal_efficiency == 0.45
        assert chp.variable_costs == 0.02

    def test_chp_efficiency_validation_valid(self, buses):
        """Test gültige Wirkungsgrade"""
        # Grenzfall: Genau 100%
        chp = CHP(
            label="test_chp",
            bus_gas=buses["gas"],
            bus_electricity=buses["electricity"],
            bus_heat=buses["heat"],
            electrical_efficiency=0.50,
            thermal_efficiency=0.50,
        )
        assert chp.electrical_efficiency == 0.50

    def test_chp_efficiency_validation_invalid(self, buses):
        """Test ungültige Wirkungsgrade (>100%)"""
        with pytest.raises(
            ValueError, match="Gesamtwirkungsgrad kann nicht > 100% sein"
        ):
            CHP(
                label="test_chp",
                bus_gas=buses["gas"],
                bus_electricity=buses["electricity"],
                bus_heat=buses["heat"],
                electrical_efficiency=0.60,
                thermal_efficiency=0.50,
            )


class TestBattery:
    """Tests für die Battery Klasse"""

    @pytest.fixture
    def electricity_bus(self):
        """Fixture für Strom-Bus"""
        return Bus(label="electricity_bus")

    def test_battery_initialization_minimal(self, electricity_bus):
        """Test minimale Battery Initialisierung"""
        battery = Battery(
            label="test_battery",
            bus_electricity=electricity_bus,
            storage_capacity=10,
        )

        assert battery.label.label == "test_battery"
        assert battery.bus_electricity == electricity_bus
        assert battery.storage_capacity == 10
        assert battery.max_charge_rate == 1.0
        assert battery.max_discharge_rate == 1.0
        assert battery.charge_efficiency == 0.95
        assert battery.discharge_efficiency == 0.95
        assert battery.self_discharge_rate == 0.001
        assert battery.initial_storage_level == 0.5

    def test_battery_initialization_full(self, electricity_bus):
        """Test vollständige Battery Initialisierung"""
        battery = Battery(
            label="test_battery_full",
            bus_electricity=electricity_bus,
            storage_capacity=50,
            max_charge_rate=0.5,
            max_discharge_rate=2.0,
            charge_efficiency=0.90,
            discharge_efficiency=0.92,
            self_discharge_rate=0.002,
            capex_capacity=400,
            capex_power=200,
            opex=0.001,
            initial_storage_level=0.3,
        )

        assert battery.storage_capacity == 50
        assert battery.max_charge_rate == 0.5
        assert battery.max_discharge_rate == 2.0
        assert battery.charge_efficiency == 0.90
        assert battery.discharge_efficiency == 0.92
        assert battery.self_discharge_rate == 0.002
        assert battery.capex_capacity == 400
        assert battery.capex_power == 200
        assert battery.variable_costs == 0.001
        assert battery.initial_storage_level == 0.3


class TestCarrierBus:
    """Tests für die CarrierBus Klasse"""

    def test_carrier_bus_initialization_with_carrier(self):
        """Test CarrierBus Initialisierung mit Energieträger"""
        bus = CarrierBus(label="test_bus", carrier="electricity")

        assert bus.label == "test_bus"
        assert bus.carrier == "electricity"
        assert isinstance(bus, Bus)  # Vererbung prüfen

    def test_carrier_bus_initialization_without_carrier(self):
        """Test CarrierBus Initialisierung ohne Energieträger"""
        bus = CarrierBus(label="test_bus")

        assert bus.label == "test_bus"
        assert bus.carrier is None

    def test_carrier_bus_with_kwargs(self):
        """Test CarrierBus mit zusätzlichen Bus-Parametern"""
        # Annahme: Bus akzeptiert weitere Parameter
        bus = CarrierBus(label="test_bus", carrier="natural_gas")

        assert bus.label == "test_bus"
        assert bus.carrier == "natural_gas"

    def test_carrier_bus_repr(self):
        """Test __repr__ Methode"""
        bus = CarrierBus(label="grid", carrier="electricity")
        repr_str = repr(bus)

        assert repr_str == "<CarrierBus 'grid' carrier='electricity'>"

    def test_carrier_bus_repr_without_carrier(self):
        """Test __repr__ ohne Energieträger"""
        bus = CarrierBus(label="test_bus")
        repr_str = repr(bus)

        assert repr_str == "<CarrierBus 'test_bus' carrier='None'>"

    @pytest.mark.parametrize(
        "carrier",
        ["electricity", "natural_gas", "heat", "hydrogen", "biomass", None],
    )
    def test_carrier_bus_different_carriers(self, carrier):
        """Test verschiedene Energieträger"""
        bus = CarrierBus(label="test_bus", carrier=carrier)
        assert bus.carrier == carrier


class TestIntegration:
    """Integrationstests für die Zusammenarbeit der Komponenten"""

    def test_chp_with_carrier_buses(self):
        """Test CHP mit CarrierBus"""
        gas_bus = CarrierBus(label="gas_grid", carrier="natural_gas")
        electricity_bus = CarrierBus(
            label="electricity_grid", carrier="electricity"
        )
        heat_bus = CarrierBus(label="heat_grid", carrier="heat")

        chp = CHP(
            label="district_chp",
            bus_gas=gas_bus,
            bus_electricity=electricity_bus,
            bus_heat=heat_bus,
            electrical_capacity=5000,
        )

        assert chp.bus_gas.carrier == "natural_gas"
        assert chp.bus_electricity.carrier == "electricity"
        assert chp.bus_heat.carrier == "heat"

    def test_battery_with_carrier_bus(self):
        """Test Battery mit CarrierBus"""
        electricity_bus = CarrierBus(label="grid", carrier="electricity")

        battery = Battery(
            label="grid_battery",
            bus_electricity=electricity_bus,
            storage_capacity=1000,
        )

        assert battery.bus_electricity.carrier == "electricity"


# Fixture für alle Tests
@pytest.fixture(scope="session")
def sample_energy_system():
    """Beispiel-Energiesystem für komplexere Tests"""
    gas_bus = CarrierBus(label="gas", carrier="natural_gas")
    electricity_bus = CarrierBus(label="electricity", carrier="electricity")
    heat_bus = CarrierBus(label="heat", carrier="heat")

    chp = CHP(
        label="chp_1MW",
        bus_gas=gas_bus,
        bus_electricity=electricity_bus,
        bus_heat=heat_bus,
        electrical_capacity=1000,
    )

    battery = Battery(
        label="battery_10MWh",
        bus_electricity=electricity_bus,
        storage_capacity=10000,
    )

    return {
        "buses": {
            "gas": gas_bus,
            "electricity": electricity_bus,
            "heat": heat_bus,
        },
        "components": {"chp": chp, "battery": battery},
    }
