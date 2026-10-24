import gang_deadlock as gd
import topology_fit as tf


def test_exact_probability_matches_the_simulation():
    for nodes in (10, 12, 14):
        assert abs(gd.exact_two_jobs(nodes, 8) - gd.simulate(nodes, 8, 2, 20000, seed=1)) < 0.02


def test_deadlock_probability_decreases_with_capacity_and_vanishes_when_both_jobs_fit():
    ps = [gd.exact_two_jobs(n, 8) for n in range(8, 17)]
    assert all(a >= b for a, b in zip(ps, ps[1:])) and ps[-1] == 0.0 and ps[0] > 0.999


def test_gang_never_deadlocks():
    assert gd.simulate(12, 8, 2, 2000, seed=3, gang=True) == 0.0


FREE = {"block-0": {"rack-0": 5, "rack-1": 3}, "block-1": {"rack-2": 6, "rack-3": 2}}


def test_required_rack_waits_when_no_rack_is_big_enough():
    assert tf.place(FREE, 6, "rack") == ("rack", 6)
    assert tf.place(FREE, 8, "rack") is None


def test_preferred_goes_up_level_by_level():
    assert tf.place(FREE, 8, "rack", "preferred") == ("block", 8)
    assert tf.place(FREE, 12, "rack", "preferred") == ("cluster", 16)
    assert tf.place(FREE, 17, "rack", "preferred") is None
