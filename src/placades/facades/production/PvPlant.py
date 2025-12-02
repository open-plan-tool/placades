from oemof.network import Source
from oemof.solph import Flow

from placades.investment import _create_invest_if_wanted


class PvPlant(Source):
    def __init__(
        self,
        label,  # automatic/default?
        bus_out_electricity,
        pv_production_timeseries,
        age_installed=0,
        installed_capacity=0,
        capex_specific=None,
        opex_specific=None,
        dispatch_costs=0,
        lifetime=25,
        expandable=False,
        maximum_capacity=None,
        project_data=None,
        fix=False,
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
          The characteristic quantity of the optimization is the *nominal power-output* of the PV-plant given in kWp

        .. include:: docstring_parameter_description.rst

        Parameters
        ----------
        label : str
            |name|
        age_installed : int, default=0
            |age_installed|
        installed_capacity : float, default=0
            Already existing installed capacity.
        capex_specific : float, default=1000
            |capex_fix|
        opex_specific : float, default=0.01
            |opex_fix|
        lifetime : int, default=25
            |lifetime|
        expandable : bool, default=True
            |expandable|
        maximum_capacity : float or None, default=None
            |maximum_capacity|
        fix : bool, default=False
            |fix|
        dispatch_costs: float, default=0
            |dispatch_costs|
        project_data: (str, int, float, float), default=None
            |project_data|



        Examples
        --------
        >>> from oemof.solph import Bus
        >>> from oemof.network import Source
        >>> ebus = Bus(label="electricity_bus")
        >>> my_pv = PvPlant(
        >>>     label="my_py_plant",
        >>>     bus_out_electricity=ebus,
        >>>     pv_production_timeseries="PV.csv",
        >>>     age_installed=0, #a
        >>>     installed_capacity=0, #a
        >>>     capex_specific=1000, #€/kWp
        >>>     opex_specific=10, # €/kWp/a
        >>>     dispatch_costs=0, # €/kWh
        >>>     lifetime=25, #a
        >>>     expandable=True,
        >>>     maximum_capacity=1000, #kWp
        >>>     project_data=(name="Project_X", lifetime=20, tax=0, discount_factor=0.01), #Projectdata
        >>>     fix=False)

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
        if fix:
            fix = pv_production_timeseries
            vmax = None
        else:
            fix = None
            vmax = pv_production_timeseries

        outputs = {
            bus_out_electricity: Flow(
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
        self.normalised_output = pv_production_timeseries
        self.fix = fix

        super().__init__(label=label, outputs=outputs)



