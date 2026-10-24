"""SkyPilot tasks and Kueue manifests — TO WRITE (milestone 4).

Structural validation only (no schema, no cluster). Field names follow the SkyPilot YAML spec and the Kueue concept
pages as read on 2026-10-24; check them against YOUR installed versions. Constants are given.
"""
import yaml  # noqa: F401

KUEUE_API = "kueue.x-k8s.io/v1beta2"
GPU_RESOURCE = "nvidia.com/gpu"
RECOVERY = ("FAILOVER", "EAGER_NEXT_REGION")


def skypilot_task(name, gpu, count, spot, run, candidates, ordered=True, recovery=None):
    """{"name", "resources": {"accelerators": "H100:8", "use_spot": bool, "ordered"|"any_of": [{"infra": c}, ...],
    optional "job_recovery": {"strategy": recovery}}, "run"}. ValueError on no candidate or a recovery not in RECOVERY."""
    raise NotImplementedError


def plan_tasks(job_name, gpu, count, ranked_offers, infra_map, run):
    """From offers ranked best-first, one task per market in ranking order (names job-spot / job-on-demand;
    infra = infra_map["provider/region"]); spot tasks get recovery EAGER_NEXT_REGION, on-demand tasks none."""
    raise NotImplementedError


def kueue_manifests(offers, namespace="team-a", cluster_queue="gpu-cq", local_queue="gpu-lq", order=None):
    """A ResourceFlavor per offer (spec.nodeLabels market and provider), one ClusterQueue with namespaceSelector {} and one
    resource group covering GPU_RESOURCE whose flavors follow `order` (offer ids; default: offers order) with
    nominalQuota = offer.capacity, one LocalQueue (metadata.namespace) pointing to the ClusterQueue."""
    raise NotImplementedError


def validate_kueue(docs):
    """True, or ValueError listing: duplicates, apiVersion != KUEUE_API, flavors not defined, resources not in
    coveredResources, nominalQuota not a non-negative int, LocalQueue pointing to an unknown ClusterQueue."""
    raise NotImplementedError


def dump(docs):
    """YAML text: one document (dict) or several (list, separated by '---'), keys in insertion order."""
    raise NotImplementedError
