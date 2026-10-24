import json
import os
import re
import subprocess

import dashboard
import exporter

PROMTOOL = os.environ.get("PROMTOOL", "promtool")
KNOWN = {m[0] for m in exporter.METRICS} | {"slurm_job_gpu_allocated"}


def exprs():
    return [(p["title"], t["expr"]) for p in dashboard.build()["panels"] for t in p["targets"]]


def test_structure():
    d = json.loads(json.dumps(dashboard.build()))
    assert d["uid"] and d["title"] and len(d["panels"]) >= 5
    ids = [p["id"] for p in d["panels"]]
    assert len(set(ids)) == len(ids)
    assert all(p["targets"] and p["gridPos"] for p in d["panels"])


def test_every_expression_is_valid_promql(tmp_path):
    rules = {"groups": [{"name": "dash", "rules": [{"record": f"dash:panel{i}", "expr": e}
                                                   for i, (_, e) in enumerate(exprs())]}]}
    f = tmp_path / "dash.rules.yml"
    f.write_text(json.dumps(rules))  # JSON is valid YAML
    r = subprocess.run([PROMTOOL, "check", "rules", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_panels_only_use_metrics_the_exporter_exposes():
    for title, expr in exprs():
        used = set(re.findall(r"\b(?:DCGM_[A-Z0-9_]+|slurm_[a-z_]+)\b", expr))
        assert used and used <= KNOWN, (title, used - KNOWN)
        if "by (job)" in expr:  # a per-job panel needs the allocation join, as the alert rules do
            assert "slurm_job_gpu_allocated" in expr, title
