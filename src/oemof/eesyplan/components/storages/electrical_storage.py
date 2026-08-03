from oemof.eesyplan.components.storages.storage import EnergyStorage


class ElectricalStorage(EnergyStorage):
    def __init__(
        self,
        name,
        project_data,
        bus_in_electricity,
        bus_out_electricity=None,
        installed_capacity=None,
        maximum_capacity=None,
        age_installed=0,
        capex_spec=0,
        opex_spec=0,
        variable_costs=0,
        lifetime=20,
        soc_max=1,
        soc_min=0,
        self_discharge=0.0,
        efficiency_charge=1.0,
        efficiency_discharge=1.0,
        c_rate_charge=1.0,
        c_rate_discharge=None,
    ):
        """
        Battery Energy Storage System (BESS).

        This class represents a complete battery energy storage system
        for electrical energy storage and dispatch.

        .. important ::
           This is a simplified representation of a complete BESS
           including all necessary components.

        :Structure:
         *input*
           1. charge : Electricity
         *output*
           1. discharge : Electricity

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
        bus_in_electricity : Node object
            |bus_in_electricity|
        bus_out_electricity : Node object, optional (default: None)
            |bus_out_electricity|
        age_installed : float or int, optional (default: 0)
            |age_installed|
        capex_spec : float, optional (default: 0)
            |capex_spec|
        opex_spec : float, optional (default: 0)
            |opex_spec|
        variable_costs : float, optional (default: 0)
            |variable_costs|
        lifetime : int, optional (default: None)
            |lifetime|
        soc_max : float, optional (default: 1)
            |soc_max|
        soc_min : float, optional (default: 0)
            |soc_min|
        self_discharge : float, optional (default: 0.0)
            |energy_losses_relative|
        efficiency_charge : float, optional (default: 1.0)
            |efficiency_charge|
        efficiency_discharge : float, optional (default: 1.0)
            |efficiency_discharge|
        c_rate_charge : float, optional (default: 1.0)
            |crate|
        c_rate_discharge : float, optional (default: None)
            |crate|

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
        >>> el_bus = CarrierBus(name="my_electricity_bus")
        >>> my_bess = ElectricalStorage(
        ...     name="lithium_battery_system",
        ...     project_data=my_project,
        ...     bus_in_electricity=el_bus,
        ...     installed_capacity=10,
        ...     c_rate_charge=0.7,
        ...     c_rate_discharge=0.8,
        ...     self_discharge=0.0001,
        ... )
        >>> my_invest_bess = ElectricalStorage(
        ...     name="lithium_battery_extension_system",
        ...     bus_in_electricity=el_bus,
        ...     bus_out_electricity=el_bus,
        ...     age_installed=0,
        ...     maximum_capacity=1000,
        ...     capex_spec=3,
        ...     opex_spec=5,
        ...     variable_costs=0,
        ...     lifetime=10,
        ...     soc_max=1,
        ...     soc_min=0,
        ...     c_rate_charge=0.7,
        ...     c_rate_discharge=0.8,
        ...     efficiency_charge=0.99,
        ...     project_data=my_project,
        ...     self_discharge=0.0001,
        ... )
        """
        super().__init__(
            name,
            project_data=project_data,
            installed_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
            bus_in=bus_in_electricity,
            bus_out=bus_out_electricity,
            age_installed=age_installed,
            capex_spec=capex_spec,
            opex_spec=opex_spec,
            variable_costs=variable_costs,
            lifetime=lifetime,
            soc_max=soc_max,
            soc_min=soc_min,
            energy_losses_relative=self_discharge,
            efficiency_charge=efficiency_charge,
            efficiency_discharge=efficiency_discharge,
            theoretical_time_charge=c_rate_charge,  # hours
            theoretical_time_discharge=c_rate_discharge,  # hours
        )
