#!/usr/bin/env python3
"""USE-method triage from the kernel's own counters: Utilisation and Saturation of CPU, memory and disk.

Utilisation: share of time a resource is busy. Saturation: work that has to wait. For saturation we use
PSI (/proc/pressure/*: share of time at least one task is stalled) and, for the disk, the average queue
size from /proc/diskstats. Errors need hardware counters (see chapter 8) and are not covered here.
"""
import argparse
import json
import os
import sys
import time

THRESH = {"cpu_util": 0.9, "cpu_psi": 0.2, "mem_psi": 0.05, "io_psi": 0.1, "disk_util": 0.8}


def read_psi(root="/"):
    out = {}
    for res in ("cpu", "memory", "io"):
        with open(os.path.join(root, "proc/pressure", res)) as f:
            for line in f:
                kind, *kv = line.split()
                out[f"{res}_{kind}"] = int(dict(x.split("=") for x in kv)["total"])  # microseconds
    return out


def read_cpu(root="/"):
    with open(os.path.join(root, "proc/stat")) as f:
        fields = [int(x) for x in f.readline().split()[1:]]
    fields = fields[:8]  # user nice system idle iowait irq softirq steal; guest and guest_nice are already inside user/nice
    idle = fields[3] + fields[4]  # idle + iowait
    return {"busy": sum(fields) - idle, "total": sum(fields)}


def root_disk(root="/"):
    """Name of the block device holding the root filesystem, found through its major:minor in diskstats."""
    st = os.stat("/").st_dev
    major, minor = os.major(st), os.minor(st)
    with open(os.path.join(root, "proc/diskstats")) as f:
        for line in f:
            p = line.split()
            if int(p[0]) == major and int(p[1]) == minor:
                return p[2]
    return None


def read_disk(name, root="/"):
    with open(os.path.join(root, "proc/diskstats")) as f:
        for line in f:
            p = line.split()
            if p[2] == name:
                return {"io_ticks_ms": int(p[12]), "queue_ms": int(p[13])}
    raise KeyError(name)


def snapshot(disk, root="/"):
    return {"t": time.monotonic(), "psi": read_psi(root), "cpu": read_cpu(root), "disk": read_disk(disk, root)}


def compute(a, b):
    """Metrics between two snapshots; every value is a fraction of the elapsed time (aqu_sz is a count)."""
    dt = b["t"] - a["t"]
    cpu_total = b["cpu"]["total"] - a["cpu"]["total"]
    psi = lambda k: (b["psi"][k] - a["psi"][k]) / (dt * 1e6)
    return {
        "cpu_util": (b["cpu"]["busy"] - a["cpu"]["busy"]) / cpu_total if cpu_total else 0.0,
        "cpu_psi": psi("cpu_some"), "mem_psi": psi("memory_some"), "io_psi": psi("io_some"),
        "disk_util": (b["disk"]["io_ticks_ms"] - a["disk"]["io_ticks_ms"]) / (dt * 1000),
        "disk_aqu_sz": (b["disk"]["queue_ms"] - a["disk"]["queue_ms"]) / (dt * 1000),
    }


def classify(m, thresh=THRESH):
    """Human-readable findings; an empty list means nothing stands out."""
    out = []
    if m["cpu_util"] >= thresh["cpu_util"]:
        out.append("cpu: saturated (busy and tasks waiting)" if m["cpu_psi"] >= thresh["cpu_psi"]
                   else "cpu: busy, but no task is waiting for a core")
    if m["mem_psi"] >= thresh["mem_psi"]:
        out.append("memory: tasks stall on reclaim or swap")
    if m["io_psi"] >= thresh["io_psi"]:
        out.append("io: tasks are stalled waiting for the disk")
    elif m["disk_util"] >= thresh["disk_util"]:
        out.append("disk: busy, but no task stalls (asynchronous IO or a parallel device): look at latency")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--disk", default=None, help="block device name; default: the device of /")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    disk = a.disk or root_disk()
    if not disk:
        sys.exit("cannot find the block device of / in /proc/diskstats (LVM, overlayfs, network root?): pass --disk NAME")
    s0 = snapshot(disk)
    time.sleep(a.seconds)
    m = compute(s0, snapshot(disk))
    findings = classify(m)
    if a.json:
        print(json.dumps({"disk": disk, "metrics": m, "findings": findings}))
    else:
        print(f"disk={disk} " + " ".join(f"{k}={v:.2f}" for k, v in m.items()))
        print("\n".join(findings) if findings else "nothing stands out")
    return 0


if __name__ == "__main__":
    sys.exit(main())
