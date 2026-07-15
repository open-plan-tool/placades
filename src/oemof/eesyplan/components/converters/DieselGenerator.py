"""Diesel generator converter component."""

from __future__ import annotations

from typing import Any

# TODO(review) [dringend]: `Any` für `project_data` ist sehr offen.
# Bitte entweder einen konkreteren Typ verwenden oder `project_data`
# explizit validieren, damit Fehler früher und klarer auftreten.
from oemof.eesyplan.components.converters._validation import validate_bool
from oemof.eesyplan.components.converters._validation import validate_bus
from oemof.eesyplan.components.converters._validation import (
    validate_efficiency,
)
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


class DieselGenerator(Converter):
    """Diesel generator for electricity generation.

    The diesel generator converts fuel from ``bus_in_fuel`` into electricity
    on ``bus_out_electricity``. The installed or optimized capacity is related
    to the electrical output flow.

    Parameters
    ----------
    name : str
        Name of the asset.
    bus_in_fuel : oemof.solph.Bus
        Fuel input bus.
    bus_out_electricity : oemof.solph.Bus
        Electricity output bus.
    project_data : oemof.eesyplan.Project
        Project data used to calculate investment annuities.
    # TODO(review) [dringend]: Wird dokumentiert, aber im Code nicht
        # typisiert oder validiert.
    efficiency : float, default=0.3
        Electrical efficiency. Must satisfy ``0 < efficiency <= 1``.
    age_installed : int, default=0
        Number of years the installed capacity has already been in operation.
    installed_capacity : float, default=0.0
        Existing electrical output capacity.
    capex_var : float, default=1000.0
        Specific investment costs related to electrical output capacity.
    capex_fix : float, default=0.0
        Fixed investment costs. Stored for consistency.
    # TODO(review) [wichtig]: `capex_fix` wird zwar gespeichert, aber
        # in der eigentlichen Investitionslogik nicht verwendet.
        # Bitte bewusst entscheiden: implementieren, entfernen oder klar
        # als reine Metadaten deklarieren.
    opex_fix : float, default=10.0
        Fixed operating costs related to installed electrical capacity.
    opex_var : float, default=0.0
        Variable operating costs related to electrical output.
    lifetime : int, default=20
        Technical lifetime of the generator.
    optimize_cap : bool, default=True
        If ``True``, output capacity is optimized using an investment flow.
    maximum_capacity : float or None, default=float("+inf")
        Maximum total electrical output capacity.
    # TODO(review) [mittel]: Der Typ erlaubt `None`, der Default ist aber
        # `float("+inf")`. Semantisch wäre entweder `None` als echter Default
        # oder ein reiner `float`-Typ konsistenter.

    Notes
    -----
    The converter equation is:

    ``p_el(t) = efficiency * p_fuel(t)``

    The nominal capacity is attached to the electricity output flow. Therefore,
    ``installed_capacity`` and ``maximum_capacity`` refer to electrical output
    capacity, not to fuel input capacity.

    Examples
    --------
    >>> from oemof.eesyplan import Project
    >>> from oemof.solph import Bus
    >>> from oemof.eesyplan.components.converters.DieselGenerator import (
    ...     DieselGenerator,
    ... )
    >>> fuel_bus = Bus(label="diesel")
    >>> electricity_bus = Bus(label="electricity")
    >>> project = Project(
    ...     name="Project_X",
    ...     lifetime=20,
    ...     tax=0,
    ...     discount_factor=0.01,
    ... )
    >>> generator = DieselGenerator(
    ...     name="diesel_generator",
    ...     bus_in_fuel=fuel_bus,
    ...     bus_out_electricity=electricity_bus,
    ...     project_data=project,
    ...     installed_capacity=10,
    ...     efficiency=0.35,
    ... )
    >>> generator.efficiency
    0.35
    """

    def __init__(
        self,
        name: str,
        bus_in_fuel: Bus,
        bus_out_electricity: Bus,
        project_data: Any,
        efficiency: float = 0.3,
        age_installed: int = 0,
        installed_capacity: float = 0.0,
        capex_var: float = 1000.0,
        capex_fix: float = 0.0,
        opex_fix: float = 10.0,
        opex_var: float = 0.0,
        lifetime: int = 20,
        optimize_cap: bool = True,
        maximum_capacity: float | None = float("+inf"),
        # TODO(review) [mittel]: Falls `None` wirklich unterstützt wird,
        # wäre `maximum_capacity: float | None = None` evtl. sauberer.
    ) -> None:
        """Initialize a diesel generator converter."""
        self.name = validate_name(name)
        self.bus_in_fuel = validate_bus("bus_in_fuel", bus_in_fuel)
        self.bus_out_electricity = validate_bus(
            "bus_out_electricity", bus_out_electricity
        )
        self.project_data = project_data
        # TODO(review) [dringend]: `project_data` sollte idealerweise vor der
        # Weitergabe an `_create_invest_if_wanted` validiert werden.

        self.efficiency = validate_efficiency("efficiency", efficiency)
        self.age_installed = validate_non_negative_int(
            "age_installed", age_installed
        )
        self.installed_capacity = validate_non_negative_float(
            "installed_capacity", installed_capacity
        )
        self.capex_var = validate_non_negative_float("capex_var", capex_var)
        self.capex_fix = validate_non_negative_float("capex_fix", capex_fix)
        self.opex_fix = validate_non_negative_float("opex_fix", opex_fix)
        self.opex_var = validate_non_negative_float("opex_var", opex_var)
        self.lifetime = validate_positive_int("lifetime", lifetime)
        self.optimize_cap = validate_bool("optimize_cap", optimize_cap)
        self.maximum_capacity = validate_optional_non_negative_capacity(
            "maximum_capacity", maximum_capacity
        )

        validate_maximum_capacity_not_below_installed(
            self.maximum_capacity,
            self.installed_capacity,
        )

        nominal_capacity = _create_invest_if_wanted(
            optimise_cap=self.optimize_cap,
            # TODO(review) [nice-to-have]: Schreibweise `optimise_cap`
            # im Helper vs. `optimize_cap` in der öffentlichen API
            # mittelfristig vereinheitlichen.
            capex_var=self.capex_var,
            opex_fix=self.opex_fix,
            lifetime=self.lifetime,
            age_installed=self.age_installed,
            existing_capacity=self.installed_capacity,
            maximum_capacity=self.maximum_capacity,
            project_data=self.project_data,
        )
        # TODO(review) [wichtig]: Bitte fachlich bestätigen, dass sich die
        # Investitions-/Bestandskapazität bewusst auf den elektrischen Output
        # und nicht auf den Brennstoffinput bezieht.

        inputs = {self.bus_in_fuel: Flow()}
        outputs = {
            self.bus_out_electricity: Flow(
                nominal_capacity=nominal_capacity,
                variable_costs=self.opex_var,
            )
        }

        super().__init__(
            label=self.name,
            inputs=inputs,
            outputs=outputs,
            conversion_factors={
                self.bus_out_electricity: self.efficiency,
            },
        )
