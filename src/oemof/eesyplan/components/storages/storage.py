from oemof.solph import Flow
from oemof.solph import Investment
from oemof.solph.components import GenericStorage


class EnergyStorage(GenericStorage):
    def __init__(
        self,
        name,
        project_data,
        installed_capacity,
        bus_in,
        bus_out=None,
        age_installed=0,
        capex_spec=0,
        opex_spec=0,
        variable_costs=0,
        lifetime=20,
        soc_max=1,
        soc_min=0,
        energy_losses_relative=0.0,
        energy_losses_absolute=0.0,
        energy_losses_absolute_investment=0.0,
        efficiency_charge=1.0,
        efficiency_discharge=1.0,
        theoretical_time_charge=1.0,  # hours
        theoretical_time_discharge=None,  # hours
        maximum_capacity_investment=None,
    ):
        """
        Energy Storage System (ESS).

        This class represents a complete energy storage system for energy
        storage and dispatch.

        .. important ::
           This is a simplified representation of a complete ESS
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
        installed_capacity : float
            |installed_capacity|
        bus_in : Node object
            |bus_in|
        bus_out : Node object, optional
            |bus_out|
        age_installed : float or int, optional (default: 0)
            |age_installed|
        capex_spec : float, optional (default: 0)
            |capex_spec|
        opex_spec : float, optional (default: 0)
            |opex_spec|
        variable_costs : float, optional (default: 0)
            |variable_costs|
        lifetime : int, optional
            |lifetime|
        soc_max : float, optional (default: 1)
            |soc_max|
        soc_min : float, optional (default: 0)
            |soc_min|
        energy_losses_relative : float, optional (default: 0.0)
            |energy_losses_relative|
        energy_losses_absolute : float, optional (default: 0.0)
            |energy_losses_absolute|
        energy_losses_absolute_investment : float, optional (default: 0.0)
            |energy_losses_absolute_investment|
        efficiency_charge : float, optional (default: 1.0)
            |efficiency_charge|
        efficiency_discharge : float, optional (default: 1.0)
            |efficiency_discharge|
        theoretical_time_charge : float, optional (default: 1.0)
            |theoretical_time_charge|
        theoretical_time_discharge : float, optional
            |theoretical_time_discharge|
        maximum_capacity_investment : float, optional (default: float("+inf"))
            |maximum_capacity_investment|

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
        >>> heat_bus = CarrierBus(name="my_bus")
        >>> my_minimal_storage = EnergyStorage(
        ...     name="energy_storage",
        ...     project_data=my_project,
        ...     installed_capacity=10,
        ...     bus_in=heat_bus,
        ... )
        >>> my_invest_storage = EnergyStorage(
        ...     name="energy_storage_extension",
        ...     bus_in=heat_bus,
        ...     bus_out=heat_bus,
        ...     age_installed=0,
        ...     installed_capacity=0,
        ...     capex_spec=3,
        ...     opex_spec=5,
        ...     variable_costs=0,
        ...     lifetime=10,
        ...     soc_max=1,
        ...     soc_min=0,
        ...     theoretical_time_charge=1,  # hours
        ...     theoretical_time_discharge=1,  # hours
        ...     efficiency_charge=0.99,
        ...     project_data=my_project,
        ...     energy_losses_relative=0.6,
        ...     energy_losses_absolute_investment=20,
        ...     energy_losses_absolute=0.001,
        ... )
        """

        nv = project_data.create_invest_if_wanted(
            capex_spec=capex_spec,
            opex_spec=opex_spec,
            lifetime=lifetime,
            installed_capacity=installed_capacity,
            maximum_capacity=maximum_capacity_investment,
            project_data=project_data,
        )
        if theoretical_time_discharge is None:
            theoretical_time_discharge = theoretical_time_charge

        self.energy_losses_relative = energy_losses_relative
        self.energy_losses_absolute = energy_losses_absolute
        self.energy_losses_absolute_investment = (
            energy_losses_absolute_investment
        )
        self.efficiency_charge = efficiency_charge
        self.efficiency_discharge = efficiency_discharge

        if installed_capacity:
            self.capacity_charge = nv * theoretical_time_charge
            self.capacity_discharge = nv * theoretical_time_discharge
            self.crate_charge = None
            self.crate_discharge = None
        else:
            self.capacity_charge = Investment()
            self.capacity_discharge = Investment()
            self.crate_charge = theoretical_time_charge
            self.crate_discharge = theoretical_time_discharge

        if bus_out is None:
            bus_out = bus_in

        outputs = {bus_out: Flow(nominal_capacity=self.capacity_discharge)}
        self.bus_out = bus_out
        self.bus_in = bus_in

        super().__init__(
            label=name,
            nominal_capacity=nv,
            inputs={
                bus_in: Flow(
                    nominal_capacity=self.capacity_charge,
                    variable_costs=variable_costs,
                )
            },
            outputs=outputs,
            min_storage_level=soc_min,
            max_storage_level=soc_max,
            balanced=True,
            initial_storage_level=None,
            inflow_conversion_factor=self.efficiency_charge,
            outflow_conversion_factor=self.efficiency_discharge,
            invest_relation_input_capacity=self.crate_charge,
            invest_relation_output_capacity=self.crate_charge,
            loss_rate=self.energy_losses_relative,
            fixed_losses_absolute=self.energy_losses_absolute,
            fixed_losses_relative=self.energy_losses_absolute_investment,
        )
