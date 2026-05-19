import logging

import pandas as pd
from datapackage import Package

from oemof.eesyplan import CarrierBus
from oemof.eesyplan import import_results
from oemof.eesyplan.datapackage.energy_system import (
    create_energy_system_from_dp,
)
from oemof.solph.buses import Bus

RAW_OUTPUTS = ["investments"]
PROCESSED_RAW_OUTPUTS = ["flow_min", "flow_max", "aggregated_flow"]

RAW_INPUTS = [
    "efficiency",
    "age_installed",
    "installed_capacity",
    "capex_var",
    "capex_fix",
    "opex_fix",
    "opex_var",
    "lifetime",
    "optimize_cap",
    "maximum_capacity",
]


# Functions for results per component
def compute_capacity_total(results_df):
    """Calculates total capacity by adding existing capacity (capacity) to optimized capacity (investments)"""
    investments = results_df.investments
    if investments is None:
        investments = 0

    return results_df.installed_capacity + investments


def compute_capacity_added(results_df):
    """Calculates duplicate optimized capacity (investments) into a column with a better name"""
    investments = results_df.investments
    if investments is None:
        investments = 0
    return investments


def compute_annuity_total(results_df):
    """Calculates total annuity by multiplying the annuity by the optimized capacity"""
    investments = results_df.investments
    if investments is None:
        investments = 0

    return results_df.capex_var * investments


CALCULATED_OUTPUTS = [
    {
        "column_name": "capacity_total",
        "operation": compute_capacity_total,
        "description": "The total capacity is calculated by adding the optimized capacity (investments) "
        "to the existing capacity (capacity)",
        "argument_names": ["investments", "capacity"],
    },
    {
        "column_name": "capacity_added",
        "operation": compute_capacity_added,
        "description": "The optimized capacity column is duplicated with a better name than 'investments'",
        "argument_names": ["investments"],
    },
    {
        "column_name": "annuity_total",
        "operation": compute_annuity_total,
        "description": "Total annuity is calculated by multiplying the optimized capacity "
        "by the capacity cost (annuity considering CAPEX, OPEX and WACC)",
        "argument_names": ["investments", "capacity_cost"],
    },
]



def construct_dataframe_from_results(results_path, es_dp_path):
    """

    Parameters
    ----------
    results_path: path to the results datapackage
    es_dp_path: path to the energy_system datapackage


    Returns
    -------
    Dataframe with oemof result sequences's timestamps as columns as well as investment and a multi-index built automatically, see construct_multi_index_levels for more information on the multi-index
    """

    p = Package(str(es_dp_path))
    mi_levels = ["bus", "direction", "asset", "carrier", "facade_type"]

    energy_system = create_energy_system_from_dp(es_dp_path)

    results = import_results(results_path, energy_system)

    # read information about bus carriers from the busses
    busses_info = {
        n.label: n.carrier
        for n in energy_system.nodes
        if isinstance(n, CarrierBus) and n.depth == 0
    }

    # read information about assets from the datapackage
    asset_info = {}
    for r in p.resources:
        if "/elements/" in r.descriptor["path"] and r.name != "bus":
            for asset in r.read(keyed=True):
                asset_info[asset["name"]] = asset["type"]

    df = results["flow"].T
    # reformat the columns
    df.columns = list(df.columns)

    # prepare the new multi-index of the dataframe
    investments_df = results["invest"]
    investments = []
    flows = []
    for co in df.index:
        if isinstance(co[0], CarrierBus) or isinstance(co[0], Bus):
            bus = co[0]
            asset = co[1]
            # going from bus to asset, so the flow goes in to the asset
            idx = (bus, "in", asset)

        elif isinstance(co[1], CarrierBus) or isinstance(co[1], Bus):
            bus = co[1]
            asset = co[0]
            # going from asset to bus, so the flow goes out of the asset
            idx = (bus, "out", asset)

        if asset in investments_df:
            investments.append(investments_df[asset].iloc[0])
        else:
            investments.append(None)

        if bus.label in busses_info:
            idx = (*idx, busses_info[bus.label])
        else:
            idx = (*idx, None)

        if asset.label in asset_info:
            idx = (*idx, asset_info[asset.label])
        elif asset.parent.label in asset_info:
            idx = (*idx, asset_info[asset.parent.label])
        else:
            idx = (*idx, None)
        flows.append(idx)

    mindex = pd.MultiIndex.from_tuples(flows, names=mi_levels)

    df.index = mindex

    df["investments"] = investments
    return df


def process_raw_results(df_results):
    """Compute the min, max and aggregated flows for each asset-bus pair

    Parameters
    ----------
    df_results: pandas DataFrame
        the outcome of construct_dataframe_from_results()

    Returns
    -------
    """
    temp = df_results[df_results.columns.difference(RAW_OUTPUTS)]
    df_results["flow_min"] = temp.min(axis=1)
    df_results["flow_max"] = temp.max(axis=1)
    df_results["aggregated_flow"] = temp.sum(axis=1)
    return df_results


def process_raw_inputs(
    df_results, es_dp_path, raw_inputs=RAW_INPUTS, typemap=None
):
    """Find the input parameters from the datapackage.json file


    Parameters
    ----------
    df_results: pandas DataFrame
        the outcome of construct_dataframe_from_results()
    es_dp_path: string
        path to the datapackage.json file
    raw_inputs: list of string
        list of parameters from the datapackage one would like to collect for result post-processing

    Returns
    -------

    """
    if typemap is None:
        typemap = {}

    p = Package(str(es_dp_path))
    # initialise inputs_df with raw inputs as indexes
    inputs_df = pd.DataFrame(index=raw_inputs)
    # inputs_df = None
    for r in p.resources:
        if "elements" in r.descriptor["path"] and r.name != "bus":
            df = pd.DataFrame.from_records(r.read(keyed=True), index="name")
            resource_inputs = df[
                list(set(raw_inputs).intersection(set(df.columns)))
            ].T
            if inputs_df is None:
                if not resource_inputs.empty:
                    inputs_df = resource_inputs
            else:
                inputs_df = inputs_df.join(resource_inputs)
            # if r.name in typemap:
            # TODO here test if facade_type has the method 'validate_datapackage'
            #   inputs_df = typemap[r.name].processing_raw_inputs(r, inputs_df)

    # kick out the lines where all values are NaN
    inputs_df = inputs_df.dropna(how="all")
    # append the inputs of the datapackage to the results DataFrame
    inputs_df.T.index.name = "asset"
    # TODO does not work for inputs which are timeseries (ie for moo)
    return df_results.join(inputs_df.T.apply(pd.to_numeric, downcast="float"))


def _validate_calculation(calculation):
    """Check if the parameters of a calculation are there and of the right format"""
    var_name = calculation.get("column_name", None)
    fhandle = calculation.get("operation", None)

    if var_name is None:
        raise ValueError(
            f"The 'column_name' under which the calculation should be saved in the results DataFrame is missing from the calculation dict: {calculation}. Please check your input or look at help(apply_calculations) for the formatting of the calculation dict"
        )

    if not callable(fhandle):
        raise ValueError(
            f"The provided function handle for calculation of column '{var_name}' is not callable"
        )


def _check_arguments(df, column_names, col_name):
    """Check that all required argument are present in the DataFrame columns"""
    for arg in column_names:
        if arg not in df.columns:
            raise AttributeError(
                f"The column {arg} is not present within the results DataFrame and is required to compute '{col_name}', listed in the calculations to be executed"
            )


def apply_calculations(results_df, calculations=None):
    """Apply calculation and populate the columns of the results_df

    Parameters
    ----------
    df_results: pandas DataFrame
        the outcome of process_raw_input()
    calculations: list of dict
        each dict should contain
            "column_name" (the name of the new column within results_df),
            "operation" (handle of a function which will be applied row-wise to results_df),
            "description" (a string for documentation purposes)
            and "argument_names" (list of columns needed within results_df)

    Returns
    -------

    """
    if calculations is None:
        calculations = []

    for calc in calculations:
        _validate_calculation(calc)
        var_name = calc.get("column_name")
        argument_names = calc.get("argument_names", [])
        func_handle = calc.get("operation")
        try:
            _check_arguments(
                results_df, column_names=argument_names, col_name=var_name
            )
        except AttributeError as e:
            logging.warning(e)
            continue

        results_df[var_name] = results_df.apply(
            func_handle,
            axis=1,
        )
        # ToDo: I've commented this out for now but decide if this or some form should be kept in
        # # check if the new column contains all None values and remove it if so
        # if results_df[var_name].isna().all():
        #     results_df.drop(columns=[var_name], inplace=True)
        #     logging.info(
        #         f"Removed column '{var_name}' because it contains all None values."
        #     )


def apply_kpi_calculations(results_df, calculations=None):
    """Apply calculation and return a new DataFrame with the KPIs.

    Parameters
    ----------
    results_df : pd.DataFrame
        The input DataFrame with raw data.
    calculations : list of dict
        List of calculations to be applied. Each calculation is a dictionary
        with keys: "column_name", "argument_names", and "operation".

    Returns
    -------
    pd.DataFrame
        A new DataFrame containing the calculated KPI values with var_name as the index.
    """

    if calculations is None:
        calculations = []

    kpis = []

    for calc in calculations:
        _validate_calculation(calc)
        var_name = calc.get("column_name")
        argument_names = calc.get("argument_names", [])
        func_handle = calc.get("operation")

        try:
            _check_arguments(
                results_df, column_names=argument_names, col_name=var_name
            )
        except AttributeError as e:
            logging.warning(e)
            continue

        kpi_value = func_handle(results_df)
        kpis.append({"kpi": var_name, "value": kpi_value})

    if kpis:
        answer = pd.DataFrame(kpis).set_index("kpi")
    else:
        answer = None
    return answer


class Calculator:
    def __init__(self, results_path, es_dp_path):
        es_dp_path = es_dp_path / "datapackage.json"
        self.df_results = construct_dataframe_from_results(
            results_path, es_dp_path
        )
        self.n_timesteps = len(self.df_results.columns) - 1

        self.df_results = process_raw_results(self.df_results)
        self.df_results = process_raw_inputs(self.df_results, es_dp_path)
        self.kpis = None

    def apply_calculations(self, calculations):
        apply_calculations(self.df_results, calculations=calculations)

    def apply_kpi_calculations(self, calculations):
        self.kpis = apply_kpi_calculations(
            self.df_results, calculations=calculations
        )

    def __scalars(self, scalar_category):
        """Ignore the flow data columns (by construction those are the first columns after the multi-index)"""
        scalars = self.df_results.iloc[:, self.n_timesteps :]
        answer = scalars
        if scalar_category == "raw_inputs":
            existing_cols = []
            for c in scalars.columns:
                if c in RAW_INPUTS:
                    existing_cols.append(c)
            answer = scalars[existing_cols]
        elif scalar_category == "outputs":
            answer = scalars[scalars.columns.difference(RAW_INPUTS)]
        return answer

    @property
    def raw_outputs(self):
        self.df_results.iloc[:, : self.n_timesteps]
        cols = self.df_results.iloc[:, : self.n_timesteps].columns.tolist()
        cols = cols + RAW_OUTPUTS + PROCESSED_RAW_OUTPUTS
        return self.df_results[cols]

    @property
    def raw_inputs(self):
        return self.__scalars("raw_inputs")

    @property
    def calculated_outputs(self):
        return self.__scalars("outputs")
