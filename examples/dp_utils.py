import os

import datapackage as dp
from oemof.tabular.datapackage import building

COMPONENT_TEMPLATES_PATH = "openPlan_package"

dp_json = os.path.join(COMPONENT_TEMPLATES_PATH, "datapackage.json")

# will look for potential foreign keys target within those resources
fk_target_resources = ["bus", "project"]

if os.path.exists(dp_json):
    print("Only inferring metadata")
    p = dp.Package(dp_json)
    building.infer_package_foreign_keys(p, fk_targets=fk_target_resources)
    p.descriptor["resources"].sort(key=lambda x: (x["path"], x["name"]))
    p.commit()
    p.save(dp_json)
else:
    print("Creating datapackage.json")
    building.infer_metadata_from_data(
        package_name="OpenPlan test scenario",
        path=COMPONENT_TEMPLATES_PATH,
        fk_targets=fk_target_resources,
    )
