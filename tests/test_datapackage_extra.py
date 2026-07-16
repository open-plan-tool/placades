import shutil
import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

from oemof.eesyplan.datapackage.energy_system import (
    cli,
    create_energy_system_from_dp,
    es_to_graphml,
    plot_es,
    solve_energy_system_from_dp,
)

DATA_PATH = Path(__file__).parent / "test_data"
DP_DIR = DATA_PATH / "openPlan_package"
DP_JSON = DP_DIR / "datapackage.json"
DP_ZIP = DATA_PATH / "dp_test.zip"


@pytest.fixture
def zip_datapackage():
    if DP_ZIP.exists():
        DP_ZIP.unlink()
    shutil.make_archive(
        DP_ZIP.with_suffix(""), "zip", DP_DIR.parent, DP_DIR.name
    )
    yield DP_ZIP
    if DP_ZIP.exists():
        DP_ZIP.unlink()


def test_create_es_from_non_json_path():
    es = create_energy_system_from_dp(DP_DIR)
    assert es is not None


def test_es_to_graphml():
    es = create_energy_system_from_dp(DP_JSON)
    out = Path("/tmp/test_output")
    out.mkdir(exist_ok=True)
    try:
        es_to_graphml(es, out / "test")
        assert (out / "test.graphml").exists()
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_solve_with_results_path():
    out = Path("/tmp/test_results_output")
    if out.exists():
        shutil.rmtree(out)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        result = solve_energy_system_from_dp(
            path=DP_JSON, results_path=out
        )
    assert result == out
    assert out.exists()
    shutil.rmtree(out, ignore_errors=True)


def test_solve_no_plot_no_results():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        result = solve_energy_system_from_dp(path=DP_JSON)
    assert result is not None


def test_solve_with_plot_graph():
    out = Path("/tmp/test_graph_output")
    out.mkdir(exist_ok=True)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            result = solve_energy_system_from_dp(
                path=DP_JSON, plot="graph", results_path=out
            )
        assert result is not None
    finally:
        shutil.rmtree(out, ignore_errors=True)


@patch(
    "oemof.eesyplan.datapackage.energy_system.ESGraphRenderer",
    None,
)
def test_plot_es_raises_without_visio():
    es = create_energy_system_from_dp(DP_JSON)
    with pytest.raises(ModuleNotFoundError, match="oemof-viso"):
        plot_es(es, "/tmp/test_path")


def test_solve_with_plot_visio():
    mock_renderer = patch(
        "oemof.eesyplan.datapackage.energy_system.ESGraphRenderer"
    )
    with mock_renderer as MockRenderer:
        instance = MockRenderer.return_value
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            result = solve_energy_system_from_dp(
                path=DP_JSON, plot="visio"
            )
        assert result is not None
        MockRenderer.assert_called_once()
        instance.render.assert_called_once()


def test_cli_with_directory(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "cli",
            str(DP_DIR),
            "-p", "graph",
        ],
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        cli()


def test_cli_with_json_file(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "cli",
            str(DP_JSON),
            "-p", "graph",
        ],
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        cli()


def test_cli_with_output(monkeypatch):
    out = Path("/tmp/test_cli_output")
    if out.exists():
        shutil.rmtree(out)
    monkeypatch.setattr(
        "sys.argv",
        [
            "cli",
            str(DP_DIR),
            "-p", "graph",
            "-o", str(out),
        ],
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        cli()
    assert out.exists()
    shutil.rmtree(out, ignore_errors=True)
