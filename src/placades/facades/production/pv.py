import pandas as pd
import pvlib
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

        .. include:: docstring_parameter_description.rst

        Parameters
        ----------
        label : str
            Name of the asset.
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
            Choose if capacity optimization should be performed for
            this asset.
        maximum_capacity : float or None, default=None
            Maximum total capacity of an asset that can be installed
            at the project site.

        Examples
        --------
        >>> from oemof.solph import Bus
        >>> ebus = Bus(label="electricity_bus")

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



