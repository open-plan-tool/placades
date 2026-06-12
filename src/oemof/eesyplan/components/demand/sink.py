from oemof.eesyplan.investment import _create_invest_if_wanted
from oemof.solph import Flow
from oemof.solph.components import Sink as SolphSink


class Sink(SolphSink):
    def __init__(
        self,
        name,
        project_data,
        bus_in,
        optimize_cap=False,
        age_installed=0,
        installed_capacity=0,
        maximum_capacity=float("inf"),
        capex_var=1000,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        minimum=None,
        maximum=None,
        fix=None,
        positive_gradient_limit=None,
        negative_gradient_limit=None,
        full_load_time_max=None,
        full_load_time_min=None,
        integer=False,
        custom_properties_flow=None,
        custom_properties=None,
    ):
        """

        Parameters
        ----------
        name
        project_data
        bus_in
        optimize_cap
        age_installed
        installed_capacity
        maximum_capacity
        capex_var
        opex_fix
        opex_var
        lifetime
        minimum
        maximum
        fix
        positive_gradient_limit
        negative_gradient_limit
        full_load_time_max
        full_load_time_min
        integer
        custom_properties_flow
        custom_properties

        Examples
        --------
        >>> from oemof.eesyplan import CarrierBus
        >>> from oemof.eesyplan import Project
        >>> bus = CarrierBus("Test", balanced=False)
        >>> project = Project(
        ...         name="Project_X", lifetime=20, tax=0,
        ...         discount_factor=0.01)
        >>> sink = Sink("test", project, bus)
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

        super().__init__(
            label=name,
            inputs={
                bus_in: Flow(
                    nominal_capacity=nv,
                    variable_costs=opex_var,
                    minimum=minimum,
                    maximum=maximum,
                    fix=fix,
                    positive_gradient_limit=positive_gradient_limit,
                    negative_gradient_limit=negative_gradient_limit,
                    full_load_time_max=full_load_time_max,
                    full_load_time_min=full_load_time_min,
                    integer=integer,
                    custom_properties=custom_properties_flow,
                )
            },
            parent_node=None,
            custom_properties=custom_properties,
        )
