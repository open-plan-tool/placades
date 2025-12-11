from oemof.solph import Flow
from oemof.solph.components import Source

from placades.investment import _create_invest_if_wanted


class WindTurbine(Source):
     def __init__(
        self,
        project_data,
        bus_out_electricity,
        input_timeseries,
        name,
        age_installed=0,
        installed_capacity=0,
        capex_fix=0,
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=False,
        maximum_capacity=None,
        renewable_asset=True,
    ):
        """
        Wind turbine for electricity generation.

        This class represents a wind turbine that converts kinetic
        energy of wind into electrical energy.

        .. important ::
            This is a renewable energy source that contributes to the
            renewable share of the system.

        :Structure:
          *output*
            1. to_bus : Electricity

        :Optimization:
          The characteristic quantity of the optimization is the *nominal
          power-output* of the wind turbine given in kW

        Parameters
        ----------
        project_data: Project object
            |project_data|
        bus_out_electricity : bus object
            |bus_out_electricity|
        input_timeseries : array-like
            |input_timeseries|
        name : str
            |name|
        age_installed : int, default=0
            |age_installed|
        installed_capacity : float, default=0
            |installed_capacity|
        capex_fix : float, default=0
            |capex_fix|
        capex_var : float, default=1000
            |capex_var|
        opex_fix : float, default=10
            |opex_fix|
        opex_var : float, default=0
            |opex_var|
        lifetime : int, default=20
            |lifetime|
        optimize_cap : bool, default=False
            |optimize_cap|
        maximum_capacity : float or None, default=None
            |maximum_capacity|
        renewable_asset : bool, default=True
            |renewable_asset|


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
        >>> el_bus = CarrierBus(label="my_electricity_bus")
        >>> my_wind = WindTurbine(
        ...     bus_out_electricity=el_bus,
        ...     name="my_wind_plant",
        ...     age_installed=0, # a
        ...     installed_capacity=0, # a
        ...     capex_fix=0, # €
        ...     capex_var=1000, # €/kW
        ...     opex_fix=10, # €/kW/a
        ...     opex_var=0, # €/kWh
        ...     lifetime=25, # a
        ...     optimize_cap=True,
        ...     maximum_capacity=1000, # kWp
        ...     renewable_asset=True,
        ...     input_timeseries=[1,2,3],
        ...     project_data=my_project,
        ...  )

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

        self.bus_out_electricity = bus_out_electricity
        self.input_timeseries = input_timeseries
        self.name = name
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_fix = capex_fix
        self.capex_var = capex_var
        self.opex_fix = opex_fix
        self.opex_var = opex_var
        self.lifetime = lifetime
        self.optimize_cap = optimize_cap
        self.maximum_capacity = maximum_capacity
        self.renewable_asset = renewable_asset

        outputs = {
            self.bus_out_electricity: Flow(
                fix=input_timeseries,
                nominal_capacity=nv,
            )
        }

        super().__init__(label=name, outputs=outputs)
