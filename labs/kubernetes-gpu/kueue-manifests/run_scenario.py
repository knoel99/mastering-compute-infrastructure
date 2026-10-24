#!/usr/bin/env python3
"""Replay a scenario on the admission model and print a readable trace.

Usage: run_scenario.py SCENARIO.yaml [--impl reference|starter] [--manifests DIR]
Queues, quotas, policies and priority values are read from the manifests (the same files that
validate_manifests.py checks), so the model and the manifests cannot drift apart.
"""
import argparse
import sys
from pathlib import Path

import yaml

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
from model import GPU, Workload, gpu_request, load_priorities, load_queues  # noqa: E402

def load_local_queues(manifests_dir):
    """(namespace, LocalQueue name) -> ClusterQueue name, from the LocalQueue manifests."""
    out = {}
    for f in sorted(Path(manifests_dir).glob("*.y*ml")):
        for doc in yaml.safe_load_all(f.read_text()):
            if doc and doc.get("kind") == "LocalQueue":
                out[(doc["metadata"]["namespace"], doc["metadata"]["name"])] = doc["spec"]["clusterQueue"]
    return out


def table(cluster, queues):
    rows = []
    for name, q in queues.items():
        used = cluster.usage(name)[GPU]
        pend = [f"{w.name}({w.requests[GPU]:g})" for w in sorted(cluster.pending(name), key=lambda w: w.created)]
        run = [f"{w.name}({w.requests[GPU]:g})" for w in sorted(cluster.admitted(name), key=lambda w: w.admitted_seq)]
        rows.append(f"      {name:<11} {used:>3g}/{q.nominal[GPU]:g} GPU  running: {', '.join(run) or '-':<40} pending: {', '.join(pend) or '-'}")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("--impl", default="reference", choices=["reference", "starter"])
    ap.add_argument("--manifests", default=str(LAB / "manifests"))
    a = ap.parse_args()
    sys.path.insert(0, str(LAB / a.impl))
    from admission import Cluster

    queues, prio, local = load_queues(a.manifests), load_priorities(a.manifests), load_local_queues(a.manifests)
    cluster = Cluster(queues)
    steps = yaml.safe_load(Path(a.scenario).read_text())["steps"]
    print(f"cohort gpu-pool: {sum(q.nominal[GPU] for q in queues.values()):g} GPUs of nominal quota; implementation: {a.impl}")
    for s in steps:
        if "submit" in s:
            d = s["submit"]
            q = local[(d["ns"], d["queue"])]
            req = {r: v for r, v in gpu_request(d["gpus"]).items() if r in queues[q].nominal}   # only what the queue covers
            wl = Workload(d["name"], q, prio[d["priority"]], req)
            print(f"t={s['t']:>3} min  submit {d['name']} ({d['gpus']} GPU, priority {d['priority']}={prio[d['priority']]}) to {d['ns']}/{d['queue']}")
            cluster.submit(wl)
        else:
            print(f"t={s['t']:>3} min  finish {s['finish']}")
            cluster.finish(s["finish"])
        for e in cluster.schedule():
            print(f"            -> {e.kind.upper():<7} {e.workload} [{e.queue}] {e.detail}")
        print(table(cluster, queues))
    return 0


if __name__ == "__main__":
    sys.exit(main())
