"""Data model shared by the starter and the reference implementation (do not edit).

This is a SIMPLIFIED MODEL of the documented behaviour of Kueue v0.20 "Classic Preemption" with one flavor:
it is not Kueue's code and it ignores flavors fungibility, fair sharing, admission checks, partial admission
and the real asynchronous eviction. See README.md for what is and is not modelled.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

GPU = "nvidia.com/gpu"


def quantity(q) -> float:
    """Kubernetes quantity -> float (cpu in cores, memory in bytes, GPUs as counts)."""
    s = str(q)
    for suf, mul in (("Ki", 2**10), ("Mi", 2**20), ("Gi", 2**30), ("Ti", 2**40), ("m", 1e-3), ("k", 1e3), ("M", 1e6), ("G", 1e9)):
        if s.endswith(suf):
            return float(s[: -len(suf)]) * mul
    return float(s)


@dataclass(frozen=True)
class QueueConfig:
    """What the lab reads from a ClusterQueue manifest (spec.cohortName, quotas, policies)."""
    name: str
    cohort: str | None
    nominal: dict                      # resource -> nominalQuota
    borrowing_limit: dict              # resource -> limit (absent = no limit)
    lending_limit: dict                # resource -> limit (absent = everything can be lent)
    strategy: str = "BestEffortFIFO"   # or StrictFIFO
    within_cq: str = "Never"           # Never | LowerPriority | LowerOrNewerEqualPriority
    reclaim: str = "Never"             # Never | LowerPriority | Any
    borrow_policy: str = "Never"       # borrowWithinCohort.policy: Never | LowerPriority
    borrow_threshold: int | None = None  # borrowWithinCohort.maxPriorityThreshold


@dataclass
class Workload:
    name: str
    queue: str                         # ClusterQueue name (the LocalQueue indirection is resolved by the caller)
    priority: int
    requests: dict
    created: int = 0                   # submission order, assigned by Cluster.submit
    admitted_seq: int = -1             # admission order, assigned when admitted
    state: str = "pending"             # pending | admitted


@dataclass(frozen=True)
class Event:
    kind: str                          # "admit" | "preempt"
    workload: str
    queue: str
    detail: str                        # admit: "nominal" | "borrowing"; preempt: reason + preemptor


def load_queues(manifests_dir) -> dict:
    """Read every ClusterQueue of a manifests directory (v1beta2) into QueueConfig objects."""
    out = {}
    for f in sorted(Path(manifests_dir).glob("*.y*ml")):
        for doc in yaml.safe_load_all(f.read_text()):
            if not doc or doc.get("kind") != "ClusterQueue":
                continue
            spec = doc["spec"]
            nominal, borrow, lend = {}, {}, {}
            for rg in spec["resourceGroups"]:
                for fl in rg["flavors"]:           # one flavor per queue in this model: the first one is used
                    for r in fl["resources"]:
                        nominal[r["name"]] = quantity(r["nominalQuota"])
                        if "borrowingLimit" in r:
                            borrow[r["name"]] = quantity(r["borrowingLimit"])
                        if "lendingLimit" in r:
                            lend[r["name"]] = quantity(r["lendingLimit"])
                    break
            pre = spec.get("preemption", {})
            bwc = pre.get("borrowWithinCohort", {})
            out[doc["metadata"]["name"]] = QueueConfig(
                name=doc["metadata"]["name"], cohort=spec.get("cohortName"), nominal=nominal,
                borrowing_limit=borrow, lending_limit=lend,
                strategy=spec.get("queueingStrategy", "BestEffortFIFO"),
                within_cq=pre.get("withinClusterQueue", "Never"), reclaim=pre.get("reclaimWithinCohort", "Never"),
                borrow_policy=bwc.get("policy", "Never"), borrow_threshold=bwc.get("maxPriorityThreshold"))
    return out


def load_priorities(manifests_dir) -> dict:
    """WorkloadPriorityClass name -> value."""
    out = {}
    for f in sorted(Path(manifests_dir).glob("*.y*ml")):
        for doc in yaml.safe_load_all(f.read_text()):
            if doc and doc.get("kind") == "WorkloadPriorityClass":
                out[doc["metadata"]["name"]] = int(doc["value"])
    return out


def gpu_request(n: int) -> dict:
    """Requests of an n-GPU workload with the lab's ratio: 8 cores and 64 GiB per GPU."""
    return {GPU: float(n), "cpu": 8.0 * n, "memory": 64.0 * 2**30 * n}


__all__ = ["GPU", "QueueConfig", "Workload", "Event", "field", "load_queues", "load_priorities", "gpu_request", "quantity"]
