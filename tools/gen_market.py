#!/usr/bin/env python3
"""Generate market/index.md from data/market/analysis.json and the hand-written narrative market/_notes/index.md.

The narrative holds placeholders that this script replaces with tables computed from the data, so that every
number on the page comes from data/jobs/*.json and data/coverage.json:
  {{N_POST}} {{N_US}} {{N_EU}} {{N_CN}} {{N_COMPANIES}} {{N_QUOTES}} {{N_QUOTES_OK}}
  {{SAMPLE_TABLE}} {{COMPANIES}} {{ROLE_TABLE}} {{TOP_BARS}} {{REGION_TABLE}} {{DISTINCTIVE}}
  {{GROUP_TABLE}} {{COVERAGE_TABLE}} {{GAPS_TABLE}} {{YEARS}}
and {{SHARE:<skill>}} / {{SHARE:<skill>:<region>}} / {{COUNT:<skill>}} / {{COUNT:<skill>:<region>}} inline.
    python3 tools/market_analysis.py && python3 tools/gen_market.py && python3 tools/build.py market
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from market_analysis import SKILL_FR, REGION_FR, GROUP_FR, ROLE_FR, GROUPS  # noqa: E402
from validate_research import SKILLS  # noqa: E402

C = json.loads((ROOT / "data" / "curriculum.json").read_text(encoding="utf-8"))
NUM = {m["id"]: m["number"] for m in C["modules"]}
PNUM = {p["id"]: p["number"] for p in C["projects"]}
DEPTH_FR = {0: "absent", 1: "mentionné", 2: "enseigné", 3: "pratiqué"}
REGIONS = ("us", "eu", "cn")


def pct(x):
    return "—" if x is None else f"{round(100 * x)} %"


def frac(a, n):
    return f"{a} sur {n}"


def sample_table(A, posts):
    groups = list(GROUP_FR)
    head = "| Zone du poste | " + " | ".join(GROUP_FR[g] for g in groups) + " | Total |"
    sep = "|---|" + "---|" * (len(groups) + 1)
    rows = [head, sep]
    for r in REGIONS:
        sub = [p for p in posts if p.get("region") == r]
        cells = [str(sum(GROUPS.get(p["company_type"], "other") == g for p in sub)) for g in groups]
        rows.append(f"| {REGION_FR[r]} | " + " | ".join(cells) + f" | **{len(sub)}** |")
    other = [p for p in posts if p.get("region") not in REGIONS]
    if other:
        cells = [str(sum(GROUPS.get(p["company_type"], "other") == g for p in other)) for g in groups]
        rows.append("| Autres | " + " | ".join(cells) + f" | **{len(other)}** |")
    tot = [str(sum(GROUPS.get(p["company_type"], "other") == g for p in posts)) for g in groups]
    rows.append("| **Total** | " + " | ".join(tot) + f" | **{len(posts)}** |")
    # drop empty columns
    keep = [i for i, g in enumerate(groups) if any(GROUPS.get(p["company_type"], "other") == g for p in posts)]
    out = []
    for line in rows:
        cells = line.strip("|").split("|")
        if line.startswith("|---"):
            out.append("|---|" + "---|" * (len(keep) + 1))
            continue
        out.append("|" + cells[0] + "|" + "|".join(cells[1 + i] for i in keep) + "|" + cells[-1] + "|")
    return "\n".join(out)


def companies(A):
    out = []
    for r in REGIONS:
        cs = A["companies_by_region"].get(r, [])
        if cs:
            out.append(f"-   **{REGION_FR[r]}** ({len(cs)}) : " + ", ".join(cs) + ".")
    return "\n".join(out)


def role_table(A):
    n = A["postings_used"]
    rows = ["| Famille de poste | Offres | Part |", "|---|---|---|"]
    for k, v in A["by_role"].items():
        rows.append(f"| {ROLE_FR.get(k, k)} | {v} | {pct(v / n)} |")
    return "\n".join(rows)


def top_bars(A, k=24):
    d = A["demand_all"]
    n = d["n"]
    top = sorted(SKILLS, key=lambda s: (-d["skills"][s]["any"], -d["skills"][s]["required"]))[:k]
    out = ['<div class="bars" role="list">']
    for s in top:
        x = d["skills"][s]
        out.append(f'<div class="bar" role="listitem"><span class="blab">{SKILL_FR[s]}</span><span class="track">'
                   f'<span class="fill two" style="width:{100 * x["share_required"]:.0f}%;float:left"></span>'
                   f'<span class="fill" style="width:{100 * (x["share_any"] - x["share_required"]):.0f}%;float:left"></span></span>'
                   f'<span class="val">{x["any"]}/{n}</span></div>')
    out.append("</div>")
    return "\n".join(out)


def region_table(A, k=30):
    d = A["demand_all"]
    top = sorted(SKILLS, key=lambda s: -d["skills"][s]["any"])[:k]
    ns = {r: A["demand_by_region"][r]["n"] for r in REGIONS}
    head = "| Compétence | Toutes (" + str(d["n"]) + ") | " + " | ".join(f"{REGION_FR[r]} ({ns[r]})" for r in REGIONS) + " |"
    rows = [head, "|---|---|---|---|---|"]
    for s in top:
        cells = [pct(A["demand_by_region"][r]["skills"][s]["share_any"]) for r in REGIONS]
        rows.append(f"| {SKILL_FR[s]} | {pct(d['skills'][s]['share_any'])} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def distinctive(A, k=6):
    out = []
    for r in REGIONS:
        rows = [x for x in A["distinctive_by_region"][r] if x["delta_points"] >= 10][:k]
        if not rows:
            continue
        items = "; ".join(f"{SKILL_FR[x['skill']]} ({pct(x['share_in'])} contre {pct(x['share_out'])} ailleurs)" for x in rows)
        out.append(f"-   **{REGION_FR[r]}** : {items}.")
    return "\n".join(out)


def group_table(A, k=22):
    d = A["demand_all"]
    groups = [g for g in GROUP_FR if A["demand_by_group"][g]["n"] >= 3]
    top = sorted(SKILLS, key=lambda s: -d["skills"][s]["any"])[:k]
    head = "| Compétence | " + " | ".join(f"{GROUP_FR[g]} ({A['demand_by_group'][g]['n']})" for g in groups) + " |"
    rows = [head, "|---|" + "---|" * len(groups)]
    for s in top:
        rows.append(f"| {SKILL_FR[s]} | " + " | ".join(pct(A["demand_by_group"][g]["skills"][s]["share_any"]) for g in groups) + " |")
    return "\n".join(rows)


def owner_links(c):
    links = []
    for o in c["owners"][:4]:
        if o["kind"] == "module":
            links.append(f"[{NUM[o['page']]}](../courses/{o['page']}/index.html)")
        else:
            links.append(f"[P{PNUM[o['page']]}](../projects/{o['page']}/index.html)")
    return ", ".join(links) or "—"


def coverage_table(A):
    d = A["demand_all"]
    cov = A.get("coverage")
    if not cov:
        return "*(couverture non calculée)*"
    rows = ["| Compétence | Offres qui la citent | dont exigée | Profondeur dans le parcours | Modules et projets |", "|---|---|---|---|---|"]
    for s in sorted(SKILLS, key=lambda s: -d["skills"][s]["any"]):
        x = d["skills"][s]
        c = cov[s]
        rows.append(f"| {SKILL_FR[s]} | {pct(x['share_any'])} | {pct(x['share_required'])} | {DEPTH_FR[c['max_depth']]} | {owner_links(c)} |")
    return "\n".join(rows)


def gaps_table(A, k=12):
    gaps = [g for g in A.get("gaps", []) if g["gap_score"] > 0][:k]
    rows = ["| Compétence | Offres qui la citent | Profondeur | Indice d'écart |", "|---|---|---|---|"]
    for g in gaps:
        rows.append(f"| {SKILL_FR[g['skill']]} | {pct(g['share_any'])} | {DEPTH_FR[g['max_depth']]} | {g['gap_score']:.2f} |")
    return "\n".join(rows)


def years(A):
    y = A["years_required"]
    parts = []
    for r in ("all",) + REGIONS:
        if r in y:
            lab = "toutes zones" if r == "all" else REGION_FR[r]
            parts.append(f"{lab} : médiane {y[r]['median']} ans ({y[r]['min']} à {y[r]['max']}, sur {y[r]['n']} offres qui le disent)")
    return " ; ".join(parts) + "."


def quotes():
    tot = ok = 0
    for f in sorted((ROOT / "data" / "jobs").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for p in d.get("postings", []):
            for e in p.get("evidence", []):
                tot += 1
                ok += bool(e.get("verified"))
    return tot, ok


def inline(text, A):
    def share(m):
        s, r = m.group(2), m.group(3)
        d = A["demand_by_region"][r] if r else A["demand_all"]
        if s not in d["skills"]:
            raise SystemExit(f"unknown skill in placeholder: {s}")
        x = d["skills"][s]
        return pct(x["share_any"]) if m.group(1) == "SHARE" else frac(x["any"], d["n"])
    return re.sub(r"\{\{(SHARE|COUNT):([a-z-]+)(?::([a-z]+))?\}\}", share, text)


def main():
    A = json.loads((ROOT / "data" / "market" / "analysis.json").read_text(encoding="utf-8"))
    posts = []
    for f in sorted((ROOT / "data" / "jobs").glob("*.json")):
        posts += [p for p in json.loads(f.read_text(encoding="utf-8")).get("postings", []) if p.get("url") and p.get("confidence") != "low"]   # same rule as market_analysis
    note = (ROOT / "market" / "_notes" / "index.md").read_text(encoding="utf-8")
    tq, okq = quotes()
    rep = {
        "{{N_POST}}": str(A["postings_used"]), "{{N_US}}": str(A["by_region"].get("us", 0)), "{{N_EU}}": str(A["by_region"].get("eu", 0)),
        "{{N_CN}}": str(A["by_region"].get("cn", 0)), "{{N_COMPANIES}}": str(len(A["companies"])),
        "{{N_QUOTES}}": str(tq), "{{N_QUOTES_OK}}": str(okq), "{{N_CORE}}": str(A["postings_core"]),
        "{{SAMPLE_TABLE}}": sample_table(A, posts), "{{COMPANIES}}": companies(A), "{{ROLE_TABLE}}": role_table(A),
        "{{TOP_BARS}}": top_bars(A), "{{REGION_TABLE}}": region_table(A), "{{DISTINCTIVE}}": distinctive(A),
        "{{GROUP_TABLE}}": group_table(A), "{{COVERAGE_TABLE}}": coverage_table(A), "{{GAPS_TABLE}}": gaps_table(A),
        "{{YEARS}}": years(A),
    }
    for k, v in rep.items():
        note = note.replace(k, v)
    note = inline(note, A)
    left = re.findall(r"\{\{[^}]+\}\}", note)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    (ROOT / "market" / "index.md").write_text(note, encoding="utf-8")
    print(f"generated market/index.md ({A['postings_used']} postings, {tq} quotes, {okq} verified)")


if __name__ == "__main__":
    main()
