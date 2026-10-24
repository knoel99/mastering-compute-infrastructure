import copy
import math
import subprocess
import sys

import pytest

import tco
from conftest import ASSUMPTIONS, HERE, IMPL


@pytest.fixture()
def a():
    return tco.load(ASSUMPTIONS)


def test_annuity_repays_the_loan():
    rate, years = 0.08, 4
    pay = tco.annuity_factor(rate, years)
    balance = 1.0
    for _ in range(years):
        balance = balance * (1 + rate) - pay
    assert abs(balance) < 1e-12


def test_annuity_without_interest_is_straight_line():
    assert tco.annuity_factor(0.0, 5) == pytest.approx(0.2)


def test_annualized_capex_without_interest_or_residual():
    assert tco.annualized_capex(1000.0, 4, 0.0, 0.0) == pytest.approx(250.0)


def test_residual_value_lowers_the_yearly_cost():
    base = tco.annualized_capex(1000.0, 4, 0.0, 0.08)
    with_resale = tco.annualized_capex(1000.0, 4, 0.2, 0.08)
    assert with_resale < base


def test_components_have_the_documented_keys(a):
    comp = tco.owned_components(a, 0.6)
    assert set(comp) == {"amortization", "support", "staff", "facility", "energy"}
    assert all(v > 0 for v in comp.values())


def test_only_energy_depends_on_utilization(a):
    low, high = tco.owned_components(a, 0.2), tco.owned_components(a, 0.9)
    assert high["energy"] > low["energy"]
    for k in ("amortization", "support", "staff", "facility"):
        assert high[k] == pytest.approx(low[k])


def test_facility_choice_changes_only_the_facility_line(a):
    b = copy.deepcopy(a)
    b["owned"]["facility"] = "onprem"
    ca, cb = tco.owned_components(a, 0.5), tco.owned_components(b, 0.5)
    assert ca["facility"] != cb["facility"]
    assert ca["amortization"] == pytest.approx(cb["amortization"])


def test_committed_cost_scales_with_inverse_utilization(a):
    full = tco.cost_per_useful_hour(a, "lease_3y", 1.0, 1.0)
    half = tco.cost_per_useful_hour(a, "lease_3y", 0.5, 1.0)
    assert full == pytest.approx(a["committed"]["lease_3y"]["u_per_gpu_hour"])
    assert half == pytest.approx(2 * full)


def test_on_demand_does_not_depend_on_utilization_but_on_goodput(a):
    c1 = tco.cost_per_useful_hour(a, "on_demand", 0.2, 0.8)
    c2 = tco.cost_per_useful_hour(a, "on_demand", 0.9, 0.8)
    assert c1 == pytest.approx(c2) == pytest.approx(a["on_demand"]["u_per_gpu_hour"] / 0.8)


def test_waste_fraction_matches_young_daly():
    # C = 3 min, M = 20 h, R = 10 min -> sqrt(2*0.05/20) + (1/6)/20
    expected = math.sqrt(2 * 0.05 / 20) + (10 / 60) / 20
    assert tco.waste_fraction(20, 3, 10) == pytest.approx(expected)


def test_waste_decreases_when_interruptions_are_rarer():
    assert tco.waste_fraction(200, 3, 10) < tco.waste_fraction(20, 3, 10) < tco.waste_fraction(2, 3, 10)


def test_spot_without_interruptions_is_its_rate_over_goodput(a):
    b = copy.deepcopy(a)
    b["spot"]["mtbi_hours"] = 1e9
    assert tco.cost_per_useful_hour(b, "spot", 0.5, 0.9) == pytest.approx(b["spot"]["u_per_gpu_hour"] / 0.9, rel=1e-3)


def test_breakeven_equalises_the_two_costs(a):
    u = tco.breakeven_utilization(a, "owned", "on_demand", goodput=0.9)
    assert u is not None and 0.05 < u < 1.0
    assert tco.cost_per_useful_hour(a, "owned", u, 0.9) == pytest.approx(
        tco.cost_per_useful_hour(a, "on_demand", u, 0.9), rel=1e-4)


def test_breakeven_is_independent_of_goodput_for_on_demand(a):
    u1 = tco.breakeven_utilization(a, "owned", "on_demand", goodput=1.0)
    u2 = tco.breakeven_utilization(a, "owned", "on_demand", goodput=0.5)
    assert u1 == pytest.approx(u2, rel=1e-4)


def test_breakeven_none_when_the_fixed_option_never_wins(a):
    b = copy.deepcopy(a)
    b["owned"]["node_price_u"] *= 10
    assert tco.breakeven_utilization(b, "owned", "on_demand") is None


def test_owned_wins_at_high_utilization_and_loses_at_low(a):
    assert tco.cost_per_useful_hour(a, "owned", 0.95, 0.9) < tco.cost_per_useful_hour(a, "on_demand", 0.95, 0.9)
    assert tco.cost_per_useful_hour(a, "owned", 0.2, 0.9) > tco.cost_per_useful_hour(a, "on_demand", 0.2, 0.9)


def test_sensitivity_is_sorted_and_signed_correctly(a):
    rows = tco.sensitivity(a, 0.7, 0.9)
    swings = [r["swing"] for r in rows]
    assert swings == sorted(swings, reverse=True)
    by = {r["param"]: r for r in rows}
    assert by["owned.node_price_u"]["high"] > by["owned.node_price_u"]["low"]      # dearer node, dearer GPU-hour
    assert by["owned.life_years"]["high"] < by["owned.life_years"]["low"]          # longer life, cheaper GPU-hour
    assert rows[0]["param"] == "owned.node_price_u"                                 # capex dominates in this example


def test_the_input_file_is_labelled_fictional():
    head = ASSUMPTIONS.read_text(encoding="utf-8")[:300]
    assert "FICTIONAL" in head


def test_cli_prints_a_table_and_breakeven():
    out = subprocess.run([sys.executable, str(HERE / IMPL / "tco.py"), str(ASSUMPTIONS), "--breakeven"],
                         capture_output=True, text=True, check=True).stdout
    assert "FICTIONAL" in out and "breakeven owned vs on_demand" in out
