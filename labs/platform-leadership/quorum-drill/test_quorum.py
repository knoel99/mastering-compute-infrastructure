"""Tests of quorum.py: majority sizes from the etcd FAQ, values used in chapter 9, Monte Carlo agreement."""
import math
import random

import pytest

import quorum as qm


@pytest.mark.parametrize("n,majority,tolerance", [
    (1, 1, 0), (2, 2, 0), (3, 2, 1), (4, 3, 1), (5, 3, 2), (6, 4, 2), (7, 4, 3),
])
def test_majority_and_failure_tolerance_match_etcd_faq(n, majority, tolerance):
    assert qm.quorum(n) == majority
    assert qm.tolerated(n) == tolerance == (n - 1) // 2


def test_even_member_adds_nothing():
    # A fourth member raises the quorum to 3: the cluster still tolerates one failure,
    # and there is one more member that can fail.
    for a in (0.9, 0.99, 0.999):
        assert qm.p_quorum(4, a) < qm.p_quorum(3, a)
        assert qm.p_quorum(6, a) < qm.p_quorum(5, a)


def test_values_of_example_9_1():
    assert qm.p_quorum(3, 0.99) == pytest.approx(0.999702, abs=1e-9)
    assert 1 - qm.p_quorum(5, 0.99) == pytest.approx(9.85e-6, rel=1e-3)
    assert 1 - qm.p_quorum(3, 0.999) == pytest.approx(3.00e-6, rel=1e-3)
    assert 1 - qm.p_quorum(5, 0.999) == pytest.approx(9.99e-9, rel=1e-3)


def test_closed_form_for_three_members():
    a = 0.97
    assert qm.p_quorum(3, a) == pytest.approx(3 * a**2 - 2 * a**3, abs=1e-15)


def test_one_domain_caps_availability():
    # All members in one rack: the cluster cannot be more available than the rack.
    a, r = 0.999, 0.9995
    assert qm.p_quorum_domains((5,), a, r) == pytest.approx(r * qm.p_quorum(5, a), abs=1e-15)
    assert qm.p_quorum_domains((5,), a, r) < r


def test_domains_with_perfect_racks_reduce_to_binomial():
    for layout in [(5,), (2, 2, 1), (1, 1, 1), (3, 2)]:
        assert qm.p_quorum_domains(layout, 0.9, 1.0) == pytest.approx(qm.p_quorum(sum(layout), 0.9), abs=1e-12)


def test_a_domain_holding_a_majority_is_no_better_than_one_rack():
    # 3+2 on two racks: losing the rack of three loses quorum, so two racks buy (almost) nothing.
    # 2+2+1 on three racks: no rack holds more than f = 2 members, any single rack may fail.
    a, r = 0.999, 0.9995
    one = qm.p_quorum_domains((5,), a, r)
    two = qm.p_quorum_domains((3, 2), a, r)
    three = qm.p_quorum_domains((2, 2, 1), a, r)
    assert two <= one
    assert (1 - one) / (1 - three) > 100
    assert 1 - three == pytest.approx(3.76e-6, rel=1e-3)
    assert 1 - qm.p_quorum_domains((1, 1, 1), a, r) == pytest.approx(6.74e-6, rel=1e-3)


def test_monte_carlo_agrees_with_formula():
    rng = random.Random(2026)
    trials = 50000
    for layout, a, r in qm.CHECK_CASES:
        exact = qm.p_quorum_domains(layout, a, r)
        est = qm.simulate(layout, a, r, trials, rng)
        assert abs(est - exact) <= 4 * math.sqrt(exact * (1 - exact) / trials)


def test_check_command_succeeds(capsys):
    assert qm.main(["check", "--trials", "20000", "--seed", "7"]) == 0
    assert "formula and simulation agree" in capsys.readouterr().out
