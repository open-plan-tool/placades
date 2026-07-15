from oemof.eesyplan.investment import _create_invest_if_wanted
from oemof.solph import Flow
from oemof.solph.components import Converter


# TODO: Decide whether FuelCell should support an optional waste-heat output (e.g. bus_out_heat, efficiency_heat).
class FuelCell(Converter):
    def __init__(
        self,
        name,
        bus_in_h2,
        bus_out_electricity,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        capex_fix=0,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=True,
        efficiency=0.8,
        maximum_capacity=float("+inf"),
        project_data=None,
    ):
        """
        Fuel cell for electricity generation.

        This class represents a fuel cell that converts hydrogen or other
        fuels into electrical energy through electrochemical processes.

        .. important ::
            The efficiency of fuel cells is typically higher than
            combustion-based generators.

        :Structure:
          *input*
            1. bus_in_h2 : H2
          *output*
            1. bus_out_electricity : Electricity

        Parameters
        ----------
        name : str
            Name of the asset.
        age_installed : int, default=0
            Number of years the asset has already been in operation.
        installed_capacity : float, default=0
            Already existing installed capacity.
        capex_fix : float, default=1000
            Specific investment costs of the asset related to the
            installed capacity (CAPEX).
            # TODO(review) [dringend]: Docstring widerspricht der Signatur:
            # Im Code ist `capex_fix=0`, hier steht `default=1000`.
            # Bitte korrigieren.
        capex_var : float, default=1000
            Specific investment costs of the asset related to the
            installed capacity (CAPEX).
        opex_fix : float, default=10
            Specific operational and maintenance costs of the asset
            related to the installed capacity (OPEX_fix).
        opex_var : float, default=0.01
            Costs associated with a flow through/from the asset
            (OPEX_var or fuel costs).
            # TODO(review) [dringend]: Docstring widerspricht der Signatur:
            # Im Code ist `opex_var=0`, hier steht `default=0.01`.
        lifetime : int, default=20
            Number of operational years of the asset until it has to
            be replaced.
        optimize_cap : bool, default=False
            Choose if capacity optimization should be performed for
            this asset.
            # TODO(review) [dringend]: Docstring widerspricht der Signatur:
            # Im Code ist `optimize_cap=True`, hier steht `default=False`.
            # Bitte fachlich bestätigen, welcher Default gewollt ist.
        maximum_capacity : float or None, default=None
            Maximum total capacity of an asset that can be installed
            at the project site.
            # TODO(review) [dringend]: Auch hier Widerspruch zur Signatur:
            # Im Code ist `float("+inf")`, im Docstring `None`.
            # API-Semantik bitte vereinheitlichen.
        efficiency : float, default=0.8
            Ratio of energy output to energy input.

        Examples
        --------
        >>> from oemof.eesyplan import Project
        >>> from oemof.solph import Bus
        >>> h2_bus = Bus(label="hydrogen_bus")
        >>> el_bus = Bus(label="electricity_bus")
        >>> my_fuel_cell = FuelCell(
        ...     name="hydrogen_fuel_cell",
        ...     bus_in_h2=h2_bus,
        ...     bus_out_electricity=el_bus,
        ...     age_installed=0,
        ...     installed_capacity=0,
        ...     capex_var=1000,
        ...     opex_fix=1000,
        ...     lifetime=20,
        ...     maximum_capacity=None,
        ...     efficiency=0.9,
        ...     opex_var=0,
        ...     optimize_cap=True,
        ...     project_data=Project(
        ...         name="Project_X", lifetime=20, tax=0,
        ...         discount_factor=0.01,
        ...     )
        ... )
        """
        # TODO(review) [wichtig]: Es fehlt durchgehend Eingabevalidierung
        # für name, Busse, Kostenparameter, lifetime, capacities und bools.
        # Bitte prüfen, ob diese Komponente an die übrigen validierten
        # Komponenten angeglichen werden soll.

        nv = _create_invest_if_wanted(
            optimise_cap=optimize_cap,
            # TODO(review) [nice-to-have]: Öffentliche API nutzt
            # `optimize_cap`, der Helper aber `optimise_cap`.
            # Mittelfristig vereinheitlichen.
            capex_var=capex_var,
            opex_fix=opex_fix,
            lifetime=lifetime,
            age_installed=age_installed,
            existing_capacity=installed_capacity,
            maximum_capacity=maximum_capacity,
            project_data=project_data,
        )

        # TODO(review) [dringend]: `capex_fix` wird hier nicht verwendet,
        # obwohl es Teil der öffentlichen API ist und später gespeichert wird.
        # Bitte entscheiden:
        # - bewusst ungenutzt für API-Kompatibilität?
        # - Implementierung unvollständig?
        # - Parameter entfernen?
        # TODO(review) [wichtig]: Es fehlt eine Konsistenzprüfung
        # `maximum_capacity >= installed_capacity`. Bitte bestätigen, ob das
        # zentral garantiert wird oder hier geprüft werden sollte.

        inputs = {bus_in_h2: Flow()}

        outputs = {
            bus_out_electricity: Flow(
                nominal_capacity=nv,
                variable_costs=opex_var,
            )
        }

        # TODO(review) [wichtig]: Bitte bestätigen, dass sich
        # `installed_capacity` und `maximum_capacity` bewusst auf die
        # elektrische Ausgangsleistung beziehen.

        self.name = name
        self.age_installed = age_installed
        self.installed_capacity = installed_capacity
        self.capex_fix = capex_fix
        self.capex_var = capex_var
        self.opex_fix = opex_fix
        self.opex_var = opex_var
        self.lifetime = lifetime
        self.maximum_capacity = maximum_capacity
        self.efficiency = efficiency
        # TODO(review) [mittel]: `optimize_cap` wird verwendet, aber nicht als
        # Attribut gespeichert. Bitte prüfen, ob das bewusst so ist oder ob
        # `self.optimize_cap` zur Konsistenz mit anderen Komponenten fehlt.

        super().__init__(
            label=name,
            outputs=outputs,
            inputs=inputs,
            conversion_factors={bus_out_electricity: efficiency},
            # TODO(review) [dringend]: `efficiency` wird nicht validiert.
            # Bitte festlegen, ob hier nur 0 < efficiency <= 1 zulässig ist.
            # Ohne Prüfung sind auch 0, negative oder >1-Werte möglich.
        )
