from math import sqrt

from oemof.solph import Flow
from oemof.solph import Investment
from oemof.solph.components import GenericStorage

from placades.investment import _create_invest_if_wanted


class ElectricalStorage(GenericStorage):
    def __init__(
        self,
        name,
        bus_electricity,
        age_installed,
        installed_capacity,
        capex_var,
        opex_fix,
        lifetime,
        optimize_cap,
        soc_max,
        soc_min,
        crate,
        efficiency,
        # # Keep in mind for thermal storages
        # fixed_thermal_losses_relative,
        # fixed_thermal_losses_absolute,
        project_data,
        self_discharge=0.0,
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
        name : str
           Name of the asset.

        Examples
        --------
        >>> from placades import Project
        >>> from placades import CarrierBus
        >>> my_project = Project(
        ...         name="my_project",
        ...         lifetime=20,
        ...         tax=0,
        ...         discount_factor=0.01
        ...     )
        >>> el_bus = CarrierBus(name="my_electricity_bus")
        >>> my_bess = ElectricalStorage(
        ...     name="lithium_battery_system",
        ...     bus_electricity=el_bus,
        ...     age_installed=0,
        ...     installed_capacity=0,
        ...     capex_var=3,
        ...     opex_fix=5,
        ...     lifetime=10,
        ...     optimize_cap=False,
        ...     soc_max=1,
        ...     soc_min=0,
        ...     crate=1,
        ...     efficiency=0.99,
        ...     project_data=my_project,
        ...     self_discharge=0.0001,
        ... )
        """

        nv = _create_invest_if_wanted(
            optimise_cap=optimize_cap,
            capex_var=capex_var,
            opex_fix=opex_fix,
            lifetime=lifetime,
            age_installed=age_installed,
            existing_capacity=installed_capacity,
            project_data=project_data,
        )

        self.self_discharge = self_discharge
        self.efficiency = sqrt(efficiency)

        if optimize_cap:
            self.capacity_charge = Investment()
            self.capacity_discharge = Investment()
            self.crate_charge = crate
            self.crate_discharge = crate
        else:
            self.capacity_charge = nv * crate
            self.capacity_discharge = nv * crate
            self.crate_charge = None
            self.crate_discharge = None

        super().__init__(
            label=name,
            nominal_capacity=nv,
            inputs={
                bus_electricity: Flow(nominal_capacity=self.capacity_charge)
            },
            outputs={
                bus_electricity: Flow(nominal_capacity=self.capacity_discharge)
            },
            loss_rate=self.self_discharge,
            min_storage_level=soc_min,
            max_storage_level=soc_max,
            balanced=True,
            initial_storage_level=None,
            inflow_conversion_factor=self.efficiency,
            outflow_conversion_factor=self.efficiency,
            invest_relation_input_capacity=self.crate_charge,
            invest_relation_output_capacity=self.crate_charge,
            # # Keep in mind for thermal storages
            # fixed_losses_absolute=fixed_thermal_losses_absolute,
            # fixed_losses_relative=fixed_thermal_losses_relative,
        )
