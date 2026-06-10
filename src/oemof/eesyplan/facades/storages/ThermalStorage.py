from oemof.eesyplan.facades.storages.storage import EnergyStorage


class ThermalStorage(EnergyStorage):
    def __init__(
        self,
        name,
        project_data,
        installed_capacity,
        bus_in_heat,
        bus_out_heat=None,
        age_installed=0,
        capex_var=0.0,
        opex_fix=0.0,
        opex_var=0.0,
        lifetime=None,
        optimize_cap=False,
        soc_max=1.0,
        soc_min=0.0,
        thermal_losses_relative=0.0,
        thermal_losses_absolute=0.0,
        thermal_losses_absolute_investment=0,
        efficiency_charge=1.0,
        efficiency_discharge=1.0,
        theoretical_time_charge=1.0,  # hours
        theoretical_time_discharge=1.0,  # hours
        maximum_capacity_investment=float("+inf"),
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
        name : str
           Name of the asset.

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
        ...     installed_capacity=0.1,
        ...     capex_var=3,
        ...     opex_fix=5,
        ...     opex_var=0,
        ...     lifetime=10,
        ...     optimize_cap=True,
        ...     soc_max=1,
        ...     soc_min=0,
        ...     theoretical_time_charge=1,
        ...     theoretical_time_discharge=1,
        ...     efficiency_charge=0.99,
        ...     project_data=my_project,
        ...     thermal_losses_relative=0.6,
        ...     thermal_losses_absolute_investment=20,
        ... )
        """
        self.thermal_losses_relative = thermal_losses_relative
        self.thermal_losses_absolute = thermal_losses_absolute
        self.thermal_losses_absolute_investment = (
            thermal_losses_absolute_investment
        )

        super().__init__(
            name,
            project_data=project_data,
            installed_capacity=installed_capacity,
            bus_in=bus_in_heat,
            bus_out=bus_out_heat,
            age_installed=age_installed,
            capex_var=capex_var,
            opex_fix=opex_fix,
            opex_var=opex_var,
            lifetime=lifetime,
            optimize_cap=optimize_cap,
            soc_max=soc_max,
            soc_min=soc_min,
            energy_losses_relative=thermal_losses_relative,
            energy_losses_absolute=thermal_losses_absolute,
            energy_losses_absolute_investment=(
                thermal_losses_absolute_investment
            ),
            efficiency_charge=efficiency_charge,
            efficiency_discharge=efficiency_discharge,
            theoretical_time_charge=theoretical_time_charge,  # hours
            theoretical_time_discharge=theoretical_time_discharge,  # hours
            maximum_capacity_investment=maximum_capacity_investment,
        )
