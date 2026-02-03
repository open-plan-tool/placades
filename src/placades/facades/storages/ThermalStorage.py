from math import sqrt

from oemof.solph import Flow
from oemof.solph import Investment
from oemof.solph.components import GenericStorage

from placades.investment import _create_invest_if_wanted


class ThermalStorage(GenericStorage):
    def __init__(
        self,
        name,
        bus_in_heat,
        age_installed,
        installed_capacity,
        capex_var,
        opex_fix,
        opex_var,
        lifetime,
        optimize_cap,
        soc_max,
        soc_min,
        crate,  # ToDo: Distinguish input and output and change to c_rate
        efficiency,  # ToDo: Distinguish input and output
        fixed_thermal_losses_relative,
        fixed_thermal_losses_absolute,
        project_data,
        capex_fix=0.0,
        thermal_loss_rate=0.0,
        bus_out_heat=None,
        maximum_capacity=float("+inf"),
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
        >>> from placades import Project
        >>> from placades import CarrierBus
        >>> my_project = Project(
        ...         name="my_project",
        ...         lifetime=20,
        ...         tax=0,
        ...         discount_factor=0.01
        ...     )
        >>> heat_bus = CarrierBus(name="my_heat_bus")
        >>> my_bess = ThermalStorage(
        ...     name="thermal_storage",
        ...     bus_in_heat=heat_bus,
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
            maximum_capacity=maximum_capacity,
            project_data=project_data,
        )

        self.thermal_loss_rate = thermal_loss_rate
        self.fixed_thermal_losses_absolute = fixed_thermal_losses_absolute
        self.fixed_thermal_losses_relative = fixed_thermal_losses_relative
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

        if bus_out_heat is None:
            bus_out_heat = bus_in_heat

        super().__init__(
            label=name,
            nominal_capacity=nv,
            inputs={
                bus_in_heat: Flow(
                    nominal_capacity=self.capacity_charge,
                    variable_costs=opex_var,
                )
            },
            outputs={
                bus_out_heat: Flow(nominal_capacity=self.capacity_discharge)
            },
            loss_rate=self.thermal_loss_rate,
            min_storage_level=soc_min,
            max_storage_level=soc_max,
            balanced=True,
            initial_storage_level=None,
            inflow_conversion_factor=self.efficiency,
            outflow_conversion_factor=self.efficiency,
            invest_relation_input_capacity=self.crate_charge,
            invest_relation_output_capacity=self.crate_charge,
            fixed_losses_absolute=fixed_thermal_losses_absolute,
            fixed_losses_relative=fixed_thermal_losses_relative,
        )
