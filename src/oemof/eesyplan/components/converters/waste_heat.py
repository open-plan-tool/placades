"""Direct waste heat components."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from oemof.eesyplan.investment import _create_invest_if_wanted
from oemof.solph import Bus
from oemof.solph import Flow
from oemof.solph.components import Converter


class WasteHeatDirect(Converter):
    """Direct integration of industrial waste heat via a heat exchanger.

    This component models a heat exchanger that converts available raw waste
    heat into useful heat. The available waste heat is taken from
    ``bus_in_heat`` and useful heat is supplied to ``bus_out_heat``.

    The component itself is a pure ``oemof.solph.components.Converter``. It
    does not create an internal waste heat source. Therefore, the raw waste
    heat bus must be supplied by a separate ``oemof.solph.components.Source``
    or another component in the energy system.

    Parameters
    ----------
    name : str
        Name of the asset.
    bus_in_heat : oemof.solph.Bus
        Input bus carrying raw waste heat before the heat exchanger.
    bus_out_heat : oemof.solph.Bus
        Output bus receiving useful heat after the heat exchanger.
    project_data : oemof.eesyplan.Project
        Project data used to calculate investment annuities.
    heat_profile : collections.abc.Iterable of float
        Time series of available raw waste heat before the heat exchanger.
        The values are interpreted as absolute available thermal power.
    age_installed : int, default=0
        Number of years the already installed heat exchanger capacity has
        been in operation.
    installed_capacity : float, default=0.0
        Existing useful heat output capacity of the heat exchanger.
    capex_fix : float, default=0.0
        Fixed investment costs of the asset. Stored for consistency with
        other eesyplan components.
    capex_var : float, default=0.0
        Specific investment costs related to useful heat output capacity.
    opex_var : float, default=0.0
        Variable operating costs of the heat exchanger related to useful heat
        output.
    opex_fix : float, default=0.0
        Fixed operating costs related to installed useful heat output
        capacity.
    lifetime : int, default=20
        Technical lifetime of the heat exchanger.
    optimize_cap : bool, default=False
        If ``True``, heat exchanger output capacity is optimized using an
        investment flow.
    maximum_capacity : float or None, default=None
        Maximum total useful heat output capacity. If ``None`` and capacity
        optimization is active, the maximum useful output implied by
        ``heat_profile`` and ``efficiency_hex`` is used.
    heat_cost : float, default=0.0
        Variable costs of raw waste heat before the heat exchanger.
    efficiency_hex : float, default=1.0
        Thermal efficiency of the heat exchanger. Must be greater than 0 and
        less than or equal to 1.

    Notes
    -----
    The raw waste heat profile ``q_raw_available(t)`` is internally normalized
    to a relative availability profile:

    ``max_raw(t) = q_raw_available(t) / max(q_raw_available)``

    The corresponding nominal raw waste heat capacity is:

    ``Q_raw_nom = max(q_raw_available)``

    The input flow from ``bus_in_heat`` is constrained by:

    ``q_raw(t) <= Q_raw_nom * max_raw(t)``

    Because the profile is used as ``max`` and not as ``fix``, curtailment of
    waste heat is possible.

    The converter equation is:

    ``q_out(t) = efficiency_hex * q_raw(t)``

    The maximum physically available useful heat output is therefore:

    ``Q_out_available = efficiency_hex * Q_raw_nom``

    Investment optimization is applied to the useful heat output flow. Thus,
    the optimizer may choose a heat exchanger capacity below the maximum
    physically available useful heat if this is economically optimal.

    Variable costs are separated physically:

    * ``heat_cost`` is applied to the raw heat input flow.
    * ``opex_var`` is applied to the useful heat output flow.

    Consequently, the raw heat cost contribution per unit of useful heat is
    ``heat_cost / efficiency_hex``.

    Examples
    --------
    >>> from oemof.eesyplan import Project
    >>> from oemof.solph import Bus
    >>> raw_heat_bus = Bus(label="raw_waste_heat")
    >>> heat_bus = Bus(label="heat")
    >>> project = Project(
    ...     name="Project_X",
    ...     lifetime=20,
    ...     tax=0,
    ...     discount_factor=0.01,
    ... )
    >>> waste_heat = WasteHeatDirect(
    ...     name="factory_waste_heat",
    ...     bus_in_heat=raw_heat_bus,
    ...     bus_out_heat=heat_bus,
    ...     project_data=project,
    ...     heat_profile=[10.0, 20.0, 30.0],
    ...     installed_capacity=24.0,
    ...     heat_cost=0.01,
    ...     efficiency_hex=0.8,
    ...     opex_var=0.002,
    ... )
    >>> waste_heat.raw_heat_nominal_capacity
    30.0
    >>> waste_heat.normalized_heat_profile
    (0.3333333333333333, 0.6666666666666666, 1.0)
    >>> waste_heat.useful_heat_available_capacity
    24.0
    """

    def __init__(
        self,
        name: str,
        bus_in_heat: Bus,
        bus_out_heat: Bus,
        project_data: Any,
        heat_profile: Iterable[float],
        age_installed: int = 0,
        installed_capacity: float = 0.0,
        capex_fix: float = 0.0,
        capex_var: float = 0.0,
        opex_var: float = 0.0,
        opex_fix: float = 0.0,
        lifetime: int = 20,
        optimize_cap: bool = False,
        maximum_capacity: float | None = None,
        heat_cost: float = 0.0,
        efficiency_hex: float = 1.0,
    ) -> None:
        """Initialize a direct waste heat converter.

        Parameters
        ----------
        name : str
            Name of the asset.
        bus_in_heat : oemof.solph.Bus
            Input bus carrying raw waste heat.
        bus_out_heat : oemof.solph.Bus
            Output bus receiving useful heat.
        project_data : oemof.eesyplan.Project
            Project data used for investment calculation.
        heat_profile : collections.abc.Iterable of float
            Available raw waste heat profile before the heat exchanger.
        age_installed : int, default=0
            Age of already installed capacity in years.
        installed_capacity : float, default=0.0
            Existing useful heat output capacity.
        capex_fix : float, default=0.0
            Fixed investment costs. Stored for consistency.
        capex_var : float, default=0.0
            Specific investment costs per unit of useful heat output capacity.
        opex_var : float, default=0.0
            Variable operating costs per unit of useful heat output.
        opex_fix : float, default=0.0
            Fixed operating costs per unit of installed useful heat capacity.
        lifetime : int, default=20
            Technical lifetime in years.
        optimize_cap : bool, default=False
            Enable investment optimization of the heat exchanger capacity.
        maximum_capacity : float or None, default=None
            Maximum useful heat output capacity.
        heat_cost : float, default=0.0
            Variable costs of raw waste heat input.
        efficiency_hex : float, default=1.0
            Heat exchanger efficiency.

        Notes
        -----
        ``heat_profile`` is used as a maximum availability profile. Therefore,
        the model may curtail unused waste heat. The heat exchanger output
        capacity is either fixed by ``installed_capacity`` or optimized if
        ``optimize_cap=True``.

        Examples
        --------
        >>> from oemof.eesyplan import Project
        >>> from oemof.solph import Bus
        >>> raw_heat_bus = Bus(label="raw_waste_heat")
        >>> heat_bus = Bus(label="heat")
        >>> project = Project(
        ...     name="Project_X",
        ...     lifetime=20,
        ...     tax=0,
        ...     discount_factor=0.01,
        ... )
        >>> component = WasteHeatDirect(
        ...     name="waste_heat",
        ...     bus_in_heat=raw_heat_bus,
        ...     bus_out_heat=heat_bus,
        ...     project_data=project,
        ...     heat_profile=[5.0, 10.0],
        ...     installed_capacity=9.0,
        ...     efficiency_hex=0.9,
        ... )
        >>> component.raw_heat_nominal_capacity
        10.0
        >>> component.useful_heat_available_capacity
        9.0
        """
        self.name = name
        self.bus_in_heat = self._validate_bus("bus_in_heat", bus_in_heat)
        self.bus_out_heat = self._validate_bus("bus_out_heat", bus_out_heat)
        self.project_data = project_data

        self.heat_profile = self._validate_heat_profile(heat_profile)
        self.age_installed = self._validate_non_negative_int(
            "age_installed", age_installed
        )
        self.installed_capacity = self._validate_non_negative_float(
            "installed_capacity", installed_capacity
        )
        self.capex_fix = self._validate_non_negative_float(
            "capex_fix", capex_fix
        )
        self.capex_var = self._validate_non_negative_float(
            "capex_var", capex_var
        )
        self.opex_var = self._validate_non_negative_float("opex_var", opex_var)
        self.opex_fix = self._validate_non_negative_float("opex_fix", opex_fix)
        self.lifetime = self._validate_positive_int("lifetime", lifetime)
        self.optimize_cap = self._validate_bool("optimize_cap", optimize_cap)
        self.maximum_capacity = self._validate_optional_non_negative_float(
            "maximum_capacity", maximum_capacity
        )
        self.heat_cost = self._validate_non_negative_float(
            "heat_cost", heat_cost
        )
        self.efficiency_hex = self._validate_efficiency(efficiency_hex)

        self.raw_heat_nominal_capacity = max(self.heat_profile)
        self.normalized_heat_profile = self._normalize_profile(
            self.heat_profile
        )
        self.useful_heat_available_capacity = (
            self.raw_heat_nominal_capacity * self.efficiency_hex
        )
        self.investment_maximum_capacity = (
            self._determine_investment_maximum_capacity()
        )

        nominal_capacity = _create_invest_if_wanted(
            optimise_cap=self.optimize_cap,
            capex_var=self.capex_var,
            opex_fix=self.opex_fix,
            lifetime=self.lifetime,
            age_installed=self.age_installed,
            existing_capacity=self.installed_capacity,
            maximum_capacity=self.investment_maximum_capacity,
            project_data=self.project_data,
        )

        inputs = {
            self.bus_in_heat: Flow(
                nominal_capacity=self.raw_heat_nominal_capacity,
                maximum=self.normalized_heat_profile,
                variable_costs=self.heat_cost,
            )
        }

        outputs = {
            self.bus_out_heat: Flow(
                nominal_capacity=nominal_capacity,
                variable_costs=self.opex_var,
            )
        }

        conversion_factors = {
            self.bus_out_heat: self.efficiency_hex,
        }

        super().__init__(
            label=self.name,
            inputs=inputs,
            outputs=outputs,
            conversion_factors=conversion_factors,
        )

    def _determine_investment_maximum_capacity(self) -> float | None:
        """Determine the maximum capacity used for investment optimization.

        Returns
        -------
        float or None
            Maximum useful heat output capacity passed to the investment
            helper.
        """
        if self.maximum_capacity is not None:
            if self.maximum_capacity < self.installed_capacity:
                raise ValueError(
                    "maximum_capacity must be >= installed_capacity."
                )
            return self.maximum_capacity

        return max(
            self.installed_capacity,
            self.useful_heat_available_capacity,
        )

    @staticmethod
    def _validate_bus(name: str, value: object) -> Bus:
        """Validate a bus parameter.

        Parameters
        ----------
        name : str
            Name of the checked parameter.
        value : object
            Object to validate.

        Returns
        -------
        oemof.solph.Bus
            Validated bus.

        Raises
        ------
        TypeError
            If ``value`` is not an ``oemof.solph.Bus``.
        """
        if not isinstance(value, Bus):
            raise TypeError(f"{name} must be an oemof.solph.Bus.")
        return value

    @staticmethod
    def _validate_heat_profile(
        heat_profile: Iterable[float],
    ) -> tuple[float, ...]:
        """Validate and convert the raw waste heat profile.

        Parameters
        ----------
        heat_profile : collections.abc.Iterable of float
            Raw waste heat availability profile.

        Returns
        -------
        tuple of float
            Validated heat profile.

        Raises
        ------
        TypeError
            If the profile is not an iterable numeric time series.
        ValueError
            If the profile is empty, contains negative values, non-finite
            values, or no positive value.
        """
        if heat_profile is None:
            raise ValueError("heat_profile must be provided.")

        if isinstance(heat_profile, str | bytes):
            raise TypeError("heat_profile must be a numeric time series.")

        try:
            values = tuple(
                WasteHeatDirect._to_float("heat_profile", value)
                for value in heat_profile
            )
        except TypeError as error:
            raise TypeError(
                "heat_profile must be an iterable of numeric values."
            ) from error

        if not values:
            raise ValueError("heat_profile must not be empty.")

        if any(value < 0 for value in values):
            raise ValueError("heat_profile must only contain values >= 0.")

        if max(values) <= 0:
            raise ValueError(
                "heat_profile must contain at least one positive value."
            )

        return values

    @staticmethod
    def _validate_efficiency(value: object) -> float:
        """Validate heat exchanger efficiency.

        Parameters
        ----------
        value : object
            Efficiency value.

        Returns
        -------
        float
            Validated efficiency.

        Raises
        ------
        TypeError
            If the value is not numeric.
        ValueError
            If the value is not finite or outside ``0 < value <= 1``.
        """
        numeric_value = WasteHeatDirect._to_float("efficiency_hex", value)

        if numeric_value <= 0 or numeric_value > 1:
            raise ValueError("efficiency_hex must be > 0 and <= 1.")

        return numeric_value

    @staticmethod
    def _validate_non_negative_float(name: str, value: object) -> float:
        """Validate a non-negative float parameter.

        Parameters
        ----------
        name : str
            Parameter name.
        value : object
            Value to validate.

        Returns
        -------
        float
            Validated float.

        Raises
        ------
        TypeError
            If the value is not numeric.
        ValueError
            If the value is negative or not finite.
        """
        numeric_value = WasteHeatDirect._to_float(name, value)

        if numeric_value < 0:
            raise ValueError(f"{name} must be >= 0.")

        return numeric_value

    @staticmethod
    def _validate_optional_non_negative_float(
        name: str,
        value: object | None,
    ) -> float | None:
        """Validate an optional non-negative float parameter.

        Parameters
        ----------
        name : str
            Parameter name.
        value : object or None
            Value to validate.

        Returns
        -------
        float or None
            Validated value.
        """
        if value is None:
            return None

        return WasteHeatDirect._validate_non_negative_float(name, value)

    @staticmethod
    def _validate_non_negative_int(name: str, value: object) -> int:
        """Validate a non-negative integer parameter.

        Parameters
        ----------
        name : str
            Parameter name.
        value : object
            Value to validate.

        Returns
        -------
        int
            Validated integer.
        """
        int_value = WasteHeatDirect._to_int(name, value)

        if int_value < 0:
            raise ValueError(f"{name} must be >= 0.")

        return int_value

    @staticmethod
    def _validate_positive_int(name: str, value: object) -> int:
        """Validate a positive integer parameter.

        Parameters
        ----------
        name : str
            Parameter name.
        value : object
            Value to validate.

        Returns
        -------
        int
            Validated integer.
        """
        int_value = WasteHeatDirect._to_int(name, value)

        if int_value <= 0:
            raise ValueError(f"{name} must be > 0.")

        return int_value

    @staticmethod
    def _validate_bool(name: str, value: object) -> bool:
        """Validate a boolean parameter.

        Parameters
        ----------
        name : str
            Parameter name.
        value : object
            Value to validate.

        Returns
        -------
        bool
            Validated boolean.
        """
        if not isinstance(value, bool):
            raise TypeError(f"{name} must be bool.")

        return value

    @staticmethod
    def _to_float(name: str, value: object) -> float:
        """Convert a value to float and check finiteness.

        Parameters
        ----------
        name : str
            Parameter name.
        value : object
            Value to convert.

        Returns
        -------
        float
            Converted finite float.
        """
        if isinstance(value, bool):
            raise TypeError(f"{name} must be numeric.")

        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as error:
            raise TypeError(f"{name} must be numeric.") from error

        if not math.isfinite(numeric_value):
            raise ValueError(f"{name} must be finite.")

        return numeric_value

    @staticmethod
    def _to_int(name: str, value: object) -> int:
        """Convert a value to int and reject non-integers.

        Parameters
        ----------
        name : str
            Parameter name.
        value : object
            Value to convert.

        Returns
        -------
        int
            Converted integer.
        """
        if isinstance(value, bool):
            raise TypeError(f"{name} must be integer.")

        try:
            int_value = int(value)
        except (TypeError, ValueError) as error:
            raise TypeError(f"{name} must be integer.") from error

        if int_value != value:
            raise TypeError(f"{name} must be integer.")

        return int_value

    @staticmethod
    def _normalize_profile(profile: tuple[float, ...]) -> tuple[float, ...]:
        """Normalize a profile to its maximum value.

        Parameters
        ----------
        profile : tuple of float
            Raw waste heat profile.

        Returns
        -------
        tuple of float
            Relative availability profile with maximum value 1.
        """
        nominal_capacity = max(profile)
        return tuple(value / nominal_capacity for value in profile)
