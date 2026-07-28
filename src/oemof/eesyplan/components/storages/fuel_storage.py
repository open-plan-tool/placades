from oemof.eesyplan.components.storages.storage import EnergyStorage


class FuelStorage(EnergyStorage):
    def __init__(
        self,
        name,
        project_data,
        installed_capacity,
        bus_in_fuel,
        bus_out_fuel=None,
        age_installed=0,
        capex_var=0,
        opex_fix=0,
        opex_var=0,
        lifetime=None,
        optimize_cap=False,
        soc_max=1,
        soc_min=0,
        c_rate_charge=1.0,
        c_rate_discharge=None,
        efficiency_charge=1.0,
        efficiency_discharge=1.0,
        energy_losses_relative=0.0,
        maximum_capacity_investment=float("+inf"),
    ):
        """
        Fuel Energy Storage System (FESS).

        This class represents a fuel energy storage system for storing
        and dispatching fuel energy carriers.

        .. important ::
            This system can store various types of fuel including natural
            gas and biogas.

        :Structure:
          *input*
            1. bus_in_fuel : Gas
          *output*
            1. bus_out_fuel : Gas

        Parameters
        ----------
        name : string
            |name|
        project_data : Project object
            |project_data|
        installed_capacity : float
            |installed_capacity|
        bus_in_fuel : Node object
            |bus_in_fuel|
        bus_out_fuel : Node object, optional (default: None)
            |bus_out_fuel|
        age_installed : float or int, optional (default: 0)
            |age_installed|
        capex_var : float, optional (default: 0)
            |capex_var|
        opex_fix : float, optional (default: 0)
            |opex_fix|
        opex_var : float, optional (default: 0)
            |opex_var|
        lifetime : int, optional (default: None)
            |lifetime|
        optimize_cap : bool, optional (default: False)
            |optimize_cap|
        soc_max : float, optional (default: 1)
            |soc_max|
        soc_min : float, optional (default: 0)
            |soc_min|
        c_rate_charge : float, optional (default: 1.0)
            |crate|
        c_rate_discharge : float, optional (default: None)
            |crate|
        efficiency_charge : float, optional (default: 1.0)
            |efficiency_charge|
        efficiency_discharge : float, optional (default: 1.0)
            |efficiency_discharge|
        energy_losses_relative : float, optional (default: 0.0)
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
        >>> fuel_bus = CarrierBus(name="gas_bus")
        >>> my_bess = FuelStorage(
        ...     name="gas storage tank",
        ...     project_data=my_project,
        ...     bus_in_fuel=fuel_bus,
        ...     installed_capacity=10,
        ...     c_rate_charge=0.7,
        ...     c_rate_discharge=0.8,
        ...     energy_losses_relative=0.0001,
        ... )
        >>> my_invest_bess = FuelStorage(
        ...     name="gas storage tank extension",
        ...     bus_in_fuel=fuel_bus,
        ...     bus_out_fuel=fuel_bus,
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
        ...     energy_losses_relative=0.0001,
        ... )
        """
        super().__init__(
            name,
            project_data=project_data,
            installed_capacity=installed_capacity,
            bus_in=bus_in_fuel,
            bus_out=bus_out_fuel,
            age_installed=age_installed,
            capex_var=capex_var,
            opex_fix=opex_fix,
            opex_var=opex_var,
            lifetime=lifetime,
            optimize_cap=optimize_cap,
            soc_max=soc_max,
            soc_min=soc_min,
            energy_losses_relative=energy_losses_relative,
            efficiency_charge=efficiency_charge,
            efficiency_discharge=efficiency_discharge,
            theoretical_time_charge=c_rate_charge,  # hours
            theoretical_time_discharge=c_rate_discharge,  # hours
            maximum_capacity_investment=maximum_capacity_investment,
        )
