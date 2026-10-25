#!/usr/bin/env python3
"""Deterministic market analysis: job postings (data/jobs/*.json) x curriculum coverage (data/coverage.json).

Computes, with no network and no model:
  * the sample: postings by region (job location), company origin, employer group, role family, seniority;
  * skill demand (share of postings citing a skill, and share requiring it), globally, per region, per company
    origin and per employer group, with and without inference-only roles;
  * distinctive skills of each region (share in the region minus share elsewhere, in points);
  * the coverage of each skill by the course (max depth over modules and projects, owners) and a gap list.
Only public postings (with a URL) whose quotes are mostly verified count (confidence != low).
    python3 tools/market_analysis.py            # writes data/market/analysis.json and prints a summary
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from validate_research import SKILLS  # noqa: E402

SKILL_FR = {
    "python": "Python", "systems-lang": "Langage système (Go, Rust, C++)", "linux-admin": "Administration Linux",
    "slurm": "Slurm", "kubernetes": "Kubernetes", "ray": "Ray", "multicloud-skypilot": "Multi-cloud (SkyPilot…)",
    "terraform-iac": "Terraform, infrastructure as code", "ansible-config": "Ansible, gestion de configuration",
    "containers": "Conteneurs", "pytorch-distributed": "Entraînement distribué (PyTorch, Megatron, DeepSpeed…)",
    "nccl-collectives": "Collectives (NCCL, RCCL, HCCL)", "cuda-gpu": "CUDA, programmation GPU",
    "infiniband-roce": "InfiniBand, RoCE", "parallel-fs-storage": "Systèmes de fichiers parallèles",
    "object-storage": "Stockage objet", "prometheus-grafana": "Prometheus, Grafana", "dcgm-gpu-monitoring": "Supervision GPU (DCGM)",
    "logging-tracing": "Journaux, traces", "experiment-tracking": "Suivi d'expériences",
    "checkpoint-fault-tolerance": "Checkpoint, tolérance aux pannes", "scheduler-design": "Conception d'ordonnanceur",
    "hyperscaler-cloud": "Cloud hyperscaler (AWS, GCP, Azure…)", "gpu-cloud-providers": "Clouds GPU spécialisés",
    "finops-cost": "FinOps, coûts", "procurement-vendor": "Achats, relation fournisseurs", "capacity-planning": "Planification de capacité",
    "security-compliance": "Sécurité, conformité", "sre-oncall": "Astreinte, fiabilité (SRE)", "leadership-mgmt": "Leadership, management",
    "hpc-experience": "Expérience HPC", "ml-training-experience": "Expérience d'entraînement ML", "rl-infra": "Infrastructure de RL",
    "data-pipelines": "Chaînes de données", "networking-general": "Réseau (général)", "bare-metal-provisioning": "Provisioning bare-metal",
    "ci-cd": "CI/CD, automatisation", "inference-serving": "Service d'inférence", "non-nvidia-accelerators": "Accélérateurs non NVIDIA (TPU, ROCm, Ascend…)",
    "perf-profiling": "Profilage, bancs d'essai", "datacenter-facilities": "Centre de données (énergie, refroidissement)",
    "distributed-systems": "Systèmes distribués", "virtualization": "Virtualisation (KVM, MIG, vGPU)",
    "hardware-health": "Santé matérielle (burn-in, diagnostics, RMA)",
}
REGION_FR = {"us": "États-Unis", "eu": "Europe", "cn": "Chine", "other": "Autres"}
GROUPS = {"ai-lab": "lab", "startup": "lab", "big-tech": "bigtech", "hyperscaler": "bigtech", "gpu-cloud": "cloud",
          "hpc-centre": "hpc", "vendor": "vendor", "other": "other"}
GROUP_FR = {"lab": "Laboratoires d'IA et start-ups", "bigtech": "Grands groupes et hyperscalers", "cloud": "Clouds GPU",
            "hpc": "Centres HPC", "vendor": "Constructeurs", "other": "Autres"}
ROLE_FR = {"training-platform": "Plateforme d'entraînement", "gpu-cluster-ops": "Clusters GPU", "hpc-ops": "Exploitation HPC",
           "inference-platform": "Plateforme d'inférence", "ml-systems-perf": "Performance des systèmes ML", "network": "Réseau",
           "storage": "Stockage", "capacity-finops": "Capacité, FinOps", "leadership": "Direction d'équipe", "other": "Autre"}


def short_company(name):
    """Display name: the part before any parenthesis ("CEA/DAM Île-de-France (TGCC…)" -> "CEA/DAM Île-de-France")."""
    return name.split(" (")[0].strip()


def load_postings():
    posts = []
    for f in sorted((ROOT / "data" / "jobs").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for p in d.get("postings", []):
            p["_unit"] = d.get("unit", f.stem)
            posts.append(p)
    # a posting counts only if it is public (a URL) and its quotes are mostly verified: the two anonymised
    # postings kept in data/jobs/jobs.json for the record have no URL and are left out of the analysis
    solid = [p for p in posts if p.get("url") and p.get("confidence") != "low"]
    return posts, solid


def levels(p):
    seen = {}
    for s in p["skills"]:
        seen[s["id"]] = max(seen.get(s["id"], 0), 2 if s["level"] == "required" else 1)
    return seen


def demand(posts):
    n = len(posts)
    req, anyc = Counter(), Counter()
    for p in posts:
        for sid, lvl in levels(p).items():
            anyc[sid] += 1
            req[sid] += lvl == 2
    return {"n": n, "skills": {s: {"any": anyc[s], "required": req[s],
                                   "share_any": round(anyc[s] / n, 3) if n else None,
                                   "share_required": round(req[s] / n, 3) if n else None} for s in SKILLS}}


def distinctive(posts, key, value, min_count=3):
    inside = [p for p in posts if p.get(key) == value]
    outside = [p for p in posts if p.get(key) != value]
    a, b = demand(inside), demand(outside)
    rows = []
    for s in SKILLS:
        if a["skills"][s]["any"] < min_count or not b["n"]:
            continue
        rows.append({"skill": s, "share_in": a["skills"][s]["share_any"], "share_out": b["skills"][s]["share_any"],
                     "delta_points": round(100 * (a["skills"][s]["share_any"] - b["skills"][s]["share_any"]), 1)})
    rows.sort(key=lambda r: -r["delta_points"])
    return rows


def coverage():
    f = ROOT / "data" / "coverage.json"
    if not f.exists():
        return None
    cov = json.loads(f.read_text(encoding="utf-8"))
    out = {}
    for s in SKILLS:
        owners = []
        best = 0
        for kind in ("modules", "projects"):
            for pid, sk in cov.get(kind, {}).items():
                d = sk.get(s, {}).get("depth", 0) if isinstance(sk.get(s), dict) else sk.get(s, 0)
                best = max(best, d)
                if d >= 2:
                    owners.append({"page": pid, "kind": kind[:-1], "depth": d})
        owners.sort(key=lambda o: -o["depth"])
        out[s] = {"max_depth": best, "owners": owners, "practised": any(o["depth"] == 3 for o in owners)}
    return out


def main():
    posts_all, posts = load_postings()
    core = [p for p in posts if p.get("role_family") != "inference-platform"]
    res = {"postings_total": len(posts_all), "postings_used": len(posts), "postings_core": len(core)}
    for key, name in (("region", "by_region"), ("company_origin", "by_origin"), ("role_family", "by_role"),
                      ("seniority", "by_seniority"), ("company_type", "by_company_type")):
        res[name] = dict(Counter(p.get(key, "?") for p in posts).most_common())
    res["by_group"] = dict(Counter(GROUPS.get(p["company_type"], "other") for p in posts).most_common())
    res["companies"] = dict(Counter(short_company(p["company"]) for p in posts).most_common())
    res["companies_by_region"] = {r: sorted({short_company(p["company"]) for p in posts if p.get("region") == r}) for r in REGION_FR}
    res["companies_by_origin"] = {r: sorted({short_company(p["company"]) for p in posts if p.get("company_origin") == r}) for r in REGION_FR}
    res["demand_all"] = demand(posts)
    res["demand_core"] = demand(core)
    res["demand_by_region"] = {r: demand([p for p in posts if p.get("region") == r]) for r in ("us", "eu", "cn")}
    res["demand_by_origin"] = {r: demand([p for p in posts if p.get("company_origin") == r]) for r in ("us", "eu", "cn")}
    res["demand_by_group"] = {g: demand([p for p in posts if GROUPS.get(p["company_type"], "other") == g]) for g in GROUP_FR}
    res["distinctive_by_region"] = {r: distinctive(posts, "region", r) for r in ("us", "eu", "cn")}
    yrs = defaultdict(list)
    for p in posts:
        if isinstance(p.get("years_required"), (int, float)):
            yrs[p.get("region", "?")].append(p["years_required"])
            yrs["all"].append(p["years_required"])
    res["years_required"] = {k: {"n": len(v), "median": sorted(v)[len(v) // 2], "min": min(v), "max": max(v)} for k, v in yrs.items()}
    # skills per posting
    nsk = sorted(len(levels(p)) for p in posts)
    res["skills_per_posting"] = {"median": nsk[len(nsk) // 2] if nsk else None, "min": nsk[0] if nsk else None, "max": nsk[-1] if nsk else None}
    # co-occurrence of the most frequent pairs (core postings)
    pairs = Counter()
    for p in core:
        ids = sorted(levels(p))
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                pairs[(a, b)] += 1
    res["top_pairs_core"] = [{"a": a, "b": b, "n": c} for (a, b), c in pairs.most_common(15)]
    cov = coverage()
    if cov:
        res["coverage"] = cov
        gaps = []
        for s in SKILLS:
            d = res["demand_all"]["skills"][s]
            c = cov[s]
            gaps.append({"skill": s, "share_any": d["share_any"], "share_required": d["share_required"],
                         "max_depth": c["max_depth"], "practised": c["practised"],
                         "gap_score": round(d["share_any"] * (3 - c["max_depth"]), 3)})
        gaps.sort(key=lambda g: -g["gap_score"])
        res["gaps"] = gaps
    out = ROOT / "data" / "market" / "analysis.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"postings {res['postings_total']} (used {res['postings_used']}, core {res['postings_core']})")
    print("by region:", res["by_region"], "| origin:", res["by_origin"], "| group:", res["by_group"])
    print("by role:", res["by_role"])
    top = sorted(SKILLS, key=lambda s: -res["demand_all"]["skills"][s]["any"])
    for s in top[:25]:
        row = [f"{res['demand_by_region'][r]['skills'][s]['share_any'] or 0:4.2f}" for r in ("us", "eu", "cn")]
        extra = f" depth {cov[s]['max_depth']}" if cov else ""
        print(f"  {s:26s} all {res['demand_all']['skills'][s]['share_any']:4.2f} req {res['demand_all']['skills'][s]['share_required']:4.2f} | us/eu/cn {' '.join(row)}{extra}")


if __name__ == "__main__":
    main()
