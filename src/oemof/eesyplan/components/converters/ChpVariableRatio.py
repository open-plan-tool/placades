"""Variable-ratio combined heat and power converter component."""

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
from oemof.solph.components import ExtractionTurbineCHP


class ChpVariableRatio(ExtractionTurbineCHP):
    """Extraction turbine CHP with variable heat-to-power ratio.

    The component models a CHP unit with heat extraction. Electricity and heat
    can vary within the feasible operating region defined by the full
    condensation electrical efficiency, the thermal extraction efficiency and
    the power loss index ``beta``.

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
        Electrical efficiency in full condensation mode.
    conversion_factor_to_heat : float
        Thermal efficiency at maximum heat extraction.
    beta : float
        Power loss index. It describes the reduction of electrical efficiency
        per unit of extracted heat.
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
    The electrical efficiency at maximum heat extraction is calculated as:

    ``eta_el_max_heat = eta_el_full_condensation - beta * eta_heat``

    with:

    ``eta_el_full_condensation = conversion_factor_to_electricity``

    ``eta_heat = conversion_factor_to_heat``

    The nominal capacity is attached to the electricity output flow. Therefore,
    ``installed_capacity`` and ``maximum_capacity`` refer to electrical output
    capacity.

    For compatibility with the existing component logic, the sum of
    ``conversion_factor_to_electricity`` and ``conversion_factor_to_heat`` must
    be strictly below ``1``.

    Examples
    --------
    >>> from oemof.eesyplan import Project
    >>> from oemof.solph import Bus
    >>> from oemof.eesyplan.components.converters.ChpVariableRatio import (
    ...     ChpVariableRatio,
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
    >>> chp = ChpVariableRatio(
    ...     name="variable_chp",
    ...     bus_in_fuel=fuel_bus,
    ...     bus_out_electricity=electricity_bus,
    ...     bus_out_heat=heat_bus,
    ...     conversion_factor_to_electricity=0.35,
    ...     conversion_factor_to_heat=0.45,
    ...     beta=0.2,
    ...     project_data=project,
    ...     installed_capacity=10,
    ... )
    >>> chp.efficiency_el_max_heat_extraction
    0.26
    """

    def __init__(
        self,
        name: str,
        bus_in_fuel: Bus,
        bus_out_electricity: Bus,
        bus_out_heat: Bus,
        conversion_factor_to_electricity: float,
        conversion_factor_to_heat: float,
        beta: float,
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
        """Initialize a variable-ratio CHP converter."""
        self.name = validate_name(name)
        self.bus_in_fuel = validate_bus("bus_in_fuel", bus_in_fuel)
        self.bus_out_electricity = validate_bus(
            "bus_out_electricity", bus_out_electricity
        )
        self.bus_out_heat = validate_bus("bus_out_heat", bus_out_heat)
        self.project_data = project_data

        self.conversion_factor_to_electricity = validate_efficiency(
            "conversion_factor_to_electricity",
            conversion_factor_to_electricity,
        )
        self.conversion_factor_to_heat = validate_efficiency(
            "conversion_factor_to_heat",
            conversion_factor_to_heat,
        )
        self.beta = validate_non_negative_float("beta", beta)

        if (
            self.conversion_factor_to_electricity
            + self.conversion_factor_to_heat
            >= 1.0
        ):
            raise ValueError(
                "Total efficiency is above 100% or equal to 100%."
            )

        self.efficiency_el_max_heat_extraction = (
            self.conversion_factor_to_electricity
            - self.beta * self.conversion_factor_to_heat
        )

        if self.efficiency_el_max_heat_extraction < 0:
            raise ValueError(
                "conversion_factor_to_electricity - beta "
                "* conversion_factor_to_heat must be >= 0."
            )

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
            self.bus_out_electricity: Flow(
                nominal_capacity=nominal_capacity,
                variable_costs=self.opex_var,
            ),
            self.bus_out_heat: Flow(),
        }
        conversion_factors = {
            self.bus_out_electricity: self.efficiency_el_max_heat_extraction,
            self.bus_out_heat: self.conversion_factor_to_heat,
        }
        conversion_factor_full_condensation = {
            self.bus_out_electricity: self.conversion_factor_to_electricity
        }

        super().__init__(
            label=self.name,
            inputs=inputs,
            outputs=outputs,
            conversion_factors=conversion_factors,
            conversion_factor_full_condensation=(
                conversion_factor_full_condensation
            ),
        )
