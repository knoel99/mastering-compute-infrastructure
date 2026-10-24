#!/usr/bin/env python3
"""Rebuild schemas/crds.json (JobSet v0.13.0 and Kubeflow Trainer v2.1.0 TrainJob) from the upstream CRDs.

Same method as ../kueue-manifests/fetch_schemas.py: keep the OpenAPI schema of the served version, drop prose
(`description`) and CEL rules. Both upstream projects are Apache-2.0. Needs outbound HTTPS to raw.githubusercontent.com.
"""
import json
import urllib.request
from pathlib import Path

import yaml

SOURCES = [
    ("jobset v0.13.0", "https://raw.githubusercontent.com/kubernetes-sigs/jobset/v0.13.0/config/components/crd/bases/jobset.x-k8s.io_jobsets.yaml"),
    ("kubeflow/trainer v2.1.0", "https://raw.githubusercontent.com/kubeflow/trainer/v2.1.0/manifests/base/crds/trainer.kubeflow.org_trainjobs.yaml"),
]


def strip(node, is_property_map=False):
    if isinstance(node, dict):
        if is_property_map:
            return {k: strip(v) for k, v in node.items()}
        return {k: strip(v, k == "properties") for k, v in node.items() if k not in ("description", "x-kubernetes-validations")}
    if isinstance(node, list):
        return [strip(v) for v in node]
    return node


def main():
    kinds, sources = {}, []
    for label, url in SOURCES:
        crd = yaml.safe_load(urllib.request.urlopen(url, timeout=120).read())
        (v,) = [v for v in crd["spec"]["versions"] if v.get("served")]
        kinds[crd["spec"]["names"]["kind"]] = {"apiVersion": f'{crd["spec"]["group"]}/{v["name"]}', "scope": crd["spec"]["scope"],
                                               "schema": strip(v["schema"]["openAPIV3Schema"])}
        sources.append(label)
    dest = Path(__file__).parent / "schemas" / "crds.json"
    dest.write_text(json.dumps({"source": sources, "kinds": kinds}, sort_keys=True, separators=(",", ":")))
    print(f"wrote {dest} ({dest.stat().st_size} bytes) from {', '.join(sources)}")


if __name__ == "__main__":
    main()
