#!/usr/bin/env python3
"""OFFLINE parse of the task files with the real SkyPilot code (sky.Task.from_yaml): no cloud account, no credentials.

Checked against SkyPilot 0.14.1 on 2026-10-24. What this catches: unknown keys, wrong types, bad mount modes, malformed
accelerators. What it does NOT catch (seen while writing the lab): an invalid job_recovery strategy name is accepted at
parse time, and nothing here proves that a location has capacity or that your quota allows the request.
"""
import copy
import os
import sys
import tempfile

import sky
import yaml


def parse(cfg):
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
        yaml.safe_dump(cfg, fh)
        path = fh.name
    try:
        return sky.Task.from_yaml(path)
    finally:
        os.unlink(path)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    print(f"skypilot {sky.__version__}")
    for name in ("job.yaml", "dev-cluster.yaml", "bad-job.yaml", "job-eu.yaml"):
        t = sky.Task.from_yaml(os.path.join(here, name))
        print(f"  {name}: parsed, num_nodes={t.num_nodes}, candidates={sorted(str(r) for r in t.resources)}")
    cfg = yaml.safe_load(open(os.path.join(here, "job.yaml"), encoding="utf-8"))
    mutations = {
        "unknown key in resources": lambda c: c["resources"].update(use_spott=True),
        "use_spot is not a boolean": lambda c: c["resources"].update(use_spot="yes please"),
        "unknown mount mode": lambda c: c["file_mounts"]["/checkpoint"].update(mode="BOGUS"),
        "malformed accelerators": lambda c: c["resources"].update(accelerators="H100:eight"),
        "unknown top-level key": lambda c: c.update(runn="echo"),
    }
    for label, mutate in mutations.items():
        bad = copy.deepcopy(cfg)
        mutate(bad)
        try:
            parse(bad)
        except Exception as exc:  # noqa: BLE001 - any rejection counts
            print(f"  rejected as expected: {label} ({type(exc).__name__})")
        else:
            print(f"FAIL: SkyPilot accepted a mutated file: {label}", file=sys.stderr)
            return 1
    print("OK skypilot parse: 4 files accepted (bad-job.yaml is valid for SkyPilot, only the policy refuses it), 5 mutations rejected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
