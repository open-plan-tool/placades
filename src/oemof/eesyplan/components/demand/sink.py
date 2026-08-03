from oemof.solph import Flow
from oemof.solph.components import Sink as SolphSink


class Sink(SolphSink):
    def __init__(
        self,
        name,
        project_data,
        bus_in,
        age_installed=0,
        installed_capacity=0,
        maximum_capacity=float("inf"),
        capex_spec=1000,
        opex_spec=10,
        variable_costs=0,
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
        name : string
            |name|
        project_data : Project object
            |project_data|
        bus_in : Node object
            |bus_in|
        age_installed : float or int, optional (default: 0)
            |age_installed|
        installed_capacity : float
            |installed_capacity|
        maximum_capacity : float, optional (default: float("+inf"))
            |maximum_capacity|
        capex_spec : float, optional (default: 0)
            |capex_spec|
        opex_spec : float, optional (default: 0)
            |opex_spec|
        variable_costs : float, optional (default: 0)
            |variable_costs|
        lifetime : int, optional (default: None)
            |lifetime|
        minimum : float, optional
            |minimum|
        maximum : float, optional
            |maximum|
        fix : float or iterable, optional
            |fix|
        positive_gradient_limit : float, optional
            |positive_gradient_limit|
        negative_gradient_limit : float, optional
            |negative_gradient_limit|
        full_load_time_max : float, optional
            |full_load_time_max|
        full_load_time_min : float, optional
            |full_load_time_min|
        integer : bool, optional
            |integer|
        custom_properties_flow : dict, optional
            |custom_properties_flow|
        custom_properties : dict, optional
            |custom_properties|

        Examples
        --------
        >>> from oemof.eesyplan import CarrierBus
        >>> from oemof.eesyplan import Project
        >>> bus = CarrierBus("Test", balanced=False)
        >>> project = Project(
        ...         name="Project_X", economic_period=20, tax=0,
        ...         discount_factor=0.01)
        >>> sink = Sink("test", project, bus)
        """
        nv = project_data.create_invest_if_wanted(
            capex_spec=capex_spec,
            opex_spec=opex_spec,
            lifetime=lifetime,
            installed_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
            project_data=project_data,
        )

        super().__init__(
            label=name,
            inputs={
                bus_in: Flow(
                    nominal_capacity=nv,
                    variable_costs=variable_costs,
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
