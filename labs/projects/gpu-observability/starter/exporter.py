"""Prometheus text exposition of simulated samples, with dcgm-exporter metric names — TO WRITE (milestone 1).

METRICS and CONTENT_TYPE are given. Write render() and serve(); see tests/test_exporter.py.
"""
import http.server  # noqa: F401  (you will need it)
import threading  # noqa: F401

from sim import MODEL  # noqa: F401

METRICS = [
    # (name, type, help, Sample field) — names, types and help texts follow dcgm-exporter's default counters
    ("DCGM_FI_DEV_GPU_UTIL", "gauge", "GPU utilization (in %).", "util"),
    ("DCGM_FI_DEV_POWER_USAGE", "gauge", "Power draw (in W).", "power"),
    ("DCGM_FI_DEV_SM_CLOCK", "gauge", "SM clock frequency (in MHz).", "sm_clock"),
    ("DCGM_FI_DEV_GPU_TEMP", "gauge", "GPU temperature (in C).", "temp"),
    ("DCGM_FI_DEV_XID_ERRORS", "gauge", "Value of the last XID error encountered.", "xid"),
    ("DCGM_FI_PROF_PIPE_TENSOR_ACTIVE", "gauge", "Ratio of cycles the tensor (HMMA) pipe is active.", "tensor"),
]
CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


def render(samples):
    """Exposition text for one scrape: for each metric one HELP and one TYPE line, then one line per
    sample with labels gpu, UUID, device, modelName, Hostname (as dcgm-exporter does). Then the join
    metric slurm_job_gpu_allocated{Hostname, gpu, job} 1 for every ALLOCATED sample (job != "")."""
    raise NotImplementedError


def serve(get_samples, port=0):
    """Serve /metrics on 127.0.0.1 in a daemon thread (404 elsewhere); get_samples() returns the latest
    samples. Return (server, port); the caller stops it with server.shutdown()."""
    raise NotImplementedError
