from oemof.eesyplan.components.storages.storage import EnergyStorage


class ThermalStorage(EnergyStorage):
    def __init__(
        self,
        name,
        project_data,
        bus_in_heat,
        bus_out_heat=None,
        age_installed=0,
        installed_capacity=None,
        maximum_capacity=None,
        capex_spec=0.0,
        opex_spec=0.0,
        variable_costs=0.0,
        lifetime=20,
        soc_max=1.0,
        soc_min=0.0,
        thermal_losses_variable=0.0,
        thermal_losses_fixed=0.0,
        efficiency_charge=1.0,
        efficiency_discharge=1.0,
        theoretical_time_charge=1.0,  # hours
        theoretical_time_discharge=None,  # hours
    ):
        """
        Heat Energy Storage System (HESS).

        This class represents a complete thermal energy storage system
        for electrical energy storage and dispatch.

        .. important ::
           This is a simplified representation of a complete HESS
           including all necessary components.

        :Structure:
         *input*
           1. charge : Heat
         *output*
           1. discharge : Heat

        Parameters
        ----------
        name : string
            |name|
        project_data : Project object
            |project_data|
        installed_capacity : float or None (default: None)
            |installed_capacity|
        maximum_capacity : float or None (default: None)
            |maximum_capacity|
        bus_in_heat : Node object
            |bus_in_heat|
        bus_out_heat : Node object, optional (default: None)
            |bus_out_heat|
        age_installed : float or int, optional (default: 0)
            |age_installed|
        capex_spec : float, optional (default: 0.0)
            |capex_spec|
        opex_spec : float, optional (default: 0.0)
            |opex_spec|
        variable_costs : float, optional (default: 0.0)
            |variable_costs|
        lifetime : int, optional (default: None)
            |lifetime|
        soc_max : float, optional (default: 1.0)
            |soc_max|
        soc_min : float, optional (default: 0.0)
            |soc_min|
        thermal_losses_variable : float, optional (default: 0.0)
            |fixed_thermal_losses_relative|
        thermal_losses_fixed : float, optional (default: 0.0)
            |fixed_thermal_losses_absolute|
        efficiency_charge : float, optional (default: 1.0)
            |efficiency_charge|
        efficiency_discharge : float, optional (default: 1.0)
            |efficiency_discharge|
        theoretical_time_charge : float, optional (default: 1.0)
            |theoretical_time_charge|
        theoretical_time_discharge : float, optional (default: None)
            |theoretical_time_discharge|

        Examples
        --------
        >>> from oemof.eesyplan import Project
        >>> from oemof.eesyplan import CarrierBus
        >>> my_project = Project(
        ...         name="my_project",
        ...         economic_period=20,
        ...         tax=0,
        ...         discount_factor=0.01
        ...     )
        >>> heat_bus = CarrierBus(name="my_heat_bus")
        >>> my_storage = ThermalStorage(
        ...     name="thermal_storage",
        ...     project_data=my_project,
        ...     bus_in_heat=heat_bus,
        ...     installed_capacity=10,
        ... )
        >>> my_invest_storage = ThermalStorage(
        ...     name="thermal_storage_extension",
        ...     bus_in_heat=heat_bus,
        ...     bus_out_heat=heat_bus,
        ...     age_installed=0,
        ...     maximum_capacity=1000,
        ...     capex_spec=3,
        ...     opex_spec=5,
        ...     variable_costs=0,
        ...     lifetime=10,
        ...     soc_max=1,
        ...     soc_min=0,
        ...     theoretical_time_charge=1,
        ...     theoretical_time_discharge=1,
        ...     efficiency_charge=0.99,
        ...     project_data=my_project,
        ...     thermal_losses_variable=0.06,
        ...     thermal_losses_fixed=0.02,
        ... )
        """
        self.thermal_losses_variable = thermal_losses_variable
        self.thermal_losses_fixed = thermal_losses_fixed

        super().__init__(
            name,
            project_data=project_data,
            installed_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
            bus_in=bus_in_heat,
            bus_out=bus_out_heat,
            age_installed=age_installed,
            capex_spec=capex_spec,
            opex_spec=opex_spec,
            variable_costs=variable_costs,
            lifetime=lifetime,
            soc_max=soc_max,
            soc_min=soc_min,
            energy_losses_variable=thermal_losses_variable,
            energy_losses_fixed=thermal_losses_fixed,
            efficiency_charge=efficiency_charge,
            efficiency_discharge=efficiency_discharge,
            theoretical_time_charge=theoretical_time_charge,  # hours
            theoretical_time_discharge=theoretical_time_discharge,  # hours
        )
