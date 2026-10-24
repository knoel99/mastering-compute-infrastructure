#!/usr/bin/env python3
"""Turn a kernel log into a per-GPU triage: which Xids, how many, what to do.

The `catalog` labels are copied from the "immediate action" column of NVIDIA's Xid catalog (page read
on 2026-10-24); the `level` column is THIS COURSE'S policy (a recommendation, not an NVIDIA rule).
    python3 xid_triage.py fixtures/kernel_log_sample.txt
"""
import collections
import re
import sys

XID = re.compile(r"NVRM: Xid \((?:PCI:)?([0-9a-fA-F:.]+)\): (\d+)")

# xid: (catalog immediate-action label, course level)  level: 0 watch, 1 restart job, 2 drain the node
CATALOG = {
    13: ("RESTART_APP", 1), 31: ("RESTART_APP", 1), 43: ("IGNORE", 0), 45: ("WORKFLOW_XID_45", 0),
    48: ("WORKFLOW_XID_48", 2), 63: ("IGNORE", 0), 64: ("RESET_GPU", 2), 74: ("WORKFLOW_NVLINK_ERR", 2),
    79: ("RESTART_BM", 2), 94: ("RESTART_APP", 1), 95: ("RESET_GPU", 2), 119: ("RESET_GPU", 2),
    120: ("RESET_GPU", 2), 140: ("RESET_GPU", 2), 154: ("XID_154", 0),
}
VERDICT = {0: "watch", 1: "restart-job", 2: "drain-node"}


def triage(lines):
    """{gpu: Counter(xid)} and the node verdict (the worst level seen)."""
    per_gpu = collections.defaultdict(collections.Counter)
    for line in lines:
        if line.lstrip().startswith("#"):  # comments of the fixture file, not log lines
            continue
        m = XID.search(line)
        if m:
            per_gpu[m.group(1)][int(m.group(2))] += 1
    level = max((CATALOG.get(x, ("UNKNOWN", 1))[1] for c in per_gpu.values() for x in c), default=0)
    return per_gpu, VERDICT[level]


def main(argv):
    per_gpu, verdict = triage(open(argv[1], encoding="utf-8"))
    for gpu, c in sorted(per_gpu.items()):
        for xid, n in sorted(c.items()):
            label, level = CATALOG.get(xid, ("UNKNOWN", 1))
            print(f"gpu {gpu}  xid {xid:>3}  x{n}  catalog={label:<20} course-level={VERDICT[level]}")
    print(f"node verdict: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
