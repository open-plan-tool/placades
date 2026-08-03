from oemof.solph import Flow
from oemof.solph.components import Source


class BiogasPlant(Source):
    def __init__(
        self,
        project_data,
        bus_out_fuel,
        input_timeseries,
        name,
        age_installed=0,
        installed_capacity=None,
        maximum_capacity=None,
        capex_spec=1000,
        opex_spec=10,
        variable_costs=0,
        lifetime=20,
        renewable_asset=True,
    ):
        """
        Biogas power plant for renewable gas generation.

        This class represents a biogas plant that produces renewable gas
        from organic waste materials through anaerobic digestion.

        .. important ::
            This is a renewable energy source that produces carbon-neutral
            gas fuel.

        :Structure:
          *output*
            1. to_bus : Fuel

        :Optimization:
          The characteristic quantity of the optimization is the *nominal
          power-output* of the biogas power plant given in kW

        Parameters
        ----------
        project_data: Project object
            |project_data|
        bus_out_fuel : bus object
            |bus_out_fuel|
        input_timeseries : array-like
            |input_timeseries|
        name : str
            |name|
        age_installed : int, default=0
            |age_installed|
        installed_capacity : float or None (default: None)
            |installed_capacity|
        maximum_capacity : float or None (default: None)
            |maximum_capacity|
        capex_spec : float, default=1000
            |capex_spec|
        opex_spec : float, default=10
            |opex_spec|
        variable_costs : float, default=0
            |variable_costs|
        lifetime : int, default=20
            |lifetime|
        renewable_asset : bool, default=True
            |renewable_asset|

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
        >>> fuel_bus = CarrierBus(name="my_fuel_bus")
        >>> my_biogas = BiogasPlant(
        ...     bus_out_fuel=fuel_bus,
        ...     name="my_biogas_plant",
        ...     age_installed=0, # a
        ...     capex_spec=1000, # €/kW
        ...     opex_spec=10, # €/kW/a
        ...     variable_costs=0, # €/kWh
        ...     lifetime=25, # a
        ...     maximum_capacity=1000, # kW
        ...     renewable_asset=True,
        ...     input_timeseries=[1,2,3],
        ...     project_data=my_project,
        ...  )

        """

        nv = project_data.create_invest_if_wanted(
            capex_spec=capex_spec,
            opex_spec=opex_spec,
            lifetime=lifetime,
            installed_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
        )

        self.bus_out_fuel = bus_out_fuel
        self.input_timeseries = input_timeseries
        self.name = name
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity

        self.capex_spec = capex_spec
        self.opex_spec = opex_spec
        self.variable_costs = variable_costs
        self.lifetime = lifetime

        self.maximum_capacity = maximum_capacity
        self.renewable_asset = renewable_asset

        outputs = {
            self.bus_out_fuel: Flow(
                fix=input_timeseries,
                nominal_capacity=nv,
            )
        }

        super().__init__(label=name, outputs=outputs)
