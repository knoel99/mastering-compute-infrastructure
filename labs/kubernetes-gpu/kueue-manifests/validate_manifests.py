#!/usr/bin/env python3
"""Offline validation of Kubernetes manifests.

* Kueue kinds (ClusterQueue, LocalQueue, ResourceFlavor, WorkloadPriorityClass, Cohort, Topology) are checked
  against the OpenAPI schema of the upstream CRDs (schemas/kueue-v1beta2.json, kueue v0.20.3), with JSON Schema.
* Core kinds (Namespace, Job, Pod...) are checked with the `kubernetes-validate` package (schemas of Kubernetes
  1.37), in strict mode: unknown fields are errors.
* Four rules that the CRD expresses in CEL (x-kubernetes-validations) cannot be run by a JSON Schema validator,
  so they are re-implemented below; one more rule (lendingLimit <= nominalQuota) is this lab's own sanity check.
  A real API server enforces the CEL rules itself: see the mini-control-plane lab, stage B.

Usage: validate_manifests.py [--schemas EXTRA.json ...] FILE_OR_DIR [...]    exit 0 if every document is valid, 1 otherwise.
"""
import json
import sys
from pathlib import Path

import jsonschema
import yaml

HERE = Path(__file__).resolve().parent
SCHEMAS: dict = {}


def load_schemas(*files):
    """Merge the {"kinds": {Kind: {apiVersion, scope, schema}}} files into the schemas used by validate_doc."""
    for f in files:
        SCHEMAS.update(json.loads(Path(f).read_text())["kinds"])


load_schemas(HERE / "schemas" / "kueue-v1beta2.json")


def load_docs(paths):
    files = []
    for p in map(Path, paths):
        files += sorted(p.glob("*.y*ml")) if p.is_dir() else [p]
    for f in files:
        for i, doc in enumerate(yaml.safe_load_all(f.read_text())):
            if doc:
                yield f, i, doc


def strictify(node):
    """Reject unknown fields like `kubectl apply --validate=strict` does (the API server would silently prune them)."""
    if isinstance(node, dict):
        out = {k: strictify(v) for k, v in node.items()}
        if "properties" in out and "additionalProperties" not in out and not out.get("x-kubernetes-preserve-unknown-fields"):
            out["additionalProperties"] = False
        return out
    if isinstance(node, list):
        return [strictify(v) for v in node]
    return node


def quantity(q):
    """Kubernetes quantity -> float, enough for cpu/memory/GPU comparisons (Ki..Ei, m, k..E)."""
    s = str(q)
    for suf, mul in (("Ki", 2**10), ("Mi", 2**20), ("Gi", 2**30), ("Ti", 2**40), ("Pi", 2**50), ("Ei", 2**60),
                     ("m", 1e-3), ("k", 1e3), ("M", 1e6), ("G", 1e9), ("T", 1e12), ("P", 1e15), ("E", 1e18)):
        if s.endswith(suf):
            return float(s[: -len(suf)]) * mul
    return float(s)


def cq_rules(doc):
    """Semantic rules for a ClusterQueue; returns a list of error strings."""
    errs, spec = [], doc.get("spec", {})
    cohort = spec.get("cohortName")
    for g, rg in enumerate(spec.get("resourceGroups", [])):
        covered = rg.get("coveredResources", [])
        for f, fl in enumerate(rg.get("flavors", [])):
            where = f"spec.resourceGroups[{g}].flavors[{f}]"
            if len(fl.get("resources", [])) != len(covered):                                   # CEL rule 4
                errs.append(f"{where}: flavors must have the same number of resources as coveredResources")
            if [r["name"] for r in fl.get("resources", [])] != covered:                       # lab rule (same order)
                errs.append(f"{where}: resources must be listed in the order of coveredResources")
            for r in fl.get("resources", []):
                nominal = quantity(r["nominalQuota"])
                if "borrowingLimit" in r and not cohort:                                      # CEL rule 1
                    errs.append(f"{where}: borrowingLimit must be nil when cohort is empty")
                if "lendingLimit" in r and not cohort:                                        # documented in the CRD text
                    errs.append(f"{where}: lendingLimit must be nil when cohort is empty")
                if "lendingLimit" in r and quantity(r["lendingLimit"]) > nominal:             # lab rule
                    errs.append(f"{where}: lendingLimit {r['lendingLimit']} exceeds nominalQuota {r['nominalQuota']} of {r['name']}")
    pre = spec.get("preemption", {})
    if pre.get("reclaimWithinCohort") == "Never" and pre.get("borrowWithinCohort", {}).get("policy", "Never") != "Never":
        errs.append("spec.preemption: reclaimWithinCohort=Never and borrowWithinCohort.policy!=Never")   # CEL rule 2
    ff = spec.get("flavorFungibility", {})
    if "preference" in ff and not (ff.get("whenCanBorrow") == "TryNextFlavor" and ff.get("whenCanPreempt") == "TryNextFlavor"):
        errs.append("spec.flavorFungibility: preference can only be set when both whenCanBorrow and whenCanPreempt are TryNextFlavor")  # CEL rule 3
    return errs


def validate_doc(doc):
    kind, api = doc.get("kind"), doc.get("apiVersion", "")
    if kind in SCHEMAS:
        entry = SCHEMAS[kind]
        if api != entry["apiVersion"]:
            return [f"apiVersion {api!r}, expected {entry['apiVersion']!r} (the only served version in the vendored CRD)"]
        errs = [f"{'.'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
                for e in jsonschema.Draft202012Validator(strictify(entry["schema"])).iter_errors(doc)]
        if errs:
            return errs                      # semantic rules assume a schema-valid document
        return cq_rules(doc) if kind == "ClusterQueue" else []
    import kubernetes_validate
    try:
        kubernetes_validate.validate(doc, "1.37", strict=True)
    except kubernetes_validate.ValidationError as e:
        return [f"{e.path_str if hasattr(e, 'path_str') else ''}: {e.message}".strip(": ")]
    except kubernetes_validate.SchemaNotFoundError as e:
        return [f"no schema for {api} {kind}: {e}"]
    return []


def main(argv):
    bad = total = 0
    while "--schemas" in argv:                       # extra CRD schema files, e.g. --schemas schemas/crds.json
        k = argv.index("--schemas")
        load_schemas(argv[k + 1])
        del argv[k:k + 2]
    for f, i, doc in load_docs(argv or ["manifests"]):
        total += 1
        errs = validate_doc(doc)
        label = f"{f.name}#{i} {doc.get('kind')}/{doc.get('metadata', {}).get('name')}"
        if errs:
            bad += 1
            print(f"INVALID {label}")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"ok      {label}")
    print(f"{total - bad}/{total} documents valid")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
