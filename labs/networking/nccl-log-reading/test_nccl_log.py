"""Tests for the NCCL log parser, on SYNTHETIC fixtures (and one public excerpt)."""
from pathlib import Path

import pytest

import make_fixtures
import nccl_log

FIX = Path(__file__).parent / "fixtures"


def run(name: str) -> dict:
    return nccl_log.analyse(nccl_log.parse((FIX / name).read_text(encoding="utf-8")))


def test_fixtures_are_reproducible():
    """The committed fixtures are exactly what make_fixtures.py generates (deterministic)."""
    body = (FIX / "healthy_2node_ib.log").read_text(encoding="utf-8").split("\n", 1)[1]
    assert body == make_fixtures.gen(2)


def test_healthy_log():
    res = run("healthy_2node_ib.log")
    s = res["summary"]
    assert res["errors"] == []
    assert (s["nranks"], s["nodes"], s["ranks_logged"], s["init_complete"]) == (16, 2, 16, 16)
    assert s["network"] == ["IB"]
    assert s["hcas_per_host"] == {"node-01": 8, "node-02": 8}
    assert s["coll_channels"] == [4]
    # 4 channels x (16 ranks - 2 inter-node hops) intra-node links; 4 x 2 inter-node links, seen at both ends
    assert s["transports"]["P2P/CUMEM"] == 4 * 14
    assert s["transports"]["NET/IB/GDRDMA"] == 4 * 2 * 2


def test_socket_fallback_is_flagged():
    assert run("socket_fallback.log")["errors"] == ["socket_network"]


def test_degraded_rail():
    res = run("degraded_rail.log")
    assert res["errors"] == ["hca_mismatch"]
    codes = {f["code"] for f in res["findings"]}
    assert "gdr_disabled" in codes
    # the channel lines agree with the HCA lines: the card without GPU Direct RDMA is used without the /GDRDMA suffix
    assert res["summary"]["transports"].get("NET/IB", 0) >= 1


def test_hang_in_init_names_the_rank():
    res = run("hang_in_init.log")
    assert res["errors"] == ["init_incomplete"]
    detail = next(f["detail"] for f in res["findings"] if f["code"] == "init_incomplete")
    assert "[11]" in detail
    assert res["summary"]["init_complete"] == 15


def test_warning_is_not_an_error():
    res = run("healthy_with_warning.log")
    assert res["errors"] == []
    assert any(f["code"] == "warnings" for f in res["findings"])


def test_public_excerpt():
    res = run("public_nccl_docs.log")
    assert res["summary"]["network"] == ["IB"]
    assert res["summary"]["version"] == "2.30.3+cuda13.0"
    msg = next(f["detail"] for f in res["findings"] if f["code"] == "warnings")
    assert msg.startswith("2 WARN/ATTN lines")


def test_broken_ring_is_detected():
    text = (FIX / "healthy_2node_ib.log").read_text(encoding="utf-8")
    good = "Ring 00 : 4 -> 5 -> 6"
    assert good in text
    res = nccl_log.analyse(nccl_log.parse(text.replace(good, "Ring 00 : 4 -> 5 -> 9")))
    assert res["errors"] == ["ring_broken"]


def test_ring_cycle_helper():
    assert nccl_log.ring_is_single_cycle({0: (3, 1), 1: (0, 2), 2: (1, 3), 3: (2, 0)}, 4)
    two_cycles = {0: (1, 1), 1: (0, 0), 2: (3, 3), 3: (2, 2)}
    assert not nccl_log.ring_is_single_cycle(two_cycles, 4)
    assert not nccl_log.ring_is_single_cycle({0: (1, 1), 1: (0, 0)}, 4)


def test_unknown_lines_are_ignored_and_timestamps_parsed():
    text = "garbage line\n[2026-05-05 06:16:47] n1:1:1 [0] plugin/net.cc:334 NCCL WARN boom\nn1:1:1 [0] NCCL INFO something new\n"
    rep = nccl_log.parse(text)
    assert rep["warnings"] == ["n1: boom"]


def test_cli_expect(tmp_path):
    assert nccl_log.main.__name__ == "main"
    p = tmp_path / "x.log"
    p.write_text((FIX / "socket_fallback.log").read_text(encoding="utf-8"), encoding="utf-8")
    import subprocess
    import sys
    ok = subprocess.run([sys.executable, str(Path(nccl_log.__file__)), str(p), "--expect", "socket_network"], capture_output=True, text=True)
    bad = subprocess.run([sys.executable, str(Path(nccl_log.__file__)), str(p)], capture_output=True, text=True)
    assert ok.returncode == 0 and bad.returncode == 1
