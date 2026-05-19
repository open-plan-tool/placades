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
