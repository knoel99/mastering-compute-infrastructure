import subprocess
import sys
from datetime import datetime

import pytest

import showback as sb
from conftest import FIXTURES, HERE

SAMPLE = """# comment line
JobID|Account|User|Partition|State|Submit|Start|End|ElapsedRaw|AllocTRES|NNodes
1|a|u1|p|COMPLETED|2026-09-01T10:00:00|2026-09-01T10:00:00|2026-09-01T12:00:00|7200|billing=8,cpu=64,gres/gpu=8,mem=512G,node=1|1
2|a|u1|p|FAILED|2026-09-01T10:00:00|2026-09-01T11:00:00|2026-09-01T11:30:00|1800|billing=4,cpu=32,gres/gpu=4,mem=256G,node=1|1
3|b|u2|p|CANCELLED by 1000|2026-09-01T09:00:00|2026-09-01T10:30:00|2026-09-01T10:45:00|900|billing=2,cpu=16,gres/gpu=2,node=1|1
4|b|u2|p|PENDING|2026-09-01T11:59:00|Unknown|Unknown|0||0
"""
WIN = (datetime(2026, 9, 1, 10, 0, 0), datetime(2026, 9, 1, 14, 0, 0))


@pytest.fixture()
def rows():
    return sb.parse_rows(SAMPLE.splitlines())


def test_parse_tres_skips_memory_and_empty():
    assert sb.parse_tres("billing=8,cpu=64,gres/gpu=8,mem=512G,node=1") == {"billing": 8.0, "cpu": 64.0, "gres/gpu": 8.0, "node": 1.0}
    assert sb.parse_tres("") == {}


def test_parse_rows_ignores_comments_and_reads_unknown_times(rows):
    assert len(rows) == 4 and rows[3]["_start"] is None and rows[0]["_elapsed"] == 7200.0


def test_alloc_hours_plain_and_clipped(rows):
    assert sb.alloc_hours(rows[0], "gres/gpu") == pytest.approx(16.0)             # 8 GPUs * 2 h
    w = (datetime(2026, 9, 1, 11, 0, 0), datetime(2026, 9, 1, 13, 0, 0))
    assert sb.alloc_hours(rows[0], "gres/gpu", w) == pytest.approx(8.0)           # only the hour 11:00-12:00 ... 1 h * 8 GPUs
    assert sb.alloc_hours(rows[3], "gres/gpu", w) == 0.0                          # never started


def test_usage_by_account(rows):
    u = sb.usage_by_account(rows, "gres/gpu")
    assert u["a"] == {"jobs": 2, "alloc_h": pytest.approx(18.0)} and u["b"]["jobs"] == 2
    assert u["b"]["alloc_h"] == pytest.approx(0.5)


def test_lost_candidates_only_counts_abnormal_endings(rows):
    lost = sb.lost_candidates(rows, "gres/gpu")
    assert lost["FAILED"] == pytest.approx(2.0) and lost["TIMEOUT"] == 0.0
    assert sum(lost.values()) == pytest.approx(2.0)                               # COMPLETED and CANCELLED are not counted


def test_utilization_exact(rows):
    # window 4 h * 16 GPUs = 64 GPU-h ; allocated inside the window: 16 + 2 + 0.5 = 18.5
    assert sb.utilization(rows, "gres/gpu", 16, WIN) == pytest.approx(18.5 / 64.0)


def test_percentile_convention():
    xs = [1, 2, 3, 4]
    assert sb.percentile(xs, 0) == 1 and sb.percentile(xs, 100) == 4
    assert sb.percentile(xs, 50) == pytest.approx(2.5) and sb.percentile(xs, 90) == pytest.approx(3.7)
    with pytest.raises(ValueError):
        sb.percentile([], 50)


def test_wait_stats(rows):
    w = sb.wait_stats(rows)
    assert w["n"] == 3                                                            # the pending job has no start
    assert sb.wait_stats(rows, "a")["p50_h"] == pytest.approx(0.5)                # waits 0 h and 1 h
    assert sb.wait_stats(rows, "zzz")["n"] == 0


@pytest.mark.parametrize("method", ["proportional", "equal", "platform"])
def test_idle_allocation_conserves_the_total(method):
    s = sb.allocate_idle({"a": 30.0, "b": 10.0}, 40.0, method)
    assert sum(s.values()) == pytest.approx(40.0)


def test_idle_allocation_shapes():
    p = sb.allocate_idle({"a": 30.0, "b": 10.0}, 40.0, "proportional")
    assert p["a"] == pytest.approx(30.0) and p["b"] == pytest.approx(10.0) and p["platform"] == 0.0
    e = sb.allocate_idle({"a": 30.0, "b": 10.0}, 40.0, "equal")
    assert e["a"] == e["b"] == pytest.approx(20.0)
    assert sb.allocate_idle({"a": 30.0}, 40.0, "platform")["platform"] == pytest.approx(40.0)


def test_cost_report_allocates_the_full_cost_exactly(rows):
    rep = sb.cost_report(rows, "gres/gpu", 16, 2.0, WIN, "proportional")
    total = sum(v["total"] for v in rep["accounts"].values()) + rep["platform"]
    assert total == pytest.approx(16 * 4 * 2.0) == pytest.approx(rep["full_cost"])
    assert rep["idle_cost"] == pytest.approx((64 - 18.5) * 2.0)


def synthetic():
    with open(FIXTURES / "synthetic_sacct.txt", encoding="utf-8") as fh:
        return sb.parse_rows(fh)


def test_synthetic_trace_is_reproducible():
    out = subprocess.run([sys.executable, str(HERE / "gen_trace.py")], capture_output=True, text=True, check=True).stdout
    assert out == (FIXTURES / "synthetic_sacct.txt").read_text(encoding="utf-8")


def test_synthetic_trace_never_exceeds_the_fleet():
    events = []
    for r in synthetic():
        g = r["_tres"]["gres/gpu"]
        events += [(r["_start"], g), (r["_end"], -g)]
    events.sort(key=lambda e: (e[0], e[1]))                                       # releases before starts at equal time
    used, peak = 0.0, 0.0
    for _, delta in events:
        used += delta
        peak = max(peak, used)
    assert peak <= 64.0


def test_synthetic_full_cost_conservation_for_every_method():
    rows = synthetic()
    win = (datetime(2026, 9, 1), datetime(2026, 9, 29))
    for m in ("proportional", "equal", "platform"):
        rep = sb.cost_report(rows, "gres/gpu", 64, 2.08, win, m)
        total = sum(v["total"] for v in rep["accounts"].values()) + rep["platform"]
        assert total == pytest.approx(rep["full_cost"], rel=1e-9)


def test_synthetic_headline_numbers_are_in_a_plausible_range():
    rep = sb.cost_report(synthetic(), "gres/gpu", 64, 2.08, (datetime(2026, 9, 1), datetime(2026, 9, 29)))
    assert 0.4 < rep["utilization"] < 0.7
    assert 0.0 < sum(rep["lost"].values()) / sum(v["alloc_h"] for v in rep["accounts"].values()) < 0.3
    assert rep["wait"]["p90_h"] > rep["wait"]["p50_h"]


def test_real_sandbox_fixture_matches_slurm_own_cputime():
    path = FIXTURES / "real_sandbox_sacct.txt"
    rows = sb.parse_rows(path.read_text(encoding="utf-8").splitlines())
    assert rows and all("CPUTimeRAW" in r for r in rows)
    ours = sb.usage_by_account(rows, "cpu")
    for acct, v in ours.items():
        theirs = sum(float(r["CPUTimeRAW"]) for r in rows if r["Account"] == acct)
        assert v["alloc_h"] * 3600.0 == pytest.approx(theirs)


def test_cli_prints_the_report():
    out = subprocess.run([sys.executable, str(HERE / "reference" / "showback.py"), str(FIXTURES / "synthetic_sacct.txt"), "--capacity", "64",
                          "--rate", "2.08", "--start", "2026-09-01T00:00:00", "--end", "2026-09-29T00:00:00"],
                         capture_output=True, text=True, check=True).stdout
    assert "utilization (allocated / capacity)" in out and "nlp" in out
