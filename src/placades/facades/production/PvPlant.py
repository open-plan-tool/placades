from placades import Flow
from placades import Source

from placades.import_functions import create_timeseries
from placades.investment import _create_invest_if_wanted


class PvPlant(Source):
    def __init__(
        self,
        label,
        bus_out,
        normed_production_timeseries,
        age_installed=0,
        installed_capacity=0,
        capex_specific=None,
        opex_specific=None,
        dispatch_costs=0,
        lifetime=25,
        expandable=False,
        maximum_capacity=None,
        curtailable=True,
        project_data=None,
    ):
        """
        Photovoltaic power plant for solar electricity generation.

        This class represents a photovoltaic plant that converts solar
        irradiation into electrical energy using photovoltaic panels.

        .. important ::
            This is a renewable energy source that contributes to the
            renewable share of the system.

        :Structure:
          *output*
            1. to_bus : Electricity

        :Optimization:
          The characteristic quantity of the optimization is the *nominal
          power-output* of the PV-plant given in kWp

        .. include:: docstring_parameter_description.rst

        Parameters
        ----------
        label : str
            |name|
        bus_out : bus object
            |bus_out|
        normed_production_timeseries: array-like
            |normed_production_timeseries|
        age_installed : int, default=0
            |age_installed|
        installed_capacity : float, default=0
            |installed_capacity|
        capex_specific : float, default=1000
            |capex_fix|
        opex_specific : float, default=0.01
            |opex_fix|
        dispatch_costs: float, default=0
            |dispatch_costs|
        lifetime : int, default=25
            |lifetime|
        expandable : bool, default=True
            |expandable|
        maximum_capacity : float or None, default=None
            |maximum_capacity|
        curtailable : bool, default=False
            |curtailable|
        project_data: Project object, default=None
            |project_data|


        Examples
        --------
        >>> from placades import Project
        >>> from oemof.solph import Bus
        >>> el_bus = Bus(label="electricity_bus")
        >>> my_pv = PvPlant(
        ...     label="my_py_plant",
        ...     bus_out=el_bus,
        ...     normed_production_timeseries=[1,0.5,0.9],
        ...     age_installed=0, #a
        ...     installed_capacity=0, #a
        ...     capex_specific=1000, #€/kWp
        ...     opex_specific=10, # €/kWp/a
        ...     dispatch_costs=0, # €/kWh
        ...     lifetime=25, #a
        ...     expandable=True,
        ...     maximum_capacity=1000, #kWp
        ...     curtailable=True,
        ...     project_data=Project(
        ...         name="Project_X", lifetime=20, tax=0,
        ...         discount_factor=0.01),
        ...  )

        """

        nv = _create_invest_if_wanted(
            optimise_cap=expandable,
            capex_var=capex_specific,
            opex_fix=opex_specific,
            lifetime=lifetime,
            age_installed=age_installed,
            existing_capacity=installed_capacity,
            project_data=project_data,
        )

        fix, vmax = create_timeseries.apply_curtailability_if_wanted(
            normed_production_timeseries, curtailable
        )

        outputs = {
            bus_out: Flow(
                fix=fix,
                max=vmax,
                nominal_capacity=nv,
                variable_costs=dispatch_costs,
            )
        }

        self.name = label
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_specific = capex_specific
        self.opex_specific = opex_specific
        self.dispatch_costs = dispatch_costs
        self.lifetime = lifetime
        self.optimize_cap = expandable
        self.maximum_capacity = maximum_capacity
        self.renewable_asset = True
        self.normalised_output = normed_production_timeseries
        self.fix = fix

        super().__init__(label=label, outputs=outputs)
