from __future__ import annotations

# BEARBEITET: Korrekter Importpfad für den Investment-Helper.
from oemof.eesyplan.investment import _create_invest_if_wanted
from oemof.solph.components import GenericStorage

from ._storage_common import ScalarSequence
from ._storage_common import make_storage_flow
from ._storage_common import normalize_investment_sequences
from ._storage_common import split_roundtrip_efficiency
from ._storage_common import validate_common_storage_parameters


class ElectricalStorage(GenericStorage):
    """Elektrischer Speicher auf Basis von oemof.solph GenericStorage.

    Die Klasse bildet einen elektrischen Speicher, z. B. eine Batterie, ab.
    Die Speicherkapazität kann entweder fest vorgegeben oder optimiert werden.

    Hinweise
    --------
    - `efficiency` wird als Roundtrip-Wirkungsgrad interpretiert.
      Intern wird daher `sqrt(efficiency)` jeweils für Laden und Entladen verwendet.
    - Bei `optimize_cap=True` wird die Speicherkapazität investiv optimiert.
    - Die Lade- und Entladeleistung wird über die C-Rate an die Speicherkapazität gekoppelt.
    - Wenn kein Ausgangsbus angegeben wird, wird der Eingangsbus auch als Ausgangsbus verwendet.
    """

    def __init__(
        self,
        name: str,
        bus_in_electricity,
        bus_out_electricity=None,
        age_installed: float = 0,
        installed_capacity: float = 0,
        capex_var: float = 0,
        opex_fix: float = 0,
        opex_var: float = 0,
        lifetime: float = 20,
        optimize_cap: bool = False,
        soc_max: float = 1,
        soc_min: float = 0,
        crate: float = 1,
        efficiency: float = 1,
        project_data=None,
        capex_fix: float = 0,
        self_discharge: float = 0,
        maximum_capacity: float | None = None,
        initial_storage_level: float | None = 0.0,
        balanced: bool = True,
    ):
        """Initialisiert einen elektrischen Speicher.

        Parameters
        ----------
        name:
            Eindeutiger Name des Speichers.
        bus_in_electricity:
            Elektrischer Eingangsbus des Speichers.
        bus_out_electricity:
            Elektrischer Ausgangsbus des Speichers. Wenn `None`, wird der Eingangsbus verwendet.
        age_installed:
            Alter der bereits installierten Kapazität.
        installed_capacity:
            Bereits installierte Speicherkapazität.
        capex_var:
            Variable Investitionskosten bezogen auf die Speicherkapazität.
        opex_fix:
            Fixe Betriebskosten.
        opex_var:
            Variable Betriebskosten des Ladeflusses.

            TODO: Klären, ob variable Speicherkosten fachlich auf den Ladefluss,
            Entladefluss oder beide Flüsse gelegt werden sollen.
        lifetime:
            Technische Lebensdauer.
        optimize_cap:
            Wenn `True`, wird die Speicherkapazität optimiert.
        soc_max:
            Maximaler Speicherfüllstand relativ zur Speicherkapazität.
        soc_min:
            Minimaler Speicherfüllstand relativ zur Speicherkapazität.
        crate:
            C-Rate zur Begrenzung von Lade- und Entladeleistung.
        efficiency:
            Roundtrip-Wirkungsgrad des Speichers.
        project_data:
            Projektdaten für die Investitionsrechnung.
        capex_fix:
            Fixe Investitionskosten.

            TODO: Aktuell nur gespeichert, aber nicht an `_create_invest_if_wanted`
            übergeben.
        self_discharge:
            Relativer Verlust pro Zeitschritt.
        maximum_capacity:
            Maximale installierbare Speicherkapazität.
        initial_storage_level:
            Initialer Speicherfüllstand relativ zur Speicherkapazität.
        balanced:
            Wenn `True`, muss der Speicher am Ende den Anfangsfüllstand erreichen.
        """

        # BEARBEITET: Wenn kein Output-Bus angegeben ist, wird der Input-Bus verwendet.
        if bus_out_electricity is None:
            bus_out_electricity = bus_in_electricity

        # BEARBEITET: Einheitliche Validierung aller Speicherparameter.
        validate_common_storage_parameters(
            name=name,
            bus_in=bus_in_electricity,
            bus_out=bus_out_electricity,
            age_installed=age_installed,
            installed_capacity=installed_capacity,
            capex_var=capex_var,
            capex_fix=capex_fix,
            opex_fix=opex_fix,
            opex_var=opex_var,
            lifetime=lifetime,
            optimize_cap=optimize_cap,
            soc_min=soc_min,
            soc_max=soc_max,
            crate=crate,
            efficiency=efficiency,
            loss_rate=self_discharge,
            maximum_capacity=maximum_capacity,
            initial_storage_level=initial_storage_level,
            balanced=balanced,
            project_data=project_data,
        )

        # BEARBEITET: Einheitliche Speicherung der Eingabeparameter.
        self.name = name
        self.bus_in_electricity = bus_in_electricity
        self.bus_out_electricity = bus_out_electricity
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_var = capex_var
        self.capex_fix = capex_fix
        self.opex_fix = opex_fix
        self.opex_var = opex_var
        self.lifetime = lifetime
        self.optimize_cap = optimize_cap
        self.soc_max = soc_max
        self.soc_min = soc_min
        self.crate = crate
        self.efficiency = efficiency
        self.self_discharge = self_discharge
        self.maximum_capacity = maximum_capacity
        self.initial_storage_level = initial_storage_level
        self.balanced = balanced
        self.project_data = project_data

        # BEARBEITET: Investition findet auf Speicherkapazität statt.
        # TODO: Prüfen, ob `_create_invest_if_wanted` `maximum_capacity=None`
        # sauber als unbegrenzt verarbeitet.
        nv = _create_invest_if_wanted(
            optimise_cap=optimize_cap,
            capex_var=capex_var,
            opex_fix=opex_fix,
            lifetime=lifetime,
            age_installed=age_installed,
            existing_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
            project_data=project_data,
        )

        nv = normalize_investment_sequences(nv)

        if optimize_cap:
            self.capacity_charge = None
            self.capacity_discharge = None
            self.crate_charge = crate
            self.crate_discharge = crate
        else:
            self.capacity_charge = installed_capacity * crate
            self.capacity_discharge = installed_capacity * crate
            self.crate_charge = None
            self.crate_discharge = None

        # BEARBEITET: Roundtrip-Wirkungsgrad wird symmetrisch aufgeteilt.
        efficiency_factor = split_roundtrip_efficiency(efficiency)

        super().__init__(
            label=name,
            inputs={
                bus_in_electricity: make_storage_flow(
                    optimize_cap=optimize_cap,
                    installed_capacity=installed_capacity,
                    crate=crate,
                    variable_costs=opex_var,
                ),
            },
            outputs={
                bus_out_electricity: make_storage_flow(
                    optimize_cap=optimize_cap,
                    installed_capacity=installed_capacity,
                    crate=crate,
                    variable_costs=0,
                ),
            },
            nominal_capacity=(nv if optimize_cap else installed_capacity),
            loss_rate=self_discharge,
            initial_storage_level=initial_storage_level,
            balanced=balanced,
            min_storage_level=soc_min,
            max_storage_level=soc_max,
            inflow_conversion_factor=efficiency_factor,
            outflow_conversion_factor=efficiency_factor,
            invest_relation_input_capacity=(crate if optimize_cap else None),
            invest_relation_output_capacity=(crate if optimize_cap else None),
        )

        self.nominal_capacity = (
            nv if optimize_cap else ScalarSequence(installed_capacity)
        )

        self.loss_rate = ScalarSequence(self_discharge)
        self.initial_storage_level = ScalarSequence(initial_storage_level)
        self.min_storage_level = ScalarSequence(soc_min)
        self.max_storage_level = ScalarSequence(soc_max)
        self.inflow_conversion_factor = ScalarSequence(efficiency_factor)
        self.outflow_conversion_factor = ScalarSequence(efficiency_factor)

        self.invest_relation_input_capacity = (
            ScalarSequence(crate) if optimize_cap else None
        )
        self.invest_relation_output_capacity = (
            ScalarSequence(crate) if optimize_cap else None
        )
