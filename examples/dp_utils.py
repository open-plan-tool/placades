import os

import datapackage as dp
from oemof.tabular.datapackage import building

COMPONENT_TEMPLATES_PATH = (
    "datapackage"  # os.path.abspath(os.path.dirname(__file__))
)

dp_json = os.path.join(COMPONENT_TEMPLATES_PATH, "datapackage.json")

if os.path.exists(dp_json):
    print("Only inferring metadata")
    p = dp.Package(dp_json)
    building.infer_package_foreign_keys(p)
    p.descriptor["resources"].sort(key=lambda x: (x["path"], x["name"]))
    p.commit()
    p.save(dp_json)
else:
    print("Creating datapackage.json")
    building.infer_metadata_from_data(
        package_name="OpenPlan test scenario",
        path=COMPONENT_TEMPLATES_PATH,
    )
