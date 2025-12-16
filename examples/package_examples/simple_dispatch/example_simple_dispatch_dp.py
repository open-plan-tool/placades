import logging
import warnings
from pathlib import Path

from oemof.network import graph
from oemof.solph import EnergySystem
from oemof.solph import Model
from oemof.solph import Results
from oemof.datapackage import datapackage
from oemof.tools.debugging import ExperimentalFeatureWarning
from oemof.visio import ESGraphRenderer

from placades import TYPEMAP

warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)
logger = logging.getLogger(__name__)

results_path = Path(Path.home(), "placades", "results")
scenario_name = "test_placade_example"
scenario_dir = "openPlan_package"
plot = "graph"  # "graph", "visio", None

Path.mkdir(results_path, parents=True, exist_ok=True)

# create energy system object from the datapackage
es = EnergySystem.from_datapackage(
    Path(scenario_dir) / "datapackage.json",
    attributemap={},
    typemap=TYPEMAP,
)

if plot == "graph":
    graph.create_nx_graph(
        es, filename=Path(results_path, "test_graph.graphml")
    )
elif plot == "visio":
    energy_system_graph = Path(
        results_path, f"{scenario_name}_energy_system.png"
    )

    es_graph = ESGraphRenderer(
        es, legend=False, filepath=str(energy_system_graph), img_format="png"
    )
    es_graph.render()

logger.info("Energy system created from datapackage")

# create model from energy system (this is just oemof.solph)
m = Model(es)


logger.info("Model created from energy system")

# # add constraints from datapackage to the model
# m.add_constraints_from_datapackage(
#     os.path.join(scenario_dir, "datapackage.json"),
#     constraint_type_map=CONSTRAINT_TYPE_MAP,
# )
# logger.info("Constraints added to model")


# select solver 'gurobi', 'cplex', 'glpk' etc
m.solve("cbc")

results = Results(m)
rdf = results.to_df("flow")

for n, m in [(0, 1), (1, 0)]:
    rdf.rename(
        columns={
            c[n]: c[n].label[-1]
            for c in rdf.columns
            if isinstance(c[n].label, tuple)
            and not isinstance(c[m].label, tuple)
        },
        level=n,
        inplace=True,
    )
elec_in = rdf[[c for c in rdf.columns if c[0] == "electricity"]]
elec_out = rdf[[c for c in rdf.columns if c[1] == "electricity"]]
print(elec_in.sum())
print(elec_out.sum())
print("*****************")
print("Input:", round(elec_in.sum().sum()))
print("Output:", round(elec_out.sum().sum()))
