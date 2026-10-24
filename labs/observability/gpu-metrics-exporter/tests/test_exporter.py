import json
import os
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

import pytest
from prometheus_client import generate_latest
from prometheus_client.parser import text_string_to_metric_families

import exporter

FIX = Path(os.environ.get("FIXDIR") or Path(__file__).resolve().parent.parent / "fixtures")
NOW = 1792864230  # six seconds after the first capture: makes pending ages deterministic


def load(name):
    return json.loads((FIX / "slurm" / name).read_text())


def scrape(dcgm=None, squeue=None, sinfo=None, sacct=True):
    dcgm = dcgm or (lambda: (FIX / "dcgm_node.prom").read_text())
    squeue = squeue or (lambda: load("squeue_busy.json"))
    sinfo = sinfo or (lambda: load("sinfo_mixed.json"))
    reg, waits = exporter.build_registry(dcgm, squeue, sinfo, now=lambda: NOW)
    if sacct:
        waits.observe_sacct((FIX / "slurm" / "sacct.txt").read_text())
    text = generate_latest(reg).decode()
    samples = {}
    for fam in text_string_to_metric_families(text):
        for s in fam.samples:
            samples[(s.name, tuple(sorted(s.labels.items())))] = s.value
    return text, samples


def value(samples, name, **labels):
    return samples[(name, tuple(sorted(labels.items())))]


def boom():
    raise RuntimeError("source down")


# ---------------------------------------------------------------- GPU node summary
def test_parse_dcgm_reads_every_gpu_and_field():
    gpus = exporter.parse_dcgm((FIX / "dcgm_node.prom").read_text())
    assert sorted(gpus) == list(range(8))
    assert gpus[6]["DCGM_FI_DEV_XID_ERRORS"] == 79
    assert gpus[0]["Hostname"] == "gpu-n01"


def test_node_summary_matches_planted_faults():
    _, s = scrape()
    n = {"node": "gpu-n01"}
    assert value(s, "gpu_node_gpus", **n) == 8
    assert value(s, "gpu_node_hot_gpus", **n) == 1          # gpu 3 at 88 C
    assert value(s, "gpu_node_xid_gpus", **n) == 1          # gpu 6, XID 79
    assert value(s, "gpu_node_busy_but_tensor_idle_gpus", **n) == 1  # gpu 5 only: gpu 6 is idle, not busy
    assert 0.55 < value(s, "gpu_node_sm_clock_min_over_median_ratio", **n) < 0.65  # 1190 MHz vs ~1975; the idle gpu 6 (345 MHz) is ignored
    assert value(s, "gpu_node_scrape_success") == 1


def test_failing_source_reports_zero_and_serves_no_values():
    _, s = scrape(dcgm=boom)
    assert value(s, "gpu_node_scrape_success") == 0
    assert not any(name == "gpu_node_gpus" for name, _ in s)


def test_text_without_gpu_samples_is_a_failure_not_an_empty_success():
    _, s = scrape(dcgm=lambda: "# HELP x y\n# TYPE x gauge\nx 1\n")
    assert value(s, "gpu_node_scrape_success") == 0


# ---------------------------------------------------------------- Slurm queue
def test_reason_classes_are_a_closed_set():
    seen = {exporter.reason_class(r) for r in list(exporter.REASON_CLASS) + ["SomethingNewInSlurm 99", ""]}
    assert seen <= {"capacity", "user", "admin", "config", "other"}
    assert exporter.reason_class("SomethingNewInSlurm 99") == "other"


def test_queue_counts_from_a_real_capture():
    _, s = scrape()
    assert value(s, "slurm_jobs", state="pending", reason_class="capacity") == 3   # Priority x2, Resources
    assert value(s, "slurm_jobs", state="pending", reason_class="user") == 2       # JobHeldUser, Dependency
    assert value(s, "slurm_jobs", state="running", reason_class="none") == 1
    assert value(s, "slurm_pending_oldest_age_seconds", reason_class="capacity") == 26
    assert value(s, "slurm_nodes", partition="debug", state="mixed") == 1
    assert value(s, "slurm_cpus", partition="debug", state="idle") == 1


def test_draining_node_is_visible_with_a_bounded_reason_class():
    _, s = scrape(squeue=lambda: load("squeue_drained.json"), sinfo=lambda: load("sinfo_draining.json"))
    assert value(s, "slurm_nodes", partition="debug", state="draining") == 1
    assert value(s, "slurm_node_drain_info", node="vm", reason_class="health") == 1
    # pending jobs on a draining node wait for capacity (Priority x2, Resources): the platform, not the user, is to blame
    assert value(s, "slurm_jobs", state="pending", reason_class="capacity") == 3


def test_node_state_collapse():
    assert exporter.node_state(["IDLE"]) == "idle"
    assert exporter.node_state(["MIXED", "DRAIN"]) == "draining"
    assert exporter.node_state(["IDLE", "DRAIN"]) == "drained"
    assert exporter.node_state(["DOWN", "DRAIN"]) == "down"


def test_failing_slurm_reports_zero():
    _, s = scrape(squeue=boom)
    assert value(s, "slurm_scrape_success") == 0
    assert not any(name == "slurm_jobs" for name, _ in s)


# ---------------------------------------------------------------- wait histogram
def test_each_finished_job_is_observed_once():
    reg, waits = exporter.build_registry(lambda: "", lambda: {}, lambda: {})
    text = (FIX / "slurm" / "sacct.txt").read_text()
    assert waits.observe_sacct(text) == 6        # jobs 2, 3, 6 never started: no wait to report
    assert waits.observe_sacct(text) == 0        # a second poll must not double count
    samples = {(s.name, tuple(sorted(s.labels.items()))): s.value
               for f in text_string_to_metric_families(generate_latest(reg).decode()) for s in f.samples}
    assert value(samples, "slurm_job_wait_seconds_count", qos="normal") == 6
    assert value(samples, "slurm_job_wait_seconds_sum", qos="normal") == 45      # 1+2+5+8+12+17 s
    assert value(samples, "slurm_job_wait_seconds_bucket", qos="normal", le="10.0") == 4
    assert value(samples, "slurm_job_wait_seconds_bucket", qos="normal", le="30.0") == 6


# ---------------------------------------------------------------- conventions and cardinality
ALLOWED_LABELS = {"node", "state", "reason_class", "partition", "qos", "le"}


def test_names_and_labels_follow_the_conventions():
    text, s = scrape()
    for name, labels in s:
        assert re.fullmatch(r"[a-z][a-z0-9_]*", name), name
        assert {k for k, _ in labels} <= ALLOWED_LABELS, (name, labels)   # no job id, no user, no free text
    for fam in text_string_to_metric_families(text):
        if fam.type == "gauge" and fam.name.endswith("_seconds"):
            assert "duration" in fam.name or "age" in fam.name or "wait" in fam.name


def test_series_budget_for_one_node_and_a_small_cluster():
    _, s = scrape()
    assert len(s) < 70   # fixed cost per node + per partition; see README for the fleet-size arithmetic


# ---------------------------------------------------------------- lint and HTTP
@pytest.mark.skipif(shutil.which("promtool") is None, reason="promtool not installed")
def test_promtool_check_metrics_accepts_the_output():
    text, _ = scrape()
    r = subprocess.run(["promtool", "check", "metrics"], input=text, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_http_scrape_roundtrip():
    from prometheus_client import start_http_server
    reg, _ = exporter.build_registry(lambda: (FIX / "dcgm_node.prom").read_text(),
                                     lambda: load("squeue_busy.json"), lambda: load("sinfo_mixed.json"))
    server, thread = start_http_server(0, addr="127.0.0.1", registry=reg)
    try:
        body = urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/metrics", timeout=5).read().decode()
    finally:
        server.shutdown()
    assert 'gpu_node_hot_gpus{node="gpu-n01"} 1.0' in body
