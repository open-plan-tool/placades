"""
CLI to (a) infer foreign keys & update an existing datapackage.json, or
(b) create datapackage.json from CSV files if it doesn't exist.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import datapackage as dp
from oemof.tabular.datapackage import building


def infer_only(
    dp_json: Path, fk_targets: list[str], sort_resources: bool = True
) -> None:
    print(f"[info] Inferring metadata on existing: {dp_json}")
    if not dp_json.exists():
        raise FileNotFoundError(f"datapackage.json not found at: {dp_json}")

    p = dp.Package(str(dp_json))
    building.infer_package_foreign_keys(p, fk_targets=fk_targets)

    p.descriptor["resources"].sort(key=lambda x: (x["path"], x["name"]))

    p.commit()
    p.save(str(dp_json))


def create_from_data(folder: Path, fk_targets: list[str]) -> None:
    print(f"[info] Creating datapackage.json in: {folder}")
    building.infer_metadata_from_data(
        package_name=folder.name,
        path=str(folder),
        fk_targets=fk_targets,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create or update a datapackage.json from the resources and infer foreign keys automatically."
    )
    parser.add_argument(
        "package_dir", help="Path to folder that contains datapackage.json"
    )

    parser.add_argument(
        "--fk-targets",
        nargs="+",
        default=["bus", "project"],
        help="Resource names as sources for potential foreign key targets (space-separated). By default 'bus' and 'project' are always here",
    )

    args = parser.parse_args(argv)

    folder = Path(args.package_dir).expanduser().resolve()
    dp_json = folder / "datapackage.json"

    if dp_json.exists():
        infer_only(dp_json, args.fk_targets)
    else:
        create_from_data(folder, args.fk_targets)


if __name__ == "__main__":
    main()
