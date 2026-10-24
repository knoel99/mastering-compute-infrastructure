"""Behavioural tests of the admission model. IMPL=starter|reference chooses the code under test.

Numbers come from manifests/30-clusterqueues.yaml: research 32 GPUs (borrow up to 8, lend up to 16),
product 24 GPUs (no limit), shared-dev 8 GPUs (borrow up to 8); cohort capacity = 16 + 24 + 8 = 48 lendable GPUs.
"""
import random

import pytest

from model import GPU

R, P, D = "research", "product", "shared-dev"


def run(cluster, *workloads):
    """Submit the workloads one after the other, running a scheduling cycle after each (as the controller does)."""
    events = []
    for w in workloads:
        cluster.submit(w)
        events += cluster.schedule()
    return events


def states(cluster):
    return {w.name: w.state for w in cluster.workloads.values()}


# ---------------------------------------------------------------- manifests -> model
def test_queues_are_read_from_the_manifests(queues):
    r = queues[R]
    assert r.cohort == "gpu-pool" and r.nominal[GPU] == 32 and r.borrowing_limit[GPU] == 8 and r.lending_limit[GPU] == 16
    assert r.strategy == "StrictFIFO" and r.reclaim == "Any"
    p = queues[P]
    assert p.nominal[GPU] == 24 and GPU not in p.borrowing_limit and p.borrow_policy == "LowerPriority" and p.borrow_threshold == 100


# ---------------------------------------------------------------- nominal quota (the starter already passes these)
def test_workload_within_nominal_quota_is_admitted(cluster, wl, gpus):
    events = run(cluster, wl("a", P, 24))
    assert [(e.kind, e.detail) for e in events] == [("admit", "nominal")]
    assert gpus(cluster, P) == 24


def test_workload_is_admitted_as_a_whole_or_not_at_all(cluster, wl, gpus):
    run(cluster, wl("a", D, 8), wl("big", D, 16))   # 8 + 16 > 8 + 8 borrowing limit
    assert states(cluster) == {"a": "admitted", "big": "pending"}
    assert gpus(cluster, D) == 8


# ---------------------------------------------------------------- borrowing and lending
def test_borrowing_uses_idle_quota_of_the_cohort(cluster, wl, gpus):
    events = run(cluster, wl("a", P, 30))
    assert events[0].detail == "borrowing" and gpus(cluster, P) == 30


def test_borrowing_limit_caps_a_queue(cluster, wl, gpus):
    run(cluster, wl("a", D, 8), wl("b", D, 8), wl("c", D, 1))   # limit 8 + 8 = 16
    assert states(cluster) == {"a": "admitted", "b": "admitted", "c": "pending"}
    assert gpus(cluster, D) == 16


def test_lending_limit_keeps_quota_for_the_owner(cluster, wl, gpus):
    run(cluster, wl("a", P, 48), wl("b", P, 1))   # pool = 48 lendable GPUs; research keeps 16 for itself
    assert states(cluster) == {"a": "admitted", "b": "pending"}
    assert gpus(cluster, P) == 48


# ---------------------------------------------------------------- queueing strategies
def test_strict_fifo_head_blocks_the_following_workloads(cluster, wl):
    run(cluster, wl("hold", R, 32), wl("big", R, 16), wl("small", R, 4))
    assert states(cluster) == {"hold": "admitted", "big": "pending", "small": "pending"}   # small would fit, but big is older


def test_best_effort_fifo_lets_smaller_workloads_pass(cluster, wl):
    run(cluster, wl("hold", P, 24), wl("big", P, 40), wl("small", P, 4))
    assert states(cluster) == {"hold": "admitted", "big": "pending", "small": "admitted"}


def test_priority_orders_the_queue_before_creation_time(cluster, wl):
    run(cluster, wl("hold", R, 40, "urgent"), wl("old", R, 8, "normal"), wl("new", R, 8, "high"))
    cluster.finish("hold")
    events = cluster.schedule()
    assert [e.workload for e in events if e.kind == "admit"][0] == "new"


# ---------------------------------------------------------------- preemption
def test_urgent_workload_preempts_lower_priority_in_its_own_queue(cluster, wl):
    run(cluster, wl("scratch", R, 32, "preemptible"))
    events = run(cluster, wl("deadline", R, 16, "urgent"))
    assert [(e.kind, e.workload) for e in events] == [("preempt", "scratch"), ("admit", "deadline")]
    assert events[0].detail.startswith("InClusterQueue")
    assert states(cluster) == {"scratch": "pending", "deadline": "admitted"}


def test_preempted_workload_is_readmitted_when_quota_returns(cluster, wl):
    run(cluster, wl("scratch", R, 32, "preemptible"), wl("deadline", R, 16, "urgent"))
    cluster.finish("deadline")
    cluster.schedule()
    assert states(cluster) == {"scratch": "admitted"}


def test_same_priority_is_never_preempted_inside_a_queue(cluster, wl):
    run(cluster, wl("a", P, 24), wl("b", P, 40))
    assert states(cluster) == {"a": "admitted", "b": "pending"}


def test_reclaim_within_cohort_any_takes_back_lent_quota(cluster, wl, gpus):
    run(cluster, wl("a", P, 24, "normal"), wl("b", P, 16, "high"))   # product borrows 16 of the idle quota
    assert gpus(cluster, P) == 40
    events = run(cluster, wl("mine", R, 32))
    kinds = [(e.kind, e.workload) for e in events]
    assert kinds == [("preempt", "a"), ("admit", "mine")]            # lowest priority first, and only as much as needed
    assert events[0].detail.startswith("InCohort")
    assert gpus(cluster, P) == 16 and gpus(cluster, R) == 32


def test_reclaim_lower_priority_spares_equal_or_higher_priority(cluster, wl):
    run(cluster, wl("r", R, 40, "normal"), wl("d", D, 8))             # research borrows 8, dev uses its own 8
    run(cluster, wl("p", P, 24))                                       # 24 + 24 + 8 > 48: needs to reclaim
    assert states(cluster) == {"r": "admitted", "d": "admitted", "p": "pending"}


def test_reclaim_lower_priority_preempts_a_lower_priority_borrower(cluster, wl):
    run(cluster, wl("r", R, 40, "preemptible"), wl("d", D, 8))
    events = run(cluster, wl("p", P, 24))
    assert [(e.kind, e.workload) for e in events] == [("preempt", "r"), ("admit", "p")]
    assert states(cluster) == {"r": "pending", "d": "admitted", "p": "admitted"}


def test_borrow_within_cohort_preempts_below_the_threshold(cluster, wl):
    run(cluster, wl("ra", R, 32, "normal"), wl("rb", R, 8, "preemptible"))   # research borrows 8
    events = run(cluster, wl("big", P, 30, "high"))                          # product needs 6 more than its nominal quota
    assert [(e.kind, e.workload) for e in events] == [("preempt", "rb"), ("admit", "big")]
    assert states(cluster)["ra"] == "admitted"


def test_borrow_within_cohort_threshold_protects_higher_priority(cluster, wl):
    run(cluster, wl("ra", R, 32, "high"), wl("rb", R, 8, "high"))           # 500 > threshold 100
    run(cluster, wl("big", P, 30, "urgent"))
    assert states(cluster)["rb"] == "admitted" and states(cluster)["big"] == "pending"


def test_schedule_is_idempotent(cluster, wl):
    run(cluster, wl("a", P, 30), wl("b", R, 40), wl("c", D, 16), wl("d", R, 8, "urgent"))
    assert cluster.schedule() == []


# ---------------------------------------------------------------- invariants under random traffic
def test_invariants_hold_under_random_traffic(queues, wl):
    from admission import Cluster
    rng = random.Random(7)
    c = Cluster(queues)
    pool_capacity = sum(q.nominal[GPU] - (q.nominal[GPU] - q.lending_limit.get(GPU, q.nominal[GPU])) for q in queues.values())
    n = 0
    for _ in range(400):
        if rng.random() < 0.65 or not c.workloads:
            n += 1
            c.submit(wl(f"w{n}", rng.choice([R, P, D]), rng.choice([1, 2, 4, 8, 16, 24, 32]),
                        rng.choice(["urgent", "high", "normal", "normal", "preemptible"])))
        else:
            c.finish(rng.choice(sorted(c.workloads)))
        c.schedule()
        used = {q: c.usage(q)[GPU] for q in queues}
        for name, q in queues.items():
            assert used[name] <= q.nominal[GPU] + q.borrowing_limit.get(GPU, float("inf")) + 1e-9, (name, used)
        assert sum(max(0.0, used[q.name] - (q.nominal[GPU] - q.lending_limit.get(GPU, q.nominal[GPU]))) for q in queues.values()) \
            <= pool_capacity + 1e-9, used
        assert c.schedule() == []
        assert all(w.state in ("pending", "admitted") for w in c.workloads.values())
