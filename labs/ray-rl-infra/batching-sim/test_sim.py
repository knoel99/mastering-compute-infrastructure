"""Structural tests of the toy engine (simulated time only: no wall-clock assertion).

Run with pytest (`python3 -m pytest -q test_sim.py`) or without it (`python3 test_sim.py`).
"""
import contextlib
import io

import sim

ENG = sim.Engine()
OFFLINE = sim.workload(n=64, seed=1)


def run(reqs=OFFLINE, eng=ENG, policy="continuous", kv="paged"):
    return sim.simulate(reqs, eng, policy, kv)


def test_deterministic():
    assert run() == run()
    assert sim.workload(n=64, seed=1) == OFFLINE
    assert sim.workload(n=64, seed=2) != OFFLINE


def test_every_engine_completes_every_request_with_the_same_tokens():
    total = sum(r.output for r in OFFLINE)
    for p, k in sim.ENGINES:
        r = run(policy=p, kv=k)
        assert r["requests"] == len(OFFLINE)
        assert r["useful_tokens"] == total


def test_continuous_batching_needs_fewer_steps_than_static():
    static = run(policy="static", kv="reserve")
    cont = run(policy="continuous", kv="reserve")      # same KV accounting: only the batching differs
    assert cont["steps"] < static["steps"]
    assert cont["makespan_s"] < static["makespan_s"]
    assert cont["mean_running"] > static["mean_running"]


def test_static_steps_equal_the_sum_of_batch_maxima():
    big = sim.Engine(kv_budget_tokens=65536)           # 32 x (512 + 1024) fits: only max_seqs limits a batch
    r = run(eng=big, policy="static", kv="reserve")
    outs = [q.output for q in OFFLINE]
    expect = sum(max(outs[i:i + big.max_seqs]) for i in range(0, len(outs), big.max_seqs))
    assert r["steps"] == expect


def test_continuous_steps_are_bounded_below_by_work_and_longest_request():
    big = sim.Engine(kv_budget_tokens=65536)
    r = run(eng=big, policy="continuous", kv="reserve")
    outs = [q.output for q in OFFLINE]
    assert r["steps"] >= max(outs)
    assert r["steps"] >= -(-sum(outs) // big.max_seqs)


def test_paged_kv_admits_more_sequences_than_reservation():
    res = run(policy="continuous", kv="reserve")
    pag = run(policy="continuous", kv="paged")
    assert pag["max_running"] > res["max_running"]
    assert pag["steps"] <= res["steps"]


def test_kv_budget_is_never_exceeded_even_with_preemption():
    tight = sim.Engine(kv_budget_tokens=2048)          # one request of 512 + 1024 still fits
    for p, k in sim.ENGINES:
        r = run(eng=tight, policy=p, kv=k)
        assert r["max_kv_tokens"] <= tight.kv_budget_tokens
    for p, k in sim.ENGINES:
        assert run(policy=p, kv=k)["max_kv_tokens"] <= ENG.kv_budget_tokens


def test_preempted_sequences_are_recomputed_and_finish():
    tight = sim.Engine(kv_budget_tokens=2048)
    r = run(eng=tight, policy="continuous", kv="paged")
    assert r["preemptions"] > 0
    assert r["useful_tokens"] == sum(q.output for q in OFFLINE)


def test_continuous_batching_cuts_tail_ttft_online():
    reqs = sim.workload(n=200, seed=3, rate=8)
    static = run(reqs, policy="static", kv="reserve")
    cont = run(reqs, policy="continuous", kv="paged")
    assert cont["ttft_p95_ms"] < static["ttft_p95_ms"]


def test_goodput_ordering():
    with contextlib.redirect_stdout(io.StringIO()):
        best = sim.sweep(n=200)
    g = [best.get(e, 0) for e in sim.ENGINES]
    assert g[0] <= g[1] <= g[2] and g[2] > g[0]


def test_invalid_inputs_are_rejected():
    for kwargs in ({"policy": "fifo"}, {"kv": "contiguous"}):
        try:
            run(**kwargs)
        except ValueError:
            continue
        raise AssertionError(f"accepted {kwargs}")
    try:
        run(eng=sim.Engine(kv_budget_tokens=1000))
    except ValueError:
        pass
    else:
        raise AssertionError("accepted a KV budget smaller than one request")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print(f"passed {name}")
    print(f"{len(tests)} tests passed")
