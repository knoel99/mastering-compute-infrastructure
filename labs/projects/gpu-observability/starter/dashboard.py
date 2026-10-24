#!/usr/bin/env python3
"""Grafana dashboard generator — TO WRITE (milestone 4).

build() -> dict: {"uid", "title", "schemaVersion", "panels": [...]} with at least 5 timeseries panels,
unique integer ids, a gridPos each, and for each panel targets=[{"refId", "expr", "legendFormat"}].
Every expression must be valid PromQL and use only metrics the exporter exposes (see tests/test_dashboard.py).
Per-job panels must JOIN the allocation metric, as the alert rules do.
"""
import json
import sys


def build():
    raise NotImplementedError


def main():
    json.dump(build(), sys.stdout, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
