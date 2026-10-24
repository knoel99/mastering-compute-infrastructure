"""Mutation testing for alert rules: change one thing in a rule file, run promtool test, demand a failure.

A promtool suite that passes on a broken rule is decoration. Each mutant below models a classic mistake.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
P, S = "rules/platform.rules.yml", "rules/slo.rules.yml"
# (name, rule file, test file, old text, new text)  -- every occurrence of `old` is replaced
MUTANTS = [
    ("GPUHot: for 5m -> 30m", P, "platform", "for: 5m\n        keep_firing_for", "for: 30m\n        keep_firing_for"),
    ("GPUHot: comparison inverted", P, "platform", "DCGM_FI_DEV_GPU_TEMP > 85", "DCGM_FI_DEV_GPU_TEMP < 85"),
    ("GPUHot: keep_firing_for removed", P, "platform", "        keep_firing_for: 10m\n", ""),
    ("NodeSlow: threshold 1.3 -> 3", P, "platform", "ratio_to_job_median > 1.3", "ratio_to_job_median > 3"),
    ("NodeSlow: ratio against mean-like max", P, "platform", "quantile by (job) (0.5,", "quantile by (job) (1.0,"),
    ("JobNoProgress: window 10m -> 5m", P, "platform", "increase(train_steps_total[10m])", "increase(train_steps_total[5m])"),
    ("JobNoProgress: == 0 -> < 50", P, "platform", "increase10m_max == 0", "increase10m_max < 50"),
    ("GpuTelemetryDown: == 0 -> == 1", P, "platform", 'up{job="dcgm"} == 0', 'up{job="dcgm"} == 1'),
    ("SLO: fast burn threshold 0.72 -> 0.072", S, "slo", "> 0.72", "> 0.072"),
    ("SLO: short window 5m -> 1h (no quick reset)", S, "slo", "[5m]", "[1h]"),
    ("SLO: wrong bucket le", S, "slo", 'le="600.0"', 'le="1800.0"'),
    ("SLO: slow burn threshold 0.3 -> 0.1", S, "slo", "> 0.3 ", "> 0.1 "),
]


def main():
    survivors = []
    for name, rel, suite, old, new in MUTANTS:
        with tempfile.TemporaryDirectory() as tmp:
            for d in ("rules", "tests", "runbooks"):
                shutil.copytree(HERE / d, Path(tmp) / d)
            f = Path(tmp) / rel
            src = f.read_text()
            assert old in src, f"{name}: pattern not found in {rel}"
            f.write_text(src.replace(old, new))
            env = dict(os.environ, GOMAXPROCS="2")
            r = subprocess.run(["nice", "-n", "10", "promtool", "test", "rules", f"tests/{suite}.rules.test.yml"],
                               cwd=tmp, env=env, capture_output=True, text=True)
        status = "killed" if r.returncode != 0 else "SURVIVED"
        print(f"  mutant {name:<46} {status}")
        if r.returncode == 0:
            survivors.append(name)
    if survivors:
        print("FAIL: surviving mutants:", survivors)
        return 1
    print(f"OK mutants: {len(MUTANTS)}/{len(MUTANTS)} killed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
