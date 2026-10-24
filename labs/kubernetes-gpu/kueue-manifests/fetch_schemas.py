#!/usr/bin/env python3
"""Rebuild schemas/kueue-v1beta2.json from the upstream CRDs (needs outbound HTTPS to raw.githubusercontent.com).

The vendored file keeps, for each Kueue kind used by the lab, the OpenAPI v3 schema of the served version
(v1beta2) with every `description` removed to keep the file small. Upstream: kubernetes-sigs/kueue, Apache-2.0.
Usage: python3 fetch_schemas.py [TAG]   (default tag: the one written in schemas/SOURCE.txt)
"""
import json
import sys
import urllib.request
from pathlib import Path

import yaml

TAG = sys.argv[1] if len(sys.argv) > 1 else "v0.20.3"
KINDS = ["clusterqueues", "localqueues", "resourceflavors", "workloadpriorityclasses", "cohorts", "topologies"]
BASE = "https://raw.githubusercontent.com/kubernetes-sigs/kueue/{tag}/config/components/crd/bases/kueue.x-k8s.io_{plural}.yaml"


def strip(node, is_property_map=False):
    """Drop prose and Kubernetes-only extensions that a generic JSON-Schema validator cannot use.

    Keys of a `properties` map are field names and are always kept (a field may itself be called `description`)."""
    if isinstance(node, dict):
        if is_property_map:
            return {k: strip(v) for k, v in node.items()}
        return {k: strip(v, k == "properties") for k, v in node.items() if k not in ("description", "x-kubernetes-validations")}
    if isinstance(node, list):
        return [strip(v) for v in node]
    return node


def main():
    out = {}
    for plural in KINDS:
        raw = urllib.request.urlopen(BASE.format(tag=TAG, plural=plural), timeout=60).read()
        crd = yaml.safe_load(raw)
        served = [v for v in crd["spec"]["versions"] if v.get("served")]
        assert len(served) == 1, (plural, [v["name"] for v in served])
        v = served[0]
        out[crd["spec"]["names"]["kind"]] = {
            "apiVersion": f'{crd["spec"]["group"]}/{v["name"]}',
            "scope": crd["spec"]["scope"],
            "schema": strip(v["schema"]["openAPIV3Schema"]),
        }
    dest = Path(__file__).parent / "schemas" / "kueue-v1beta2.json"
    dest.write_text(json.dumps({"source": f"kubernetes-sigs/kueue {TAG}", "kinds": out}, sort_keys=True, separators=(",", ":")))
    print(f"wrote {dest} ({dest.stat().st_size} bytes) from kueue {TAG}")


if __name__ == "__main__":
    main()
