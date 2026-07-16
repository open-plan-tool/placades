import pytest

from oemof.eesyplan.project import Project


def test_project_init():
    p = Project(
        name="test",
        lifetime=20,
        tax=0.19,
        discount_factor=0.05,
        shortage_cost=999,
        excess_cost=99,
    )
    assert p.name == "test"
    assert p.lifetime == 20
    assert p.tax == 0.19
    assert p.discount_factor == 0.05
    assert p.shortage_cost == 999
    assert p.excess_cost == 99


def test_project_defaults():
    p = Project(name="p", lifetime=10, tax=0, discount_factor=0.01)
    assert p.shortage_cost == 999
    assert p.excess_cost == 99


def test_calculate_epc_mvs():
    p = Project(name="p", lifetime=20, tax=0, discount_factor=0.01)
    result = p.calculate_epc(True, 234, 20, 0)
    assert result is not None
    assert round(result, 3) == 12.967


def test_calculate_epc_oemof():
    p = Project(name="p", lifetime=20, tax=0, discount_factor=0.01)
    result = p.calculate_epc(True, 234, 20, 0, "oemof")
    assert result is not None
    assert round(result, 3) == 12.967


def test_calculate_epc_wrong_method():
    p = Project(name="p", lifetime=20, tax=0, discount_factor=0.01)
    result = p.calculate_epc(True, 234, 20, 0, "wrong")
    assert result is None


def test_calculate_epc_mvs_none_param():
    p = Project(name="p", lifetime=20, tax=0, discount_factor=0.01)
    with pytest.raises(ValueError, match="None is not allowed"):
        p.calculate_epc(None, 234, 20, 0)


def test_calculate_epc_oemof_none_param():
    p = Project(name="p", lifetime=20, tax=0, discount_factor=0.01)
    with pytest.raises(ValueError, match="None is not allowed"):
        p.calculate_epc(True, 234, None, 0, "oemof")
