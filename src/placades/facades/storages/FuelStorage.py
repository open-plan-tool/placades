from math import sqrt

from oemof.solph import Flow
from oemof.solph import Investment
from oemof.solph.components import GenericStorage

from placades.investment import _create_invest_if_wanted


class FuelStorage(GenericStorage):
    def __init__(
        self,
        name,
        bus_in_fuel,
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
        project_data,
        capex_fix=0.0,
        self_discharge=0.0,
        bus_out_fuel=None,
        maximum_capacity=float("+inf"),
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
        >>> fuel_bus = CarrierBus(name="gas_bus")
        >>> my_bess = FuelStorage(
        ...     name="gas_storage_tank",
        ...     bus_in_fuel=fuel_bus,
        ...     age_installed=0,
        ...     installed_capacity=0,
        ...     capex_var=3,
        ...     opex_fix=5,
        ...     opex_var=0.,
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

        if bus_out_fuel is None:
            bus_out_fuel = bus_in_fuel

        super().__init__(
            label=name,
            nominal_capacity=nv,
            inputs={
                bus_in_fuel: Flow(
                    nominal_capacity=self.capacity_charge,
                    variable_costs=opex_var,
                )
            },
            outputs={
                bus_out_fuel: Flow(nominal_capacity=self.capacity_discharge)
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
        )
