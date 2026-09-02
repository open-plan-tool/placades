import numpy as np

from oemof.solph import Flow
from oemof.solph.components import Converter


class HeatPump(Converter):
    def __init__(
        self,
        name,
        project_data,
        cop,
        bus_in_electricity,
        bus_out_heat,
        bus_in_heat=None,
        installed_capacity=None,
        maximum_capacity=None,
        age_installed=0,
        capex_spec=0.0,
        variable_costs=0.0,
        opex_spec=0.0,
        lifetime=20,
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
            |name|
        age_installed : int, default=0
            |age_installed|
        installed_capacity : float or None (default: None)
            |installed_capacity|
        maximum_capacity : float or None (default: None)
            |maximum_capacity|
        capex_spec : float, default=0
            |capex_spec|
        variable_costs : float, default=0
            |variable_costs|
        opex_spec : float, default=0
            |opex_spec|
        lifetime : int, default=20
            |lifetime|
        maximum_capacity : float or None, default=None
            |maximum_capacity|
        cop : float or list-like, default=0.8
            |cop|

        Examples
        --------
        >>> from oemof.eesyplan import Project
        >>> from oemof.eesyplan import CarrierBus
        >>> el_bus = CarrierBus(name="electricity_bus")
        >>> ambient_heat_bus = CarrierBus(name="ambient_heat_bus")
        >>> heat_bus = CarrierBus(name="heat_bus")
        >>> my_heat_pump = HeatPump(
        ...     name="air_source_heat_pump",
        ...     bus_in_electricity=el_bus,
        ...     bus_out_heat=heat_bus,
        ...     installed_capacity=15,
        ...     cop=3.5,
        ...     project_data=Project(
        ...         name="Project_X", economic_period=20, tax=0,
        ...         discount_factor=0.01,
        ...     )
        ... )
        >>> my_heat_pump2 = HeatPump(
        ...     name="air_source_heat_pump",
        ...     bus_in_electricity=el_bus,
        ...     bus_in_heat=ambient_heat_bus,
        ...     bus_out_heat=heat_bus,
        ...     installed_capacity=15,
        ...     cop=[3.5] * 5,
        ...     project_data=Project(
        ...         name="Project_X", economic_period=20, tax=0,
        ...         discount_factor=0.01,
        ...     )
        ... )

        """

        if isinstance(cop, list):
            cop = np.array(cop)

        nv = project_data.create_invest_if_wanted(
            capex_spec=capex_spec,
            opex_spec=opex_spec,
            lifetime=lifetime,
            installed_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
        )

        inputs = {bus_in_electricity: Flow()}

        outputs = {
            bus_out_heat: Flow(
                nominal_capacity=nv,
                variable_costs=variable_costs,
            )
        }

        conversion_factors = {
            bus_in_electricity: 1 / cop,
        }

        if bus_in_heat is not None:
            conversion_factors[bus_in_heat] = (cop - 1) / cop
            inputs[bus_in_heat] = Flow()

        super().__init__(
            label=name,
            outputs=outputs,
            inputs=inputs,
            conversion_factors=conversion_factors,
        )

        self.name = name
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_spec = capex_spec
        self.variable_costs = variable_costs
        self.opex_spec = opex_spec
        self.lifetime = lifetime

        self.maximum_capacity = maximum_capacity
        self.cop = cop
