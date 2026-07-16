import pytest

from oemof.eesyplan import Project
from oemof.eesyplan.investment import (
    _create_invest_if_wanted,
    calculate_annuity_mvs,
    crf,
)


def _make_project():
    return Project(
        name="test_project", lifetime=20, tax=0, discount_factor=0.01
    )


def test_crf_with_nonzero_discount():
    result = crf(20, 0.05)
    assert result > 0


def test_crf_with_zero_discount():
    result = crf(20, 0.0)
    assert result == 1 / 20


def test_create_invest_optimize_cap_true():
    project = _make_project()
    result = _create_invest_if_wanted(
        optimise_cap=True,
        existing_capacity=0,
        project_data=project,
        capex_var=1000,
        opex_fix=10,
        lifetime=20,
        age_installed=0,
    )
    assert float(result.maximum[0]) == float("+inf")
    assert float(result.minimum[0]) == 0


def test_create_invest_optimize_cap_false():
    project = _make_project()
    result = _create_invest_if_wanted(
        optimise_cap=False,
        existing_capacity=500,
        project_data=project,
        capex_var=1000,
        opex_fix=10,
        lifetime=20,
        age_installed=0,
    )
    assert float(result.maximum[0]) == 500
    assert float(result.minimum[0]) == 500


def test_create_invest_optimize_cap_with_existing_capacity_raises():
    project = _make_project()
    with pytest.raises(
        ValueError,
        match="When optimizing an asset no existing capacity",
    ):
        _create_invest_if_wanted(
            optimise_cap=True,
            existing_capacity=100,
            project_data=project,
            capex_var=1000,
            opex_fix=10,
            lifetime=20,
            age_installed=0,
        )


def test_create_invest_optimize_cap_with_age_installed_raises():
    project = _make_project()
    with pytest.raises(
        ValueError,
        match="When optimizing an asset no existing capacity",
    ):
        _create_invest_if_wanted(
            optimise_cap=True,
            existing_capacity=0,
            project_data=project,
            capex_var=1000,
            opex_fix=10,
            lifetime=20,
            age_installed=5,
        )


def test_create_invest_age_exceeds_lifetime_raises():
    project = _make_project()
    with pytest.raises(
        ValueError,
        match="lifetime of an existing asset needs to be higher",
    ):
        _create_invest_if_wanted(
            optimise_cap=False,
            existing_capacity=100,
            project_data=project,
            capex_var=1000,
            opex_fix=10,
            lifetime=10,
            age_installed=15,
        )


def test_create_invest_with_max_and_min_capacity():
    project = _make_project()
    result = _create_invest_if_wanted(
        optimise_cap=True,
        existing_capacity=0,
        project_data=project,
        capex_var=1000,
        opex_fix=10,
        lifetime=20,
        age_installed=0,
        maximum_capacity=500,
        minimum_capacity=100,
    )
    assert float(result.maximum[0]) == 500
    assert float(result.minimum[0]) == 100


def test_calculate_annuity_mvs_optimise_cap():
    result = calculate_annuity_mvs(
        optimise_cap=True,
        capex_var=1000,
        lifetime=20,
        age_installed=0,
        tax=0,
        lifetime_project=20,
        discount_factor=0.01,
    )
    assert result > 0


def test_calculate_annuity_mvs_no_optimise():
    result = calculate_annuity_mvs(
        optimise_cap=False,
        capex_var=1000,
        lifetime=20,
        age_installed=5,
        tax=0,
        lifetime_project=20,
        discount_factor=0.01,
    )
    assert result > 0


def test_calculate_annuity_mvs_age_exceeds_project_lifetime():
    result = calculate_annuity_mvs(
        optimise_cap=False,
        capex_var=1000,
        lifetime=20,
        age_installed=0,
        tax=0,
        lifetime_project=15,
        discount_factor=0.01,
    )
    assert result == 0
