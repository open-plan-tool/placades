from oemof.solph import Flow
from oemof.solph.components import Converter

from placades.investment import _create_invest_if_wanted


class ElectricalTransformator(Converter):
    def __init__(
        self,
        name,
        bus_in_electricity,
        bus_out_electricity,
        project_data,
        efficiency=0.3,
        age_installed=0,
        installed_capacity=0,
        capex_var=1000,
        capex_fix=0,
        opex_fix=10,
        opex_var=0,
        lifetime=20,
        optimize_cap=True,
        maximum_capacity=float("+inf"),
    ):
        """
        #         This is an Electrical transformator, e.g. for different voltage levels
        #
        #         This class represents an electrical conversion of any kind

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
                installed_capacity : float, default=0
                    Already existing installed capacity.
                capex_fix : float, default=1000
                    Specific investment costs of the asset related to the
                    installed capacity (CAPEX).
                capex_var : float, default=1000
                    Specific investment costs of the asset related to the
                    installed capacity (CAPEX).
                opex_fix : float, default=10
                    Specific operational and maintenance costs of the asset
                    related to the installed capacity (OPEX_fix).
                opex_var : float, default=0.01
                    Costs associated with a flow through/from the asset
                    (OPEX_var or fuel costs).
                lifetime : int, default=20
                    Number of operational years of the asset until it has to
                    be replaced.
                optimize_cap : bool, default=False
                    Choose if capacity optimization should be performed for
                    this asset.
                maximum_capacity : float or None, default=None
                    Maximum total capacity of an asset that can be installed
                    at the project site.
                efficiency : float, default=0.8
                    Ratio of energy output to energy input.

                Examples
                --------

                >>> from placades import Project
                >>> from oemof.solph import Bus
                >>> el_bus_in = Bus(label="el_bus_in")
                >>> el_bus_out = Bus(label="el_bus_out")
                >>> my_el_transformer = ElectricalTransformator(
                ...     name="ElectricalTransformator",
                ...     bus_in_electricity=el_bus_in,
                ...     bus_out_electricity=el_bus_out,
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
                ...         discount_factor=0.01),
                ...     )

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

        inputs = {bus_in_electricity: Flow()}

        outputs = {
            bus_out_electricity: Flow(
                nominal_capacity=nv,
                variable_costs=opex_var,
            )
        }

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
        super().__init__(
            label=name,
            outputs=outputs,
            inputs=inputs,
            conversion_factors={bus_out_electricity: efficiency},
        )


# from oemof.solph.components import Converter
#
#
# class ElectricalTransformator(Converter):
#     def __init__(
#         self,
#         name,
#         age_installed=0,
#         installed_capacity=0,
#         capex_fix=1000,
#         capex_var=1000,
#         opex_fix=10,
#         opex_var=0.01,
#         lifetime=20,
#         optimize_cap=False,
#         efficiency=0.8,
#     ):
#         """
#         Electrical transformator, e.g. for different voltage levels
#
#         This class represents an electrical conversion of any kind
#
#         .. important ::
#             The efficiency parameter significantly affects the overall
#             system performance.
#
#         :Structure:
#           *input*
#             1. from_bus : Electricity
#           *output*
#             1. to_bus : Electricity
#
#         Parameters
#         ----------
#         name : str
#             Name of the asset.
#         age_installed : int, default=0
#             Number of years the asset has already been in operation.
#         installed_capacity : float, default=0
#             Already existing installed capacity.
#         capex_fix : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         capex_var : float, default=1000
#             Specific investment costs of the asset related to the
#             installed capacity (CAPEX).
#         opex_fix : float, default=10
#             Specific operational and maintenance costs of the asset
#             related to the installed capacity (OPEX_fix).
#         opex_var : float, default=0.01
#             Costs associated with a flow through/from the asset
#             (OPEX_var or fuel costs).
#         lifetime : int, default=20
#             Number of operational years of the asset until it has to
#             be replaced.
#         optimize_cap : bool, default=False
#             Choose if capacity optimization should be performed for
#             this asset.
#         efficiency : float, default=0.8
#             Ratio of energy output to energy input.
#
#         Examples
#         --------
#         >>> from oemof.solph import Bus
#         >>> dc_bus = Bus(label="dc_bus")
#         >>> ac_bus = Bus(label="ac_bus")
#         >>> my_inverter = electrical_transformator(
#         ...     name="pv_inverter_01",
#         ...     installed_capacity=5000,
#         ...     efficiency=0.95,
#         ... )
#
#         """
#         self.name = name
#         self.age_installed = age_installed
#         self.installed_capacity = installed_capacity
#         self.capex_fix = capex_fix
#         self.capex_var = capex_var
#         self.opex_fix = opex_fix
#         self.opex_var = opex_var
#         self.lifetime = lifetime
#         self.optimize_cap = optimize_cap
#         self.efficiency = efficiency
#         super().__init__()
