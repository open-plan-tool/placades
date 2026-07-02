.. |age_installed| replace:: Number of years the asset has already been
    in operation. If the project lasts longer than its remaining
    lifetime, the replacement costs of the asset will be taken into
    account in a (Natural number).

.. |asset_type| replace:: Type of the component. [-] ().

.. |balanced| replace:: Defines whether the storage has balanced operation
    over the optimization period. [-] (Boolean).

.. |beta| replace:: Power loss index for CHPs, usually known as beta
    coefficient [-] (Between 0 and 1).

.. |bus_in| replace:: Connected Bus component for an input flow.
    [object].

.. |bus_in_electricity| replace:: Connected Bus component for the
    electricity input flow. [object].

.. |bus_in_fuel| replace:: Connected Bus component for the fuel input
    flow [object].

.. |bus_in_heat| replace:: Connected Bus component for the heat input
    flow. [object].

.. |bus_in_hydrogen| replace:: Connected Bus component for the hydrogen
    input flow. [object].

.. |bus_out| replace:: Connected Bus component for the output flow.
    [object].

.. |bus_out_electricity| replace:: Connected Bus component for the
    electricity output flow. [object].

.. |bus_out_fuel| replace:: Connected Bus component for the fuel output
    flow. [object].

.. |bus_out_heat| replace:: Connected Bus component for the heat output
    flow. [object].

.. |bus_out_hydrogen| replace:: Connected Bus component for the
    hydrogen output flow. [object].

.. |capex_fix| replace:: Planning and development costs. This could be
    planning and development costs which do not depend on the
    (optimized) capacities of the assets in € (Positive real number).

.. |capex_var| replace:: Specific investment costs of the asset related
    to the installed capacity (CAPEX) in €/:unit:.

.. |carrier| replace:: Energieträger/Medium like 'electricity', 'gas',
    'heat', 'hydrogen' [-] (string)

.. |cop| replace:: Coefficient of performance Ratio of energy output to
    energy input.

.. |crate| replace:: Maximum permissible power at which the storage can
    be charged or discharged relative to the nominal capacity of the
    storage. The C rate indicates the reciprocal of the time for which a
    battery of the specified capacity can be charged or discharged with
    the maximum charge or discharge current. A C-rate of 1 implies that
    the battery can be fully charged or discharged completely in a
    single timestep. A C-rate of 0.5 implies that the battery needs at
    least 2 timesteps to be fully charged or discharged [-] (Real
    number between 0 and 1).

.. |efficiency| replace:: Ratio of energy output to energy input. The
    battery efficiency is the ratio of the energy taken out from the
    battery to the energy put into the battery [-] (Positive real
    number).

.. |efficiency_charge| replace:: Efficiency of the charging process of the
    storage. It is used as inflow conversion factor [-] (Positive real
    number).

.. |efficiency_discharge| replace:: Efficiency of the discharging process of
    the storage. It is used as outflow conversion factor [-] (Positive real
    number).

.. |efficiency_electricity_chp| replace:: Electrical efficiency with
    maximal heat extraction [-] (Positive real number).

.. |efficiency_electricity_full_condensation| replace:: Electrical
    efficiency with no heat extraction [-] (Positive real number).

.. |efficiency_heat_chp| replace:: Thermal efficiency with maximal heat
    extraction [-] (Positive real number).

.. |energy_losses_absolute| replace:: Absolute fixed energy losses of the
    storage between two consecutive timesteps. [in :unit:] (Positive real
    number).

.. |energy_losses_absolute_investment| replace:: Fixed energy losses of the
    storage relative to the invested nominal capacity between two consecutive
    timesteps. [-] (Positive real number).

.. |energy_losses_relative| replace:: Relative energy losses of the storage
    between two consecutive timesteps. [-] (Real number between 0 and 1).

.. |energy_prics| replace:: Price of the energy carrier sourced from the
    utility grid. Can be also a timeseries in €/kWh.

.. |excess_cost| replace:: Text is missing.

.. |feedin_cap| replace:: Maximum flow for feeding electricity into the
    grid at any given timestep in kW (Acceptable values are either a
    positive real number or None).

.. |feedin_tariff| replace:: Price received for feeding electricity into
    the grid. Can be also a timeseries in €/kWh.

.. |fixed_thermal_losses_absolute| replace:: Thermal losses of the
    storage independent of the state of charge and independent of
    nominal storage capacity between two consecutive timesteps [-]
    (Between 0 and 1).

.. |fixed_thermal_losses_relative| replace:: Thermal losses of storage
    independent of state of charge between two consecutive timesteps
    relative to nominal storage capacity [-] (Between 0 and 1).

.. |input_timeseries| replace:: Timeseries. Timeseries in :unit:.

.. |installed_capacity| replace:: Already existing installed capacity.
    If the project lasts longer than its remaining lifetime, the
    replacement costs of the asset will be taken into account in
    :unit:.

.. |lifetime| replace:: Number of operational years of the asset until
    it has to be replaced in a (Natural number).

.. |maximum_capacity| replace:: Maximum total capacity of an asset that
    can be installed at the project site. This includes the already
    existing installed and additional capacity possible. An example
    would be that a roof can only carry 50 kW PV (maximum capacity),
    whereas the installed capacity is already 10 kW. The optimization
    would only be allowed to add 40 kW PV at maximum in :unit:
    (Acceptable values are either a positive real number or None.).

.. |maximum_capacity_investment| replace:: Maximum additional storage
    capacity that may be invested in at the project site in :unit:
    (Acceptable values are either a positive real number or
    float("+inf")).

.. |name| replace:: Name of the asset. [-] (Input the names in a
    computer friendly format, preferably with underscores instead of
    spaces, and avoiding special characters).

.. |opex_fix| replace:: Specific operational and maintenance costs of
    the asset related to the installed capacity (OPEX_fix) in
    €/(:unit: • a)

.. |opex_var| replace:: Costs associated with a flow through/from the
    asset (OPEX_var or fuel costs). This could be fuel costs for fuel
    sources like biogas or oil or operational costs for thermal power
    plants which only occur when operating the plant in €/kWh.

.. |optimize_cap| replace:: Choose if capacity optimization should be
    performed for this asset. [-] (Acceptable values are either Yes or
    No.).

.. |peak_demand_period| replace:: Number of reference periods in one
    year for peak demand pricing in times per year (Only one of the
    following are acceptable values: 1 (yearly), 2, 3 ,4, 6, 12
    (monthly)).

.. |peak_demand_pricing| replace:: Grid fee to be paid based on the
    peak demand of a given period in €/kW.

.. |project_data| replace:: The framework of the project in which the
    asset is ought to be optimized.

.. |renewable_asset| replace:: Choose if this asset should be
    considered as renewable. This parameter is necessary to consider the
    renewable share constraint correctly. [-] (Acceptable values are
    either Yes or No.).

.. |renewable_share| replace:: Share of renewables in the generation
    mix of the energy supplied by the DSO utility. [Factor] (Real
    number between 0 and 1).

.. |sco_max| replace:: The maximum permissible level of charge of the
    storage as a factor of the nominal capacity. When the battery is
    filled to its nominal capacity the state of charge is represented by
    the value 1 [-] (Real number between 0 and 1).

.. |shortage_cost| replace:: Text is missing

.. |soc_max| replace:: The maximum permissible level of charge of the storage
    as a factor of the nominal capacity. When the storage is filled to its
    nominal capacity the state of charge is represented by the value 1 [-]
    (Real number between 0 and 1).

.. |soc_min| replace:: The minimum permissible level of charge of the
    storage as a factor of the nominal capacity. When the battery is
    fully discharged the state of charge is represented by the value 0
    [-] (Real number between 0 and 1).

.. |theoretical_time_charge| replace:: Theoretical charging time of the
    storage at nominal charging power. [h] (Positive real number).

.. |theoretical_time_discharge| replace:: Theoretical discharging time of the
    storage at nominal discharging power. If not specified, it is set equal
    to theoretical_time_charge. [h] (Positive real number or None).

.. |thermal_loss_rate| replace:: Definition of thermal loss rate. [-]
    (numeric).

.. |<Parameter>| replace:: <Description> [<Unit>]
    (<Restriction>).
