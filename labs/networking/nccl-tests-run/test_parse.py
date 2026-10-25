"""Tests of the nccl-tests table parser on SYNTHETIC tables (ring alpha-beta model + seeded noise)."""
from pathlib import Path

import pytest

import make_sample
import parse_nccl_tests as P

FIX = Path(__file__).parent / "fixtures"


def load(name: str, **kw):
    res = P.parse((FIX / name).read_text(encoding="utf-8"))
    return res, P.analyse(res, kw.get("ranks"), kw.get("expect"), kw.get("tol", 0.8))


def test_fixtures_are_reproducible():
    assert (FIX / "all_reduce_synthetic_ok.txt").read_text(encoding="utf-8") == make_sample.table(16, 12.0, 48.0, 1)


def test_parse_structure():
    res, _ = load("all_reduce_synthetic_ok.txt")
    assert res["ranks_listed"] == 16
    assert len(res["rows"]) == 32  # 8 B ... 16 GiB, doubling
    assert res["rows"][0]["size"] == 8 and res["rows"][-1]["size"] == 1 << 34
    assert res["avg_busbw"] is not None


def test_busbw_is_algbw_times_factor():
    res, _ = load("all_reduce_synthetic_ok.txt")
    f = 2 * 15 / 16
    for r in res["rows"][20:]:  # sizes >= 8 MiB: the printed 2 decimals no longer dominate
        assert r["oop"]["busbw"] == pytest.approx(r["oop"]["algbw"] * f, rel=0.02)


def test_healthy_table_passes():
    _, a = load("all_reduce_synthetic_ok.txt", expect=48.0)
    assert a["problems"] == []
    assert 0.95 <= a["summary"]["plateau_over_expected"] <= 1.05
    assert a["summary"]["fit"]["B_gbs"] == pytest.approx(48.0, rel=0.05)
    assert a["summary"]["fit"]["alpha_us"] == pytest.approx(12.0, rel=0.3)


def test_degraded_table_is_flagged():
    _, a = load("all_reduce_synthetic_degraded.txt", expect=48.0)
    assert len(a["problems"]) == 1 and "of the expected" in a["problems"][0]
    assert a["summary"]["plateau_over_expected"] == pytest.approx(26 / 48, rel=0.05)


def test_wrong_results_are_flagged():
    _, a = load("all_reduce_synthetic_wrong.txt", expect=48.0)
    assert any("corruption" in p for p in a["problems"])


def test_no_expectation_no_bandwidth_verdict():
    _, a = load("all_reduce_synthetic_degraded.txt")
    assert a["problems"] == []


def test_garbage_input():
    a = P.analyse(P.parse("nothing useful here\n"), None, None, 0.8)
    assert a["problems"] == ["no data rows found"]


def test_na_wrong_column():
    line = "    1048576       262144    float    sum     -1    90.0  11.65  21.84    N/A    90.0  11.65  21.84    N/A"
    res = P.parse(line)
    assert res["rows"][0]["oop"]["wrong"] is None
