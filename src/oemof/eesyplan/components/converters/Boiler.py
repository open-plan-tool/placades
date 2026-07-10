"""Boiler converter component."""

from __future__ import annotations

from typing import Any

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


class Boiler(Converter):
    """Boiler for heat generation.

    The boiler converts fuel energy from ``bus_in_fuel`` into useful heat on
    ``bus_out_heat``. The installed or optimized capacity is related to the
    useful heat output flow.

    Parameters
    ----------
    name : str
        Name of the asset.
    bus_in_fuel : oemof.solph.Bus
        Fuel input bus.
    bus_out_heat : oemof.solph.Bus
        Useful heat output bus.
    project_data : oemof.eesyplan.Project
        Project data used to calculate investment annuities.
    efficiency : float, default=0.8
        Boiler efficiency. Must satisfy ``0 < efficiency <= 1``.
    age_installed : int, default=0
        Number of years the installed capacity has already been in operation.
    installed_capacity : float, default=0.0
        Existing useful heat output capacity.
    capex_var : float, default=1000.0
        Specific investment costs related to useful heat output capacity.
    capex_fix : float, default=0.0
        Fixed investment costs. Stored for consistency.
    opex_fix : float, default=10.0
        Fixed operating costs related to installed heat output capacity.
    opex_var : float, default=0.0
        Variable operating costs related to useful heat output.
    lifetime : int, default=20
        Technical lifetime of the boiler.
    optimize_cap : bool, default=True
        If ``True``, output capacity is optimized using an investment flow.
    maximum_capacity : float or None, default=float("+inf")
        Maximum total useful heat output capacity.

    Notes
    -----
    The converter equation is:

    ``q_heat(t) = efficiency * q_fuel(t)``

    The nominal capacity is attached to the heat output flow. Therefore,
    ``installed_capacity`` and ``maximum_capacity`` refer to useful heat
    output capacity, not to fuel input capacity.

    Examples
    --------
    >>> from oemof.eesyplan import Project
    >>> from oemof.solph import Bus
    >>> from oemof.eesyplan.components.converters.Boiler import Boiler
    >>> fuel_bus = Bus(label="fuel")
    >>> heat_bus = Bus(label="heat")
    >>> project = Project(
    ...     name="Project_X",
    ...     lifetime=20,
    ...     tax=0,
    ...     discount_factor=0.01,
    ... )
    >>> boiler = Boiler(
    ...     name="gas_boiler",
    ...     bus_in_fuel=fuel_bus,
    ...     bus_out_heat=heat_bus,
    ...     project_data=project,
    ...     installed_capacity=10,
    ...     efficiency=0.9,
    ... )
    >>> boiler.efficiency
    0.9
    """

    def __init__(
        self,
        name: str,
        bus_in_fuel: Bus,
        bus_out_heat: Bus,
        project_data: Any,
        efficiency: float = 0.8,
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
        """Initialize a boiler converter."""
        self.name = validate_name(name)
        self.bus_in_fuel = validate_bus("bus_in_fuel", bus_in_fuel)
        self.bus_out_heat = validate_bus("bus_out_heat", bus_out_heat)
        self.project_data = project_data

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
            self.bus_out_heat: Flow(
                nominal_capacity=nominal_capacity,
                variable_costs=self.opex_var,
            )
        }

        super().__init__(
            label=self.name,
            inputs=inputs,
            outputs=outputs,
            conversion_factors={self.bus_out_heat: self.efficiency},
        )
