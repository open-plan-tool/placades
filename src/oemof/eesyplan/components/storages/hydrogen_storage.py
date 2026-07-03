from oemof.eesyplan.components.storages.storage import EnergyStorage


class HydrogenStorage(EnergyStorage):
    def __init__(
        self,
        name,
        project_data,
        installed_capacity,
        bus_in_hydrogen,
        bus_out_hydrogen=None,
        capex_var=0,
        opex_fix=0,
        opex_var=0,
        lifetime=None,
        age_installed=0,
        optimize_cap=False,
        soc_max=1.0,
        soc_min=1.0,
        c_rate_charge=1.0,
        c_rate_discharge=None,
        efficiency_charge=1.0,
        efficiency_discharge=1.0,
        self_discharge=0.0,
        maximum_capacity_investment=float("+inf"),
    ):
        """
        Hydrogen Energy Storage System (H2ESS).

        This class represents a hydrogen energy storage system for storing
        and dispatching hydrogen gas for various applications.

        .. important ::
            This system requires specialized storage technology for
            hydrogen handling and safety.

        :Structure:
          *input*
            1. charge : H2
          *output*
            1. discharge : H2

        Parameters
        ----------
        name : string
            |name|
        project_data : Project object
            |project_data|
        installed_capacity : float
            |installed_capacity|
        bus_in_hydrogen : Node object
            |bus_in_hydrogen|
        bus_out_hydrogen : Node object, optional (default: None)
            |bus_out_hydrogen|
        capex_var : float, optional (default: 0)
            |capex_var|
        opex_fix : float, optional (default: 0)
            |opex_fix|
        opex_var : float, optional (default: 0)
            |opex_var|
        lifetime : int, optional (default: None)
            |lifetime|
        age_installed : float or int, optional (default: 0)
            |age_installed|
        optimize_cap : bool, optional (default: False)
            |optimize_cap|
        soc_max : float, optional (default: 1.0)
            |soc_max|
        soc_min : float, optional (default: 1.0)
            |soc_min|
        c_rate_charge : float, optional (default: 1.0)
            |c_rate_charge|
        c_rate_discharge : float, optional (default: None)
            |c_rate_discharge|
        efficiency_charge : float, optional (default: 1.0)
            |efficiency_charge|
        efficiency_discharge : float, optional (default: 1.0)
            |efficiency_discharge|
        self_discharge : float, optional (default: 0.0)
            |energy_losses_relative|
        maximum_capacity_investment : float, optional (default: float("+inf"))
            |maximum_capacity_investment|

        Examples
        --------
        >>> from oemof.eesyplan import Project
        >>> from oemof.eesyplan import CarrierBus
        >>> my_project = Project(
        ...         name="my_project",
        ...         lifetime=20,
        ...         tax=0,
        ...         discount_factor=0.01
        ...     )
        >>> h2_bus = CarrierBus(name="my_h2_bus")
        >>> my_storage = HydrogenStorage(
        ...     name="hydrogen_storage_system",
        ...     project_data=my_project,
        ...     bus_in_hydrogen=h2_bus,
        ...     installed_capacity=10,
        ...     c_rate_charge=0.7,
        ...     c_rate_discharge=0.8,
        ...     self_discharge=0.0001,
        ... )
        >>> my_invest_storage = HydrogenStorage(
        ...     name="hydrogen_storage_system_extension",
        ...     bus_in_hydrogen=h2_bus,
        ...     bus_out_hydrogen=h2_bus,
        ...     age_installed=0,
        ...     installed_capacity=0,
        ...     capex_var=3,
        ...     opex_fix=5,
        ...     opex_var=0,
        ...     lifetime=10,
        ...     optimize_cap=True,
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
            bus_in=bus_in_hydrogen,
            bus_out=bus_out_hydrogen,
            age_installed=age_installed,
            capex_var=capex_var,
            opex_fix=opex_fix,
            opex_var=opex_var,
            lifetime=lifetime,
            optimize_cap=optimize_cap,
            soc_max=soc_max,
            soc_min=soc_min,
            energy_losses_relative=self_discharge,
            efficiency_charge=efficiency_charge,
            efficiency_discharge=efficiency_discharge,
            theoretical_time_charge=c_rate_charge,  # hours
            theoretical_time_discharge=c_rate_discharge,  # hours
            maximum_capacity_investment=maximum_capacity_investment,
        )
