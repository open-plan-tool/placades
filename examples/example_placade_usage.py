import logging
from pathlib import Path

from oemof.solph import EnergySystem
from oemof.solph import Model
from oemof.solph import processing
from oemof.solph.processing import parameter_as_dict
from oemof.tabular import datapackage  # noqa
from oemof.visio import ESGraphRenderer

from placades import TYPEMAP

logger = logging.getLogger(__name__)

results_path = "results"
scenario_name = "test_placade_example"
scenario_dir = "datapackage"

# create energy system object from the datapackage
es = EnergySystem.from_datapackage(
    Path(scenario_dir) / "datapackage.json",
    attributemap={},
    typemap=TYPEMAP,
)

# if ES_GRAPH is True:
energy_system_graph = Path(results_path) / f"{scenario_name}_energy_system.png"

es_graph = ESGraphRenderer(
    es, legend=True, filepath=energy_system_graph, img_format="png"
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

# extract parameters and results
params = parameter_as_dict(es)
es.results = processing.results(m)
es.dump(dpath=results_path, filename="oemof_raw")
