import calendar
import os
import subprocess
import time
from pathlib import Path

import pytest

import exporter

FIX = Path(__file__).resolve().parent.parent / "fixtures"
PROMTOOL = os.environ.get("PROMTOOL", "promtool")
T0 = calendar.timegm(time.strptime("2026-10-24T18:20:15", "%Y-%m-%dT%H:%M:%S"))


def fx(name):
    return (FIX / name).read_text()


def metric(m, name, **labels):
    for lab, v in m[name]:
        if all(lab.get(k) == x for k, x in labels.items()):
            return v
    return None


def test_state_and_reason_normalisation():
    assert exporter.norm_state("mix~") == "mix" and exporter.norm_state("DOWN*") == "down"
    assert exporter.bounded_reason("gpu_xid:79") == "gpu_xid"
    assert exporter.bounded_reason("health: gpu_xid:79") == "health"
    assert exporter.bounded_reason("none") == "none" and exporter.bounded_reason("") == "none"
    assert exporter.bounded_reason("Not responding (node 17)") == "not"
    assert len(exporter.bounded_reason("x" * 200)) <= 24


def test_parsers_read_the_real_captured_outputs(monkeypatch):
    jobs = exporter.parse_squeue(fx("squeue_mixed.txt"))
    assert [j["state"] for j in jobs].count("PENDING") == 4 and jobs[-1]["state"] == "RUNNING"
    assert jobs[0]["submit"] == T0 and jobs[0]["account"] == "teamb"
    nodes = exporter.parse_sinfo(fx("sinfo_draining.txt"))
    assert nodes == [{"partition": "debug", "node": "vm", "state": "drng", "reason": "gpu_xid:79"}]
    shares = exporter.parse_sshare(fx("sshare.txt"))
    assert shares[1]["account"] == "root" and shares[1]["user"] == "root"  # the indentation of sshare is stripped
    assert shares[0]["fairshare"] is None and shares[1]["fairshare"] == 1.0
    # squeue prints LOCAL time and the parser reads UTC: the commands must run with TZ=UTC
    seen = {}
    monkeypatch.setattr(exporter.subprocess, "run", lambda argv, **kw: seen.update(kw) or subprocess.CompletedProcess(argv, 0, "", ""))
    exporter.run_cmd(["squeue"])
    assert seen["env"]["TZ"] == "UTC"


def test_samples_from_a_busy_cluster():
    m = exporter.samples(fx("sinfo_mix.txt"), fx("squeue_mixed.txt"), fx("sshare.txt"), T0 + 100)
    assert metric(m, "slurm_nodes", state="mix") == 1
    assert metric(m, "slurm_jobs", state="PENDING") == 4 and metric(m, "slurm_jobs", state="RUNNING") == 1
    assert metric(m, "slurm_jobs_pending_by_reason", reason="Priority") == 3
    assert metric(m, "slurm_jobs_pending_by_reason", reason="Resources") == 1
    assert metric(m, "slurm_job_max_pending_seconds", partition="debug") == 100
    assert len(m["slurm_account_norm_shares"]) == 4  # one per account row; the user rows must not add duplicate series
    assert metric(m, "slurm_account_norm_shares", account="teama") == pytest.approx(0.333333)
    assert m["slurm_node_unhealthy"] == []


def test_unknown_pending_reasons_are_grouped_to_bound_cardinality():
    squeue = "9|debug|u|a|PENDING|SomethingNew_42|2026-10-24T18:20:15\n"
    m = exporter.samples(fx("sinfo_idle.txt"), squeue, "", T0 + 10)
    assert metric(m, "slurm_jobs_pending_by_reason", reason="other") == 1


def test_a_drained_node_is_unhealthy_with_a_bounded_reason():
    for name in ("sinfo_draining.txt", "sinfo_drained.txt"):
        m = exporter.samples(fx(name), "", "", T0)
        assert metric(m, "slurm_node_unhealthy", node="vm", reason="gpu_xid") == 1
    m = exporter.samples("debug*|vm|down*|4|12872|Not responding\n", "", "", T0)  # the most common unhealthy state, with its flag
    assert metric(m, "slurm_nodes", state="down") == 1 and metric(m, "slurm_node_unhealthy", node="vm") == 1


def test_idle_cluster_still_emits_zero_valued_job_series():
    m = exporter.samples(fx("sinfo_idle.txt"), fx("squeue_empty.txt"), "", T0)
    assert metric(m, "slurm_jobs", partition="debug", state="RUNNING") == 0
    assert metric(m, "slurm_jobs", partition="debug", state="PENDING") == 0  # "nothing runs" alerts need a 0, not an absence


def test_a_failing_command_gives_scrape_success_zero_and_nothing_else():
    def broken(argv):
        raise RuntimeError("slurmctld unreachable")
    out = exporter.collect(broken, now=T0)
    assert "slurm_scrape_success 0" in out and "slurm_jobs" not in out and "slurm_nodes" not in out
    garbled = {"sinfo": "", "squeue": "1|debug|u|a|PENDING|Priority|not-a-date\n", "sshare": ""}  # unparsable output is a failed scrape too
    assert "slurm_scrape_success 0" in exporter.collect(lambda argv: garbled[argv[0]], now=T0)


def test_collect_with_working_commands_reports_ok():
    outputs = {"sinfo": fx("sinfo_mix.txt"), "squeue": fx("squeue_mixed.txt"), "sshare": fx("sshare.txt")}
    out = exporter.collect(lambda argv: outputs[argv[0]], now=T0 + 5)
    assert "slurm_scrape_success 1" in out and 'slurm_jobs{partition="debug",state="PENDING"} 4' in out


def test_exposition_passes_promtool_check_metrics():
    outputs = {"sinfo": fx("sinfo_draining.txt"), "squeue": fx("squeue_mixed.txt"), "sshare": fx("sshare.txt")}
    out = exporter.collect(lambda argv: outputs[argv[0]], now=T0 + 5)
    r = subprocess.run([PROMTOOL, "check", "metrics"], input=out, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
