#!/usr/bin/env python3
"""Validate data/masters/*.json and data/jobs/*.json against specs/research-contract.md.

Usage (repository root):
    python3 tools/validate_research.py                 # every file
    python3 tools/validate_research.py data/masters/fr-a.json
Exit status 1 if any file has an error. Warnings never fail.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPICS = """openmp-threads mpi gpu-prog perf-model arch numerics simulation-apps parallel-algos
distributed-sys sysadmin scheduling interconnect storage-io containers-k8s cloud bigdata ml-dl
ml-systems hpc-software-eng energy quantum-emerging viz thesis-internship soft-skills resilience
observability-sre""".split()
SKILLS = """python systems-lang linux-admin slurm kubernetes ray multicloud-skypilot terraform-iac
ansible-config containers pytorch-distributed nccl-collectives cuda-gpu infiniband-roce
parallel-fs-storage object-storage prometheus-grafana dcgm-gpu-monitoring logging-tracing
experiment-tracking checkpoint-fault-tolerance scheduler-design hyperscaler-cloud gpu-cloud-providers
finops-cost procurement-vendor capacity-planning security-compliance sre-oncall leadership-mgmt
hpc-experience ml-training-experience rl-infra data-pipelines networking-general
bare-metal-provisioning ci-cd inference-serving non-nvidia-accelerators perf-profiling
datacenter-facilities distributed-systems virtualization hardware-health""".split()
FOCUS = {"hpc-core", "ml-systems", "cse", "cloud-distributed", "ops-sysadmin", "mixed"}
CONF = {"high", "medium", "low"}
REGIONS = {"us", "eu", "cn", "other"}
ROLE_FAMILIES = {"training-platform", "gpu-cluster-ops", "hpc-ops", "inference-platform", "ml-systems-perf",
                 "network", "storage", "capacity-finops", "leadership", "other"}
COMPANY_TYPES = {"ai-lab", "gpu-cloud", "hyperscaler", "big-tech", "hpc-centre", "vendor", "startup", "other"}
URL = re.compile(r"^https?://[^\s]+$")


def words(s):
    return len(str(s).split())


def check_evidence(ev, where, errs, warns):
    if not isinstance(ev, list) or not ev:
        errs.append(f"{where}: evidence missing or empty")
        return
    for i, e in enumerate(ev):
        w = f"{where}.evidence[{i}]"
        if not isinstance(e, dict):
            errs.append(f"{w}: not an object")
            continue
        src = e.get("source", "web")
        if src not in ("web", "memory"):
            errs.append(f"{w}: source must be web|memory")
        if src == "web":
            if not URL.match(str(e.get("url", ""))):
                errs.append(f"{w}: bad url")
            q = e.get("quote", "")
            if not q:
                errs.append(f"{w}: empty quote")
            elif words(q) > 40:
                warns.append(f"{w}: quote longer than 25 words ({words(q)})")
        if not e.get("claim"):
            errs.append(f"{w}: empty claim")


def check_masters(d, errs, warns):
    for k in ("unit", "region", "retrieved_on", "programmes", "ecosystem", "blocked_sources", "verification"):
        if k not in d:
            errs.append(f"missing top-level key {k}")
    seen = set()
    for p in d.get("programmes", []):
        pid = p.get("id", "?")
        w = f"programme {pid}"
        if pid in seen:
            errs.append(f"{w}: duplicate id")
        seen.add(pid)
        for k in ("country", "institution", "programme_name", "degree", "urls", "duration", "credits",
                  "language", "delivery", "entry_requirements", "focus", "structure_summary",
                  "core_courses", "electives", "capstone", "machines_access", "industry_links",
                  "topic_coverage", "evidence", "confidence"):
            if k not in p:
                errs.append(f"{w}: missing {k}")
        if p.get("focus") not in FOCUS:
            errs.append(f"{w}: focus {p.get('focus')!r} not in {sorted(FOCUS)}")
        if p.get("confidence") not in CONF:
            errs.append(f"{w}: confidence invalid")
        for u in p.get("urls", []):
            if not URL.match(u):
                errs.append(f"{w}: bad url {u!r}")
        tc = p.get("topic_coverage", {})
        missing = [t for t in TOPICS if t not in tc]
        extra = [t for t in tc if t not in TOPICS]
        if missing:
            errs.append(f"{w}: topic_coverage missing {missing}")
        if extra:
            errs.append(f"{w}: topic_coverage unknown {extra}")
        for t, v in tc.items():
            if v not in (0, 1, 2, None):
                errs.append(f"{w}: topic_coverage[{t}]={v!r}")
        for c in p.get("core_courses", []) + p.get("electives", []):
            for t in c.get("topics", []):
                if t not in TOPICS:
                    errs.append(f"{w}: course {c.get('name')!r} unknown topic {t}")
        check_evidence(p.get("evidence"), w, errs, warns)
        if p.get("confidence") == "high" and any(e.get("source") == "memory" for e in p.get("evidence", [])):
            errs.append(f"{w}: confidence high but some evidence comes from memory")
        known = [v for v in tc.values() if v is not None]
        if len(known) == 0 and p.get("confidence") != "low":
            warns.append(f"{w}: no topic known but confidence {p.get('confidence')}")
    for e in d.get("ecosystem", []):
        w = f"ecosystem {e.get('id', '?')}"
        for k in ("id", "kind", "name", "url", "why_relevant", "evidence"):
            if k not in e:
                errs.append(f"{w}: missing {k}")
        if "url" in e and not URL.match(e["url"]):
            errs.append(f"{w}: bad url")
        if "evidence" in e:
            check_evidence(e["evidence"], w, errs, warns)
    v = d.get("verification", {})
    if v.get("status") not in ("unverified", "verified"):
        errs.append("verification.status must be unverified|verified")


def check_jobs(d, errs, warns):
    for k in ("unit", "retrieved_on", "postings", "blocked_sources"):
        if k not in d:
            errs.append(f"missing top-level key {k}")
    seen = set()
    for p in d.get("postings", []):
        pid = p.get("id", "?")
        w = f"posting {pid}"
        if pid in seen:
            errs.append(f"{w}: duplicate id")
        seen.add(pid)
        for k in ("company", "company_type", "title", "location", "seniority", "skills", "responsibilities",
                  "region", "company_origin", "role_family"):
            if k not in p:
                errs.append(f"{w}: missing {k}")
        if p.get("company_type") not in COMPANY_TYPES:
            errs.append(f"{w}: company_type {p.get('company_type')!r} not in {sorted(COMPANY_TYPES)}")
        for k in ("region", "company_origin"):
            if k in p and p[k] not in REGIONS:
                errs.append(f"{w}: {k} {p[k]!r} not in {sorted(REGIONS)}")
        if "role_family" in p and p["role_family"] not in ROLE_FAMILIES:
            errs.append(f"{w}: role_family {p['role_family']!r} not in {sorted(ROLE_FAMILIES)}")
        if p.get("source_url") and not URL.match(str(p["source_url"])):
            errs.append(f"{w}: bad source_url")
        withheld = str(p.get("company", "")).startswith("startup robotique")
        if not withheld and not URL.match(str(p.get("url", ""))):
            errs.append(f"{w}: bad or missing url")
        if withheld and p.get("url"):
            errs.append(f"{w}: withheld posting must have no url")
        for s in p.get("skills", []):
            if s.get("id") not in SKILLS:
                errs.append(f"{w}: unknown skill {s.get('id')!r}")
            if s.get("level") not in ("required", "bonus"):
                errs.append(f"{w}: skill level invalid for {s.get('id')}")
            if not s.get("quote"):
                errs.append(f"{w}: skill {s.get('id')} has no quote")
            elif words(s["quote"]) > 40 or len(s["quote"]) > 300:
                warns.append(f"{w}: skill {s.get('id')} quote too long")
        if not p.get("skills"):
            errs.append(f"{w}: no skills extracted")


def main(argv):
    files = [Path(a) for a in argv] or sorted((ROOT / "data").glob("masters/*.json")) + sorted((ROOT / "data").glob("jobs/*.json"))
    files = [f for f in files if f.name != "synthesis.json"]
    bad = 0
    for f in files:
        errs, warns = [], []
        try:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception as ex:  # noqa: BLE001
            print(f"{f}: INVALID JSON — {ex}")
            bad += 1
            continue
        (check_jobs if "jobs" in str(f) else check_masters)(d, errs, warns)
        print(f"{f}: {len(errs)} error(s), {len(warns)} warning(s)")
        for m in errs:
            print("  ERROR", m)
        for m in warns[:10]:
            print("  warn ", m)
        bad += bool(errs)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
