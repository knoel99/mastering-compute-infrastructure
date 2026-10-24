"""SkyPilot tasks and Kueue manifests generated from placement decisions.

STRUCTURAL validation only: shapes and cross-references are checked here, NOT against the official schemas
(no cluster, no CRDs, no cloud account in the sandbox). Field names follow the SkyPilot YAML spec and the Kueue
concept pages as read on 2026-10-24 (SkyPilot `infra:`, `ordered`, `any_of`, `job_recovery.strategy`;
Kueue kueue.x-k8s.io/v1beta2). Check them against YOUR installed versions before applying anything.
"""
import yaml

KUEUE_API = "kueue.x-k8s.io/v1beta2"
GPU_RESOURCE = "nvidia.com/gpu"
RECOVERY = ("FAILOVER", "EAGER_NEXT_REGION")


def skypilot_task(name, gpu, count, spot, run, candidates, ordered=True, recovery=None):
    """One SkyPilot task. candidates: list of "provider/region" strings, tried in order (ordered) or by cost (any_of)."""
    if not candidates:
        raise ValueError("at least one candidate infra is required")
    if recovery is not None and recovery not in RECOVERY:
        raise ValueError(f"recovery must be one of {RECOVERY}")
    resources = {"accelerators": f"{gpu}:{count}", "use_spot": bool(spot),
                 ("ordered" if ordered else "any_of"): [{"infra": c} for c in candidates]}
    if recovery:
        resources["job_recovery"] = {"strategy": recovery}
    return {"name": name, "resources": resources, "run": run}


def plan_tasks(job_name, gpu, count, ranked_offers, infra_map, run):
    """From offers ranked best-first by a policy, build one task per market (spot first when it ranks first).

    A SkyPilot task has a single use_spot flag, so a spot-then-on-demand fallback is two tasks, launched in order
    by whatever orchestrates the jobs. infra_map maps "provider/region" of the synthetic data to a real infra string.
    """
    groups = {}
    for o in ranked_offers:
        groups.setdefault(o.market, []).append(infra_map[f"{o.provider}/{o.region}"])
    tasks = []
    for market in dict.fromkeys(o.market for o in ranked_offers):
        spot = market == "spot"
        tasks.append(skypilot_task(f"{job_name}-{market.replace('_', '-')}", gpu, count, spot, run, groups[market],
                                   recovery="EAGER_NEXT_REGION" if spot else None))
    return tasks


def kueue_manifests(offers, namespace="team-a", cluster_queue="gpu-cq", local_queue="gpu-lq", order=None):
    """ResourceFlavor per offer, one ClusterQueue whose flavors follow `order` (offer ids, most preferred first:
    Kueue gives a workload the FIRST flavor with enough unused quota), one LocalQueue pointing to it."""
    by_id = {o.id: o for o in offers}
    ids = list(order) if order else [o.id for o in offers]
    docs = [{"apiVersion": KUEUE_API, "kind": "ResourceFlavor", "metadata": {"name": o.id},
             "spec": {"nodeLabels": {"market": o.market, "provider": o.provider}}} for o in offers]
    flavors = [{"name": i, "resources": [{"name": GPU_RESOURCE, "nominalQuota": by_id[i].capacity}]} for i in ids]
    docs.append({"apiVersion": KUEUE_API, "kind": "ClusterQueue", "metadata": {"name": cluster_queue},
                 "spec": {"namespaceSelector": {}, "resourceGroups": [{"coveredResources": [GPU_RESOURCE], "flavors": flavors}]}})
    docs.append({"apiVersion": KUEUE_API, "kind": "LocalQueue", "metadata": {"namespace": namespace, "name": local_queue},
                 "spec": {"clusterQueue": cluster_queue}})
    return docs


def validate_kueue(docs):
    """Raise ValueError listing every structural problem: duplicates, dangling references, bad quotas."""
    problems = []
    seen = set()
    for d in docs:
        key = (d.get("kind"), d.get("metadata", {}).get("namespace"), d.get("metadata", {}).get("name"))
        if key in seen:
            problems.append(f"duplicate {key}")
        seen.add(key)
        if d.get("apiVersion") != KUEUE_API:
            problems.append(f"{key}: apiVersion {d.get('apiVersion')!r} != {KUEUE_API}")
    flavors = {d["metadata"]["name"] for d in docs if d.get("kind") == "ResourceFlavor"}
    cqs = {d["metadata"]["name"] for d in docs if d.get("kind") == "ClusterQueue"}
    for d in docs:
        if d.get("kind") == "ClusterQueue":
            for g in d["spec"].get("resourceGroups", []):
                covered = set(g.get("coveredResources", []))
                for f in g.get("flavors", []):
                    if f["name"] not in flavors:
                        problems.append(f"ClusterQueue {d['metadata']['name']}: unknown flavor {f['name']}")
                    for r in f.get("resources", []):
                        if r["name"] not in covered:
                            problems.append(f"flavor {f['name']}: resource {r['name']} not in coveredResources")
                        q = r.get("nominalQuota")
                        if not isinstance(q, int) or isinstance(q, bool) or q < 0:
                            problems.append(f"flavor {f['name']}: nominalQuota {q!r} must be a non-negative integer")
        if d.get("kind") == "LocalQueue" and d["spec"].get("clusterQueue") not in cqs:
            problems.append(f"LocalQueue {d['metadata']['name']}: unknown ClusterQueue {d['spec'].get('clusterQueue')}")
    if problems:
        raise ValueError("; ".join(problems))
    return True


def dump(docs):
    """YAML text; several documents are separated by '---'."""
    one = isinstance(docs, dict)
    items = [docs] if one else list(docs)
    return "\n---\n".join(yaml.safe_dump(d, sort_keys=False) for d in items)
