"""Policy lint for alert rules (lab 14.2): what `promtool check rules` does not check.

  1. every alert has severity page|ticket, a summary and a runbook_url that points to an existing file;
  2. every alert has a `for:` of at least 2m, except burn-rate alerts (label slo=burn), which must have none;
  3. every metric an expression reads is really exposed: by the lab 14.1 exporter, by dcgm-exporter (fixture),
     by the trainer contract, or defined by a recording rule in these files.
"""
import re
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
EXPORTER = HERE.parent / "gpu-metrics-exporter"
TRAINER = {"train_steps_total", "train_compute_seconds"}
BUILTIN = {"up"}
TOKEN = re.compile(r"\b(?:DCGM_[A-Z0-9_]+|train_[a-z_]+|slurm_[a-z_]+|gpu_node_[a-z_]+|[a-z_]+:[a-z0-9_:]+)\b")


def seconds(d):
    m = re.fullmatch(r"(\d+)([smh])", d)
    return int(m.group(1)) * {"s": 1, "m": 60, "h": 3600}[m.group(2)] if m else None


def exposed_names():
    out = subprocess.run([sys.executable, str(EXPORTER / "exporter.py"), "--fixtures", str(EXPORTER / "fixtures"), "--once"],
                         capture_output=True, text=True, check=True).stdout
    names = {m.group(1) for m in re.finditer(r"^([A-Za-z_:][A-Za-z0-9_:]*)[{ ]", out, re.M)}
    dcgm = {m.group(1) for m in re.finditer(r"^([A-Za-z_:][A-Za-z0-9_:]*)\{", (EXPORTER / "fixtures" / "dcgm_node.prom").read_text(), re.M)}
    return names | dcgm | TRAINER | BUILTIN


def load_rules(paths):
    rules = []
    for p in paths:
        for g in yaml.safe_load(Path(p).read_text())["groups"]:
            rules += g["rules"]
    return rules


def lint(paths):
    rules, errs = load_rules(paths), []
    defined = {r["record"] for r in rules if "record" in r}
    known = exposed_names() | defined
    for r in rules:
        if "alert" in r:
            name = r["alert"]
            sev = r.get("labels", {}).get("severity")
            if sev not in ("page", "ticket"):
                errs.append(f"{name}: severity must be page|ticket, got {sev!r}")
            for k in ("summary", "runbook_url"):
                if not r.get("annotations", {}).get(k):
                    errs.append(f"{name}: missing annotation {k}")
            rb = r.get("annotations", {}).get("runbook_url")
            if rb and not (HERE / rb).exists():
                errs.append(f"{name}: runbook {rb} does not exist")
            burn = r.get("labels", {}).get("slo") == "burn"
            f = seconds(r.get("for", "0s")) if "for" in r else None
            if burn and f:
                errs.append(f"{name}: a burn-rate alert must not use `for` (the short window is the filter)")
            if not burn and (f is None or f < 120):
                errs.append(f"{name}: needs `for` >= 2m (got {r.get('for')!r})")
        for tok in TOKEN.findall(r["expr"]):
            if tok not in known:
                errs.append(f"{r.get('alert') or r.get('record')}: unknown metric {tok!r}")
    return errs


if __name__ == "__main__":
    files = sys.argv[1:] or [str(HERE / "rules" / "platform.rules.yml"), str(HERE / "rules" / "slo.rules.yml")]
    problems = lint(files)
    print("\n".join(problems) if problems else f"lint ok: {len(load_rules(files))} rules")
    sys.exit(1 if problems else 0)
