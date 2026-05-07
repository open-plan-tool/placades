import pytest

from oemof.eesyplan.importer import electricity_demand as el

PROFILE_TYPES_EL_BDEW_ABBR = el.PROFILE_TYPES_EL_BDEW_ABBR
PROFILE_TYPES_EL_BDEW = el.PROFILE_TYPES_EL_BDEW


@pytest.mark.parametrize("profile_type", PROFILE_TYPES_EL_BDEW_ABBR)
def test_el_demand_profile_by_bdew(profile_type):
    el_demand = el.create_el_demand(
        profile_type=profile_type,
        annual_electricity_demand=3000,
        resolution="1h",
        consider_holidays=False,
    )
    assert pytest.approx(el_demand.sum(), rel=0.01) == 3000


@pytest.mark.parametrize("profile_type", PROFILE_TYPES_EL_BDEW)
def test_el_demand_profile_by_bdew2(profile_type):
    el_demand = el.create_el_demand(
        profile_type=profile_type,
        annual_electricity_demand=3000,
        resolution="1h",
        consider_holidays=True,
    )
    assert pytest.approx(el_demand.sum(), rel=0.01) == 3000


def test_el_demand_profile_by_bdew3():
    el_demand = el.create_el_demand(
        profile_type="G1",
        annual_electricity_demand=3000,
        resolution="15min",
        consider_holidays=True,
    )
    assert pytest.approx(el_demand.sum(), rel=0.01) == 3000


def test_invalid_profile_type():
    with pytest.raises(ValueError, match="Invalid profile type"):
        el.create_el_demand(
            profile_type="swimming",
            annual_electricity_demand=3000,
            resolution="1h",
            consider_holidays=True,
        )


def test_invalid_resolution():
    with pytest.raises(ValueError, match="Invalid resolution"):
        el.create_el_demand(
            profile_type="G1",
            annual_electricity_demand=3000,
            resolution="2h",
            consider_holidays=True,
        )
