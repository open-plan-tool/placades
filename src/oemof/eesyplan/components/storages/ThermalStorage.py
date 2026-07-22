from __future__ import annotations

import math

# BEARBEITET: Korrekter Importpfad für den Investment-Helper.
from oemof.eesyplan.investment import _create_invest_if_wanted
from oemof.solph.components import GenericStorage

from ._storage_common import ScalarSequence
from ._storage_common import make_storage_flow
from ._storage_common import normalize_investment_sequences
from ._storage_common import split_roundtrip_efficiency
from ._storage_common import validate_common_storage_parameters
from ._storage_common import validate_thermal_fixed_losses


class ThermalStorage(GenericStorage):
    """Thermischer Speicher auf Basis von oemof.solph GenericStorage.

    Die Klasse bildet einen Wärmespeicher ab.
    Zusätzlich zu den allgemeinen Speicherparametern können thermische Verluste
    über relative und absolute Fixverluste berücksichtigt werden.

    Hinweise
    --------
    - `efficiency` wird als Roundtrip-Wirkungsgrad interpretiert.
    - Bei `optimize_cap=True` wird die Speicherkapazität investiv optimiert.
    - Lade- und Entladeleistung werden über die C-Rate an die Speicherkapazität gekoppelt.
    - `self_discharge` bleibt aus Kompatibilitätsgründen erhalten.
    - `thermal_loss_rate` ist als fachlich klarerer Alias vorgesehen.
    """

    def __init__(
        self,
        name: str,
        bus_in_heat,
        bus_out_heat=None,
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
        fixed_thermal_losses_absolute: float = 0,
        fixed_thermal_losses_relative: float = 0,
        thermal_loss_rate: float | None = None,
        initial_storage_level: float | None = 0.0,
        balanced: bool = True,
    ):
        """Initialisiert einen thermischen Speicher.

        Parameters
        ----------
        name:
            Eindeutiger Name des Speichers.
        bus_in_heat:
            Wärme-Eingangsbus des Speichers.
        bus_out_heat:
            Wärme-Ausgangsbus des Speichers. Wenn `None`, wird der Eingangsbus verwendet.
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
            Relativer Speicherverlust pro Zeitschritt.
            Bleibt aus Kompatibilitätsgründen erhalten.
        maximum_capacity:
            Maximale installierbare Speicherkapazität.
        fixed_thermal_losses_absolute:
            Absolute thermische Fixverluste.

            TODO: Prüfen, ob eure verwendete oemof.solph-Version
            `fixed_losses_absolute` im GenericStorage unterstützt.
        fixed_thermal_losses_relative:
            Relative thermische Fixverluste.

            TODO: Prüfen, ob eure verwendete oemof.solph-Version
            `fixed_losses_relative` im GenericStorage unterstützt.
        thermal_loss_rate:
            Alternativer Name für `self_discharge`.
        initial_storage_level:
            Initialer Speicherfüllstand relativ zur Speicherkapazität.
        balanced:
            Wenn `True`, muss der Speicher am Ende den Anfangsfüllstand erreichen.
        """

        # BEARBEITET: Wenn kein Output-Bus angegeben ist, wird der Input-Bus verwendet.
        if bus_out_heat is None:
            bus_out_heat = bus_in_heat

        # BEARBEITET: thermal_loss_rate als Alias für self_discharge eingeführt.
        # TODO: Langfristig entscheiden, ob nur noch `loss_rate`,
        # `self_discharge` oder `thermal_loss_rate` verwendet werden soll.
        if thermal_loss_rate is None:
            effective_thermal_loss_rate = self_discharge
        else:
            if not math.isclose(self_discharge, 0.0) and not math.isclose(
                self_discharge,
                thermal_loss_rate,
            ):
                raise ValueError(
                    "Use either self_discharge or thermal_loss_rate for ThermalStorage, "
                    "or set both to the same value."
                )

            effective_thermal_loss_rate = thermal_loss_rate

        # BEARBEITET: Einheitliche Validierung.
        validate_common_storage_parameters(
            name=name,
            bus_in=bus_in_heat,
            bus_out=bus_out_heat,
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
            loss_rate=effective_thermal_loss_rate,
            maximum_capacity=maximum_capacity,
            initial_storage_level=initial_storage_level,
            balanced=balanced,
            project_data=project_data,
        )

        # BEARBEITET: Zusatzvalidierung für thermische Fixverluste.
        validate_thermal_fixed_losses(
            fixed_thermal_losses_absolute=fixed_thermal_losses_absolute,
            fixed_thermal_losses_relative=fixed_thermal_losses_relative,
        )

        # BEARBEITET: Einheitliche Attributspeicherung.
        self.name = name
        self.bus_in_heat = bus_in_heat
        self.bus_out_heat = bus_out_heat
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
        self.self_discharge = effective_thermal_loss_rate
        self.thermal_loss_rate = effective_thermal_loss_rate
        self.fixed_thermal_losses_absolute = fixed_thermal_losses_absolute
        self.fixed_thermal_losses_relative = fixed_thermal_losses_relative
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
                bus_in_heat: make_storage_flow(
                    optimize_cap=optimize_cap,
                    installed_capacity=installed_capacity,
                    crate=crate,
                    variable_costs=opex_var,
                ),
            },
            outputs={
                bus_out_heat: make_storage_flow(
                    optimize_cap=optimize_cap,
                    installed_capacity=installed_capacity,
                    crate=crate,
                    variable_costs=0,
                ),
            },
            nominal_capacity=(nv if optimize_cap else installed_capacity),
            loss_rate=effective_thermal_loss_rate,
            fixed_losses_absolute=fixed_thermal_losses_absolute,
            fixed_losses_relative=fixed_thermal_losses_relative,
            initial_storage_level=initial_storage_level,
            balanced=balanced,
            min_storage_level=soc_min,
            max_storage_level=soc_max,
            inflow_conversion_factor=efficiency_factor,
            outflow_conversion_factor=efficiency_factor,
            invest_relation_input_capacity=(crate if optimize_cap else None),
            invest_relation_output_capacity=(crate if optimize_cap else None),
        )

        nv = normalize_investment_sequences(nv)

        self.nominal_capacity = (
            nv if optimize_cap else ScalarSequence(installed_capacity)
        )

        self.loss_rate = ScalarSequence(effective_thermal_loss_rate)
        self.initial_storage_level = ScalarSequence(initial_storage_level)
        self.min_storage_level = ScalarSequence(soc_min)
        self.max_storage_level = ScalarSequence(soc_max)
        self.inflow_conversion_factor = ScalarSequence(efficiency_factor)
        self.outflow_conversion_factor = ScalarSequence(efficiency_factor)

        self.fixed_losses_absolute = ScalarSequence(
            fixed_thermal_losses_absolute
        )
        self.fixed_losses_relative = ScalarSequence(
            fixed_thermal_losses_relative
        )

        self.invest_relation_input_capacity = (
            ScalarSequence(crate) if optimize_cap else None
        )
        self.invest_relation_output_capacity = (
            ScalarSequence(crate) if optimize_cap else None
        )

        self.self_discharge = float(effective_thermal_loss_rate)
        self.thermal_loss_rate = float(effective_thermal_loss_rate)
