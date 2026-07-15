"""Fixed-ratio combined heat and power converter component."""

from __future__ import annotations

from typing import Any

from oemof.eesyplan.components.converters._validation import validate_bool
from oemof.eesyplan.components.converters._validation import validate_bus
from oemof.eesyplan.components.converters._validation import (
    validate_efficiency,
)
from oemof.eesyplan.components.converters._validation import validate_float
from oemof.eesyplan.components.converters._validation import (
    validate_maximum_capacity_not_below_installed,
)
from oemof.eesyplan.components.converters._validation import validate_name
from oemof.eesyplan.components.converters._validation import (
    validate_non_negative_float,
)
from oemof.eesyplan.components.converters._validation import (
    validate_non_negative_int,
)
from oemof.eesyplan.components.converters._validation import (
    validate_optional_non_negative_capacity,
)
from oemof.eesyplan.components.converters._validation import (
    validate_positive_int,
)
from oemof.eesyplan.investment import _create_invest_if_wanted
from oemof.solph import Bus
from oemof.solph import Flow
from oemof.solph.components import Converter


class ChpFixedRatio(Converter):
    """Combined heat and power plant with fixed output ratio.

    The component converts fuel into electricity and heat with fixed
    conversion factors. The installed or optimized capacity is related to the
    electricity output flow.

    Parameters
    ----------
    name : str
        Name of the asset.
    bus_in_fuel : oemof.solph.Bus
        Fuel input bus.
    bus_out_electricity : oemof.solph.Bus
        Electricity output bus.
    bus_out_heat : oemof.solph.Bus
        Heat output bus.
    conversion_factor_to_electricity : float
        Electrical efficiency. Must satisfy ``0 < value <= 1``.
    conversion_factor_to_heat : float
        Thermal efficiency. Must satisfy ``0 < value <= 1``.
    project_data : oemof.eesyplan.Project
        Project data used to calculate investment annuities.
    age_installed : int, default=0
        Number of years the installed capacity has already been in operation.
    installed_capacity : float, default=0.0
        Existing electrical output capacity.
    capex_var : float, default=1000.0
        Specific investment costs related to electrical output capacity.
    capex_fix : float, default=0.0
        Fixed investment costs. Stored for consistency.
    opex_fix : float, default=10.0
        Fixed operating costs related to installed electrical capacity.
    opex_var : float, default=0.0
        Variable operating costs related to electricity output.
    lifetime : int, default=20
        Technical lifetime of the CHP unit.
    optimize_cap : bool, default=True
        If ``True``, electrical output capacity is optimized.
    maximum_capacity : float or None, default=float("+inf")
        Maximum total electrical output capacity.

    Notes
    -----
    The converter equations are:

    ``p_el(t) = conversion_factor_to_electricity * p_fuel(t)``

    ``q_heat(t) = conversion_factor_to_heat * p_fuel(t)``

    The total efficiency is:

    ``eta_total = conversion_factor_to_electricity
    + conversion_factor_to_heat``

    This implementation validates ``eta_total <= 1``. The nominal capacity is
    attached only to the electricity output flow.

    Examples
    --------
    >>> from oemof.eesyplan import Project
    >>> from oemof.solph import Bus
    >>> from oemof.eesyplan.components.converters.ChpFixedRatio import (
    ...     ChpFixedRatio,
    ... )
    >>> fuel_bus = Bus(label="fuel")
    >>> electricity_bus = Bus(label="electricity")
    >>> heat_bus = Bus(label="heat")
    >>> project = Project(
    ...     name="Project_X",
    ...     lifetime=20,
    ...     tax=0,
    ...     discount_factor=0.01,
    ... )
    >>> chp = ChpFixedRatio(
    ...     name="fixed_chp",
    ...     bus_in_fuel=fuel_bus,
    ...     bus_out_electricity=electricity_bus,
    ...     bus_out_heat=heat_bus,
    ...     conversion_factor_to_electricity=0.3,
    ...     conversion_factor_to_heat=0.5,
    ...     project_data=project,
    ...     installed_capacity=10,
    ... )
    >>> chp.conversion_factor_to_electricity
    0.3
    """

    def __init__(
        self,
        name: str,
        bus_in_fuel: Bus,
        bus_out_electricity: Bus,
        bus_out_heat: Bus,
        conversion_factor_to_electricity: float,
        conversion_factor_to_heat: float,
        project_data: Any,
        age_installed: int = 0,
        installed_capacity: float = 0.0,
        capex_var: float = 1000.0,
        capex_fix: float = 0.0,
        opex_fix: float = 10.0,
        opex_var: float = 0.0,
        lifetime: int = 20,
        optimize_cap: bool = True,
        maximum_capacity: float | None = float("+inf"),
    ) -> None:
        """Initialize a fixed-ratio CHP converter."""
        self.name = validate_name(name)
        self.bus_in_fuel = validate_bus("bus_in_fuel", bus_in_fuel)
        self.bus_out_electricity = validate_bus(
            "bus_out_electricity", bus_out_electricity
        )
        self.bus_out_heat = validate_bus("bus_out_heat", bus_out_heat)
        self.project_data = project_data
        # TODO(review): `project_data` wird aktuell nicht validiert, obwohl die
        # meisten anderen Eingaben explizit geprüft werden. Eine frühe Validierung
        # würde Fehler konsistenter und verständlicher machen.
        self.conversion_factor_to_electricity = validate_efficiency(
            "conversion_factor_to_electricity",
            conversion_factor_to_electricity,
        )
        self.conversion_factor_to_heat = validate_efficiency(
            "conversion_factor_to_heat",
            conversion_factor_to_heat,
        )

        if (
            self.conversion_factor_to_electricity
            + self.conversion_factor_to_heat
            > 1.0
        ):
            raise ValueError("Total efficiency must be <= 100%.")
        # TODO(review): Diese Prüfung verändert das
        # Verhalten gegenüber der alten Version. Prüfen, ob diese Verschärfung
        # als beabsichtigte API-/Kompatibilitätsänderung dokumentiert werden soll.

        self.age_installed = validate_non_negative_int(
            "age_installed", age_installed
        )
        self.installed_capacity = validate_non_negative_float(
            "installed_capacity", installed_capacity
        )
        self.capex_var = validate_non_negative_float("capex_var", capex_var)
        # TODO(review): `capex_fix` wird validiert und gespeichert, hat aber
        # aktuell keinen Einfluss auf Investitionsberechnung oder Modellverhalten.
        # Entweder in `_create_invest_if_wanted(...)` integrieren oder den
        # Parameter entfernen/deprecated markieren, um eine irreführende API
        # zu vermeiden.
        self.capex_fix = validate_non_negative_float("capex_fix", capex_fix)
        self.opex_fix = validate_non_negative_float("opex_fix", opex_fix)
        # TODO(review): opex_var darf auch negativ sein, durch angenommene Erlöse!?!
        self.opex_var = validate_float("opex_var", opex_var)
        self.lifetime = validate_positive_int("lifetime", lifetime)
        self.optimize_cap = validate_bool("optimize_cap", optimize_cap)

        self.maximum_capacity = validate_optional_non_negative_capacity(
            "maximum_capacity", maximum_capacity
        )
        # TODO(review): Die öffentliche API erlaubt hier `None`, der Default ist
        # aber `float("+inf")`. Prüfen, ob `None` wirklich unterstützt werden
        # soll oder ob Typannotation und Doku enger gefasst werden sollten.

        validate_maximum_capacity_not_below_installed(
            self.maximum_capacity,
            self.installed_capacity,
        )

        nominal_capacity = _create_invest_if_wanted(
            optimise_cap=self.optimize_cap,
            capex_var=self.capex_var,
            opex_fix=self.opex_fix,
            lifetime=self.lifetime,
            age_installed=self.age_installed,
            existing_capacity=self.installed_capacity,
            maximum_capacity=self.maximum_capacity,
            project_data=self.project_data,
        )

        inputs = {self.bus_in_fuel: Flow()}
        outputs = {
            self.bus_out_electricity: Flow(
                nominal_capacity=nominal_capacity,
                variable_costs=self.opex_var,
            ),
            self.bus_out_heat: Flow(),
        }
        conversion_factors = {
            self.bus_out_electricity: self.conversion_factor_to_electricity,
            self.bus_out_heat: self.conversion_factor_to_heat,
        }
        # TODO(review): Die Nennkapazität hängt nur am Strom-Output.
        # Das sollte in der Doku weiterhin klar hervorgehoben bleiben, damit
        # keine falschen Erwartungen an eine separat begrenzte Wärmekapazität
        # entstehen.
        super().__init__(
            label=self.name,
            inputs=inputs,
            outputs=outputs,
            conversion_factors=conversion_factors,
        )
