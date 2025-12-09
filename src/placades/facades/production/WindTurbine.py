from placades import Source
from placades import Flow

from placades.investment import _create_invest_if_wanted


class WindTurbine(Source):
    """Windkraftanlage basierend auf Source"""

    def __init__(
        self,
        label,
        bus_out_electricity,
        wind_profile,
        age_installed=0,
        installed_capacity=0,
        capex_fix=None,
        capex_specific=None,
        opex_fix=None,
        opex_specific=None,
        dispatch_costs=0,
        lifetime=25,
        expandable=True,
        maximum_capacity=999999999,
        renewable_asset=True,
        project_data=None,
        fix=False,
    ):
        """
        Windkraftanlage (WKA) Facade

        Parameters
        ----------
        label : str or tuple
            Eindeutige Bezeichnung der WKA
        bus_out_electricity : oemof.solph.Bus
            Stromnetz-Bus
        installed_capacity : float
            Nennleistung der WKA in kW
        wind_profile : iterable
            Normalisierte Windleistung (0-1) als Zeitreihe
        fix : bool
            True = feste Erzeugung, False = flexible Abregelung möglich

        Examples
        --------
        >>> from placades import Bus
        >>> ebus = Bus(label="my_electricity_bus")
        """

        self.name = label
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_fix = capex_fix
        self.capex_specific = capex_specific
        self.opex_fix = opex_fix
        self.opex_specific = opex_specific
        self.dispatch_costs = dispatch_costs
        self.lifetime = lifetime
        self.optimize_cap = expandable
        self.maximum_capacity = maximum_capacity
        self.renewable_asset = renewable_asset
        self.normalised_output = wind_profile
        self.fix = fix

        nv = _create_invest_if_wanted(
            optimise_cap=expandable,
            capex_var=capex_specific,
            opex_fix=opex_specific,
            lifetime=lifetime,
            age_installed=age_installed,
            existing_capacity=installed_capacity,
            project_data=project_data,
        )

        self.bus_electricity = bus_out_electricity
        self.installed_capacity = installed_capacity
        self.wind_profile = wind_profile
        self.fix = fix
        if self.fix:
            fix = self.wind_profile
            vmax = None
        else:
            fix = None
            vmax = self.wind_profile

        outputs = {
            self.bus_electricity: Flow(
                max=vmax,
                fix=fix,
                nominal_capacity=nv,
            )
        }
        super().__init__(label=label, outputs=outputs)
