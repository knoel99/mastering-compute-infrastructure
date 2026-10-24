import os
import re
import subprocess
import urllib.error
import urllib.request

import pytest

import exporter
from sim import ClusterSim

PROMTOOL = os.environ.get("PROMTOOL", "promtool")
NAMES = ["DCGM_FI_DEV_GPU_UTIL", "DCGM_FI_DEV_POWER_USAGE", "DCGM_FI_DEV_SM_CLOCK", "DCGM_FI_DEV_GPU_TEMP",
         "DCGM_FI_DEV_XID_ERRORS", "DCGM_FI_PROF_PIPE_TENSOR_ACTIVE"]


@pytest.fixture
def samples():
    return next(ClusterSim({"42": ["n1", "n2"]}, gpus_per_host=2, seed=1).frames(0))[1]


def test_output_is_valid_exposition_format(samples):
    """promtool lints naming conventions as well as syntax. dcgm-exporter's own labels (UUID, modelName,
    Hostname) break its snake_case convention; we keep them, because real rules and dashboards use them.
    Any OTHER complaint (or a parse error) fails the test."""
    r = subprocess.run([PROMTOOL, "check", "metrics"], input=exporter.render(samples), capture_output=True, text=True)
    complaints = [x for x in (r.stdout + r.stderr).splitlines() if x.strip()]
    other = [x for x in complaints if "label names should be written in 'snake_case'" not in x]
    assert not other, other
    assert r.returncode in (0, 3)  # 3 = lint problems only; 1 would be a parse error


def test_every_metric_has_help_type_and_one_line_per_gpu(samples):
    text = exporter.render(samples)
    for name in NAMES:
        assert f"# HELP {name} " in text and f"# TYPE {name} gauge" in text
        assert len(re.findall(rf"^{name}\{{", text, re.M)) == len(samples)


def test_labels_follow_dcgm_exporter_and_join_metric_covers_allocated_gpus(samples):
    text = exporter.render(samples)
    line = next(x for x in text.splitlines() if x.startswith("DCGM_FI_DEV_GPU_UTIL{"))
    for label in ("gpu=", "UUID=", "device=", "modelName=", "Hostname="):
        assert label in line
    joins = [x for x in text.splitlines() if x.startswith("slurm_job_gpu_allocated{")]
    assert len(joins) == len(samples) and all('job="42"' in x and x.endswith(" 1") for x in joins)


def test_values_are_plain_floats(samples):
    for line in exporter.render(samples).splitlines():
        if not line.startswith("#"):
            float(line.rsplit(" ", 1)[1])


def test_http_endpoint(samples):
    srv, port = exporter.serve(lambda: samples)
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=5)
        assert r.status == 200
        assert r.headers["Content-Type"].startswith("text/plain; version=0.0.4")
        assert r.read().decode() == exporter.render(samples)
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/other", timeout=5)
        assert e.value.code == 404
    finally:
        srv.shutdown()
