from oemof.solph import Flow
from oemof.solph.components import Converter


class ElectricalTransformator(Converter):
    def __init__(
        self,
        name,
        bus_in_electricity,
        bus_out_electricity,
        project_data,
        efficiency=0.3,
        age_installed=0,
        installed_capacity=None,
        maximum_capacity=None,
        capex_spec=1000,
        opex_spec=10,
        variable_costs=0,
        lifetime=20,
    ):
        """
        This is an Electrical transformator, e.g. for different voltage levels

        This class represents an electrical conversion of any kind

        .. important ::
            The efficiency parameter determines the conversion rate
            from gas to electrical output.

        :Structure:
          *input*
            1. from_bus : Electricity
          *output*
            1. to_bus : Electricity

        :Optimization:
          The characteristic quantity of the optimization is the *maximum
          power-output* of the Transformer given in kW

        Parameters
        ----------
        name : str
            Name of the asset.
        age_installed : int, default=0
            Number of years the asset has already been in operation.
        installed_capacity : float or None (default: None)
            |installed_capacity|
        maximum_capacity : float or None (default: None)
            |maximum_capacity|
        capex_spec : float, default=1000
            Specific investment costs of the asset related to the
            installed capacity (CAPEX).
        opex_spec : float, default=10
            Specific operational and maintenance costs of the asset
            related to the installed capacity (opex_spec).
        variable_costs : float, default=0.01
            Costs associated with a flow through/from the asset
            (variable_costs or fuel costs).
        lifetime : int, default=20
            Number of operational years of the asset until it has to
            be replaced.
        efficiency : float, default=0.8
            Ratio of energy output to energy input.

        Examples
        --------

        >>> from oemof.eesyplan import Project
        >>> from oemof.solph import Bus
        >>> el_bus_in = Bus(label="el_bus_in")
        >>> el_bus_out = Bus(label="el_bus_out")
        >>> my_el_transformer = ElectricalTransformator(
        ...     name="ElectricalTransformator",
        ...     bus_in_electricity=el_bus_in,
        ...     bus_out_electricity=el_bus_out,
        ...     age_installed=0,
        ...     maximum_capacity=1000,
        ...     capex_spec=1000,
        ...     opex_spec=1000,
        ...     lifetime=20,
        ...     efficiency=0.9,
        ...     variable_costs=0,
        ...     project_data=Project(
        ...         name="Project_X", economic_period=20, tax=0,
        ...         discount_factor=0.01),
        ...     )

        """
        nv = project_data.create_invest_if_wanted(
            capex_spec=capex_spec,
            opex_spec=opex_spec,
            lifetime=lifetime,
            installed_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
        )

        inputs = {bus_in_electricity: Flow()}

        outputs = {
            bus_out_electricity: Flow(
                nominal_capacity=nv,
                variable_costs=variable_costs,
            )
        }

        self.name = name
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity

        self.capex_spec = capex_spec
        self.opex_spec = opex_spec
        self.variable_costs = variable_costs
        self.lifetime = lifetime
        self.maximum_capacity = maximum_capacity
        self.efficiency = efficiency
        super().__init__(
            label=name,
            outputs=outputs,
            inputs=inputs,
            conversion_factors={bus_out_electricity: efficiency},
        )
