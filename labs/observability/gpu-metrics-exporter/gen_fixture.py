"""Generate fixtures/dcgm_node.prom: ONE SCRAPE of a SIMULATED 8-GPU node in dcgm-exporter text format.

Everything here is invented for the lab (seeded, reproducible): metric names, types and help strings follow
dcgm-exporter's default-counters.csv, the values do not come from hardware. Faults planted on purpose:
  gpu 3  hot and clocked down (thermal throttling story)
  gpu 5  busy-looking but idle tensor pipe (the 'stalled collective' signature assumed by the course)
  gpu 6  last XID = 79 and idle (util 0, idle clock and power)
"""
import random
import sys

HOST, MODEL = "gpu-n01", "SIM-GPU 80GB"
FIELDS = [  # (name, type, help)
    ("DCGM_FI_DEV_SM_CLOCK", "gauge", "SM clock frequency (in MHz)."),
    ("DCGM_FI_DEV_GPU_TEMP", "gauge", "GPU temperature (in C)."),
    ("DCGM_FI_DEV_POWER_USAGE", "gauge", "Power draw (in W)."),
    ("DCGM_FI_DEV_GPU_UTIL", "gauge", "GPU utilization (in %)."),
    ("DCGM_FI_DEV_XID_ERRORS", "gauge", "Value of the last XID error encountered."),
    ("DCGM_FI_DEV_FB_USED", "gauge", "Framebuffer memory used (in MiB)."),
    ("DCGM_FI_PROF_PIPE_TENSOR_ACTIVE", "gauge", "Ratio of cycles the tensor (HMMA) pipe is active."),
]


def values(rng, gpu):
    v = {"DCGM_FI_DEV_SM_CLOCK": rng.gauss(1980, 8), "DCGM_FI_DEV_GPU_TEMP": rng.gauss(63, 1.5),
         "DCGM_FI_DEV_POWER_USAGE": rng.gauss(620, 15), "DCGM_FI_DEV_GPU_UTIL": min(100, rng.gauss(97, 1)),
         "DCGM_FI_DEV_XID_ERRORS": 0, "DCGM_FI_DEV_FB_USED": 61200 + rng.randint(-300, 300),
         "DCGM_FI_PROF_PIPE_TENSOR_ACTIVE": rng.gauss(0.55, 0.02)}
    if gpu == 3:
        v.update(DCGM_FI_DEV_GPU_TEMP=88.0, DCGM_FI_DEV_SM_CLOCK=1190.0, DCGM_FI_DEV_POWER_USAGE=540.0)
    if gpu == 5:
        v.update(DCGM_FI_DEV_GPU_UTIL=99.0, DCGM_FI_PROF_PIPE_TENSOR_ACTIVE=0.0, DCGM_FI_DEV_POWER_USAGE=255.0)
    if gpu == 6:
        v.update(DCGM_FI_DEV_XID_ERRORS=79, DCGM_FI_DEV_GPU_UTIL=0.0, DCGM_FI_PROF_PIPE_TENSOR_ACTIVE=0.0,
                 DCGM_FI_DEV_POWER_USAGE=70.0, DCGM_FI_DEV_SM_CLOCK=345.0)   # idle values: nothing runs on it any more
    return v


def render(seed=1):
    rng = random.Random(seed)
    per_gpu = [values(rng, g) for g in range(8)]
    out = []
    for name, typ, help_ in FIELDS:
        out += [f"# HELP {name} {help_}", f"# TYPE {name} {typ}"]
        for g, v in enumerate(per_gpu):
            lab = f'gpu="{g}",UUID="GPU-sim-{HOST}-{g}",device="nvidia{g}",modelName="{MODEL}",Hostname="{HOST}"'
            out.append(f"{name}{{{lab}}} {v[name]:.6g}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.stdout.write(render())
