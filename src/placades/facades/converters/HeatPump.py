import numpy as np
from oemof.solph import Flow
from oemof.solph.components import Converter

from placades.investment import _create_invest_if_wanted


class HeatPump(Converter):
    def __init__(
        self,
        name,
        bus_in_heat,
        bus_in_electricity,
        bus_out_heat,
        project_data,
        age_installed=0,
        installed_capacity=0,
        capex_fix=1000,
        capex_var=1000,
        opex_var=0.01,
        opex_fix=10,
        lifetime=20,
        optimize_cap=False,
        maximum_capacity=None,
        cop=3,
    ):
        """
        Heat pump for efficient heat generation.

        This class represents a heat pump that extracts heat from a
        low-temperature source and delivers it at a higher temperature
        using electrical energy.

        .. important ::
            Heat pumps typically achieve efficiencies (COP) greater
            than 1.0, making them very efficient heating systems.

        :Structure:
          *input*
            1. electricity_bus : Electricity
            2. heat_bus : Heat
          *output*
            1. to_bus : Heat

        Parameters
        ----------
        name : str
            Name of the asset.
        age_installed : int, default=0
            Number of years the asset has already been in operation.
        installed_capacity : float, default=0
            Already existing installed capacity.
        capex_fix : float, default=1000
            Specific investment costs of the asset related to the
            installed capacity (CAPEX).
        capex_var : float, default=1000
            Specific investment costs of the asset related to the
            installed capacity (CAPEX).
        opex_var : float, default=0.01
            Costs associated with a flow through/from the asset
            (OPEX_var or fuel costs).
        opex_fix : float, default=10
            Specific operational and maintenance costs of the asset
            related to the installed capacity (OPEX_fix).
        lifetime : int, default=20
            Number of operational years of the asset until it has to
            be replaced.
        optimize_cap : bool, default=False
            Choose if capacity optimization should be performed for
            this asset.
        maximum_capacity : float or None, default=None
            Maximum total capacity of an asset that can be installed
            at the project site.
        efficiency : float, default=0.8
            Ratio of energy output to energy input.

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> el_bus = Bus(label="electricity_bus")
        >>> ambient_heat_bus = Bus(label="ambient_heat_bus")
        >>> heat_bus = Bus(label="heat_bus")
        >>> my_heat_pump = HeatPump(
        ...     name="air_source_heat_pump",
        ...     installed_capacity=15,
        ...     cop=3.5,
        ... )

        """

        if isinstance(cop, list):
            cop = np.array(cop)

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

        inputs = {bus_in_heat: Flow(), bus_in_electricity: Flow()}

        outputs = {
            bus_out_heat: Flow(
                nominal_capacity=nv,
                variable_costs=opex_var,
            )
        }

        conversion_factors = {
            bus_in_electricity: 1 / cop,
            bus_in_heat: (cop - 1) / cop,
        }

        super().__init__(
            label=name,
            outputs=outputs,
            inputs=inputs,
            conversion_factors=conversion_factors,
        )

        self.name = name
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_fix = capex_fix
        self.capex_var = capex_var
        self.opex_var = opex_var
        self.opex_fix = opex_fix
        self.lifetime = lifetime
        self.optimize_cap = optimize_cap
        self.maximum_capacity = maximum_capacity
        self.cop = cop
