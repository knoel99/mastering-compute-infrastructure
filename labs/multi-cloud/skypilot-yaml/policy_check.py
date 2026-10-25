#!/usr/bin/env python3
"""Governance lint for SkyPilot task files. It reads YAML only: no cloud, no credentials, no SkyPilot import.

Rules (E = error, W = warning). The point is that the rule set is CODE a team can review and extend, not a wiki page:
  E1 missing-label        labels must contain team, project and owner (cost allocation, clean-up of orphans)
  E2 spot-no-recovery     use_spot without resources.job_recovery
  E3 spot-no-checkpoint   use_spot without a WRITABLE bucket mount (MOUNT or MOUNT_CACHED, type not read-only)
  E4 secret-in-envs       an envs key that looks like a credential holds a value (use `secrets:`)
  E5 cluster-no-autostop  --kind cluster without autostop.idle_minutes <= 60 and autostop.down: true
  W1 no-cost-cap          no resources.max_hourly_cost
  W2 single-location      use_spot with fewer than two candidate locations (no failover target)
  W3 cross-cloud-mount    a bucket of one hyperscaler (s3://, gs://) mounted from candidates on another provider
  E6 location-not-allowed with --allow-prefix: a cloud candidate (aws/..., gcp/...) outside the allowed prefixes
  W4 location-unverifiable with --allow-prefix: a k8s/ or slurm candidate, whose real location a name does not prove
Usage: policy_check.py FILE.yaml [--kind managed|cluster] [--allow-prefix aws/eu- --allow-prefix gcp/europe-]
Exit status 1 if there is at least one error.
"""
import argparse
import re
import sys

import yaml

REQUIRED_LABELS = ("team", "project", "owner")
SECRETISH = re.compile(r"(TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY)$", re.I)
SCHEME_PROVIDER = {"s3": "aws", "gs": "gcp"}
MOUNT_MODES = ("MOUNT", "MOUNT_CACHED")
READ_ONLY_TYPES = ("DATASET_RO", "MODEL_CHECKPOINT_RO")


def candidates(res):
    out = []
    for key in ("any_of", "ordered"):
        for c in res.get(key) or []:
            if isinstance(c, dict) and c.get("infra"):
                out.append(str(c["infra"]))
    if res.get("infra"):
        out.append(str(res["infra"]))
    return out


def bucket_mounts(task):
    """(path, scheme, mode, type) for every file_mounts entry that is a bucket."""
    found = []
    for path, spec in (task.get("file_mounts") or {}).items():
        if isinstance(spec, dict):
            src = str(spec.get("source") or "")
            m = re.match(r"([a-z0-9]+)://", src)
            if m:
                found.append((path, m.group(1), spec.get("mode", "MOUNT"), spec.get("type")))
            elif spec.get("name"):
                found.append((path, "", spec.get("mode", "MOUNT"), spec.get("type")))
    return found


def check(task, kind="managed", allow=None):
    """Return a list of (code, level, message) for a parsed task dict. `allow`: allowed location prefixes, or None."""
    res = task.get("resources") or {}
    out = []
    labels = res.get("labels") or {}
    for need in REQUIRED_LABELS:
        if not labels.get(need):
            out.append(("E1", "error", f"label {need!r} is missing"))
    spot = bool(res.get("use_spot"))
    mounts = bucket_mounts(task)
    if spot and not res.get("job_recovery"):
        out.append(("E2", "error", "use_spot without job_recovery"))
    if spot and not any(mode in MOUNT_MODES and typ not in READ_ONLY_TYPES for _, _, mode, typ in mounts):
        out.append(("E3", "error", "use_spot without a writable mounted bucket to resume from"))
    for k, v in (task.get("envs") or {}).items():
        if SECRETISH.search(str(k)) and str(v).strip():
            out.append(("E4", "error", f"envs.{k} looks like a credential: use secrets:"))
    if kind == "cluster":
        a = res.get("autostop") or {}
        idle = a.get("idle_minutes") if isinstance(a, dict) else None
        if not (isinstance(idle, (int, float)) and idle <= 60 and a.get("down") is True):
            out.append(("E5", "error", "cluster needs autostop.idle_minutes <= 60 and autostop.down: true"))
    if res.get("max_hourly_cost") is None:
        out.append(("W1", "warning", "no max_hourly_cost"))
    cands = candidates(res)
    if spot and len(set(cands)) < 2:
        out.append(("W2", "warning", "fewer than two candidate locations: nowhere to fail over"))
    if allow:
        for c in cands:
            if c.split("/")[0] in ("k8s", "slurm"):
                out.append(("W4", "warning", f"{c}: a context name does not prove where the cluster runs"))
            elif not any(c.startswith(pref) for pref in allow):
                out.append(("E6", "error", f"{c} is outside the allowed locations {list(allow)}"))
    providers = {c.split("/")[0] for c in cands}
    for path, scheme, _, _ in mounts:
        home = SCHEME_PROVIDER.get(scheme)
        if home and (providers - {home}):
            out.append(("W3", "warning", f"{path}: {scheme}:// bucket read from {sorted(providers - {home})}: egress"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--kind", choices=["managed", "cluster"], default="managed")
    ap.add_argument("--allow-prefix", action="append", default=None, help="allowed location prefix, repeatable")
    args = ap.parse_args(argv)
    with open(args.file, encoding="utf-8") as fh:
        task = yaml.safe_load(fh)
    findings = check(task, args.kind, args.allow_prefix)
    for code, level, msg in findings:
        print(f"{args.file}: {code} {level}: {msg}")
    errors = sum(1 for _, level, _ in findings if level == "error")
    print(f"{args.file}: {errors} error(s), {len(findings) - errors} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
