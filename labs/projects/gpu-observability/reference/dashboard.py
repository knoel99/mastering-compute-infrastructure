#!/usr/bin/env python3
"""Generate a Grafana dashboard (JSON) for the simulated GPU fleet."""
import json
import sys

PANELS = [
    ("Tensor pipe activity per job", 'avg by (job) (DCGM_FI_PROF_PIPE_TENSOR_ACTIVE * on (Hostname, gpu) group_left (job) slurm_job_gpu_allocated)', "{{job}}"),
    ("GPU utilisation per job", 'avg by (job) (DCGM_FI_DEV_GPU_UTIL * on (Hostname, gpu) group_left (job) slurm_job_gpu_allocated)', "{{job}}"),
    ("Power per job (W, mean per GPU)", 'avg by (job) (DCGM_FI_DEV_POWER_USAGE * on (Hostname, gpu) group_left (job) slurm_job_gpu_allocated)', "{{job}}"),
    ("SM clock spread per job (max - min, MHz)", 'max by (job) (DCGM_FI_DEV_SM_CLOCK * on (Hostname, gpu) group_left (job) slurm_job_gpu_allocated) - min by (job) (DCGM_FI_DEV_SM_CLOCK * on (Hostname, gpu) group_left (job) slurm_job_gpu_allocated)', "{{job}}"),
    ("Hottest GPU per host (C)", 'max by (Hostname) (DCGM_FI_DEV_GPU_TEMP)', "{{Hostname}}"),
    ("GPUs reporting an XID error", 'count(DCGM_FI_DEV_XID_ERRORS > 0) or vector(0)', "xid"),
]


def build():
    panels = []
    for i, (title, expr, legend) in enumerate(PANELS):
        panels.append({"id": i + 1, "type": "timeseries", "title": title,
                       "gridPos": {"h": 8, "w": 12, "x": 12 * (i % 2), "y": 8 * (i // 2)},
                       "targets": [{"refId": "A", "expr": expr, "legendFormat": legend}]})
    return {"uid": "gpu-fleet-sim", "title": "GPU fleet (simulated)", "schemaVersion": 39, "version": 1,
            "time": {"from": "now-1h", "to": "now"}, "refresh": "30s", "panels": panels}


def main():
    json.dump(build(), sys.stdout, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
