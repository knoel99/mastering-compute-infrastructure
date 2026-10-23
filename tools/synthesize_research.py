#!/usr/bin/env python3
"""Deterministic synthesis of data/masters/*.json, data/jobs/*.json -> data/masters/synthesis.json.

Computes (no network, no model):
  * programme x topic matrix, share of programmes covering each topic, over programmes with a KNOWN value
    (null = unknown is excluded from the denominator, which is reported), globally, per region and per focus;
  * job-skill frequencies (required / bonus), per company type, seniority and years_required;
  * supply (masters) versus demand (postings) for mapped skill/topic pairs.
Only programmes/postings whose evidence is mostly verified count as "solid" (confidence != low).
    python3 tools/synthesize_research.py [--include-low]
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from validate_research import TOPICS, SKILLS  # noqa: E402

SKILL_TO_TOPIC = {
    "slurm": "scheduling", "kubernetes": "containers-k8s", "containers": "containers-k8s",
    "infiniband-roce": "interconnect", "networking-general": "interconnect",
    "parallel-fs-storage": "storage-io", "object-storage": "storage-io",
    "checkpoint-fault-tolerance": "resilience", "prometheus-grafana": "observability-sre",
    "dcgm-gpu-monitoring": "observability-sre", "logging-tracing": "observability-sre", "sre-oncall": "observability-sre",
    "pytorch-distributed": "ml-systems", "nccl-collectives": "ml-systems", "ml-training-experience": "ml-systems",
    "cuda-gpu": "gpu-prog", "linux-admin": "sysadmin", "bare-metal-provisioning": "sysadmin", "ansible-config": "sysadmin",
    "hyperscaler-cloud": "cloud", "gpu-cloud-providers": "cloud", "multicloud-skypilot": "cloud",
    "finops-cost": "cloud", "capacity-planning": "cloud", "procurement-vendor": "cloud",
    "hpc-experience": "mpi", "scheduler-design": "scheduling", "ci-cd": "hpc-software-eng",
    "data-pipelines": "bigdata", "rl-infra": "ml-systems", "terraform-iac": "cloud", "ray": "distributed-sys",
}


def load():
    include_low = "--include-low" in sys.argv
    progs, posts, resources = [], [], []
    for f in sorted((ROOT / "data" / "masters").glob("*.json")):
        if f.name == "synthesis.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for p in d.get("programmes", []):
            p["_region"] = d.get("region", "?")
            p["_unit"] = d.get("unit", f.stem)
            progs.append(p)
    for f in sorted((ROOT / "data" / "jobs").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        posts += d.get("postings", [])
    for f in sorted((ROOT / "data" / "resources").glob("*.json")):
        resources += json.loads(f.read_text(encoding="utf-8")).get("items", [])
    if not include_low:
        progs_solid = [p for p in progs if p.get("confidence") != "low"]
    else:
        progs_solid = progs
    return progs, progs_solid, posts, resources


def coverage(progs):
    out = {}
    for t in TOPICS:
        vals = [p["topic_coverage"].get(t) for p in progs]
        known = [v for v in vals if v is not None]
        out[t] = {"known": len(known), "unknown": len(vals) - len(known),
                  "share_ge1": round(sum(v >= 1 for v in known) / len(known), 2) if known else None,
                  "share_eq2": round(sum(v == 2 for v in known) / len(known), 2) if known else None}
    return out


def main():
    progs_all, progs, posts, resources = load()
    res = {"programmes_total": len(progs_all), "programmes_solid": len(progs),
           "postings_total": len(posts), "resources_total": len(resources)}
    res["programmes_by_region"] = dict(Counter(p["_region"] for p in progs))
    res["programmes_by_focus"] = dict(Counter(p["focus"] for p in progs))
    res["programmes_by_country"] = dict(Counter(p["country"] for p in progs))
    res["coverage_global"] = coverage(progs)
    res["coverage_by_region"] = {r: coverage([p for p in progs if p["_region"] == r]) for r in sorted({p["_region"] for p in progs})}
    res["coverage_by_focus"] = {f: coverage([p for p in progs if p["focus"] == f]) for f in sorted({p["focus"] for p in progs})}
    # jobs
    req, bonus, by_type = Counter(), Counter(), defaultdict(Counter)
    for p in posts:
        seen = {}
        for s in p["skills"]:
            seen[s["id"]] = max(seen.get(s["id"], 0), 2 if s["level"] == "required" else 1)
        for sid, lvl in seen.items():
            (req if lvl == 2 else bonus)[sid] += 1
            by_type[p["company_type"]][sid] += 1
    n = len(posts) or 1
    res["skills"] = {s: {"required": req[s], "bonus": bonus[s], "share_any": round((req[s] + bonus[s]) / n, 2),
                         "share_required": round(req[s] / n, 2)} for s in SKILLS}
    res["postings_by_type"] = dict(Counter(p["company_type"] for p in posts))
    res["postings_by_seniority"] = dict(Counter(p["seniority"] for p in posts))
    yrs = sorted(p["years_required"] for p in posts if isinstance(p.get("years_required"), (int, float)))
    res["years_required"] = {"n": len(yrs), "values": yrs, "median": yrs[len(yrs) // 2] if yrs else None}
    res["skills_by_company_type"] = {t: dict(c.most_common(12)) for t, c in by_type.items()}
    # supply vs demand
    cov = res["coverage_global"]
    sd = []
    for skill, topic in sorted(SKILL_TO_TOPIC.items()):
        sd.append({"skill": skill, "topic": topic, "demand_share_any": res["skills"][skill]["share_any"],
                   "demand_share_required": res["skills"][skill]["share_required"],
                   "supply_share_ge1": cov[topic]["share_ge1"], "supply_share_eq2": cov[topic]["share_eq2"],
                   "supply_known": cov[topic]["known"]})
    res["supply_vs_demand"] = sd
    (ROOT / "data" / "masters" / "synthesis.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"programmes {len(progs_all)} (solid {len(progs)}), postings {len(posts)}, resources {len(resources)}")
    print("by region:", res["programmes_by_region"], "| by focus:", res["programmes_by_focus"])
    top = sorted(((t, c["share_ge1"], c["share_eq2"], c["known"]) for t, c in cov.items() if c["share_ge1"] is not None), key=lambda x: -x[1])
    print("topic coverage (>=1 / dedicated(2) / known):")
    for t, a, b, k in top[:30]:
        print(f"  {t:20s} {a:4.2f} {b:4.2f} n={k}")


if __name__ == "__main__":
    main()
