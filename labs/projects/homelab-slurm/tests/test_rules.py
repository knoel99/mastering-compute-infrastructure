import os
import re
import shutil
import subprocess

import pytest
import yaml

PROMTOOL = os.environ.get("PROMTOOL", "promtool")
REQUIRED = {"SlurmExporterStale", "SlurmNodeUnhealthy", "SlurmJobsPendingTooLong", "SlurmSchedulerStuck"}


def promtool(*args, cwd):
    return subprocess.run([PROMTOOL, *args], cwd=cwd, capture_output=True, text=True)


@pytest.fixture
def rules_dir(impl):
    return impl / "rules"


def load_alerts(rules_dir):
    doc = yaml.safe_load((rules_dir / "slurm.rules.yml").read_text())
    return {r["alert"]: r for g in doc["groups"] for r in g["rules"] if "alert" in r}


def test_rules_are_syntactically_valid(rules_dir):
    r = promtool("check", "rules", "slurm.rules.yml", cwd=rules_dir)
    assert r.returncode == 0, r.stdout + r.stderr


def test_required_alerts_exist_with_severity_and_summary(rules_dir):
    alerts = load_alerts(rules_dir)
    assert REQUIRED <= set(alerts), f"missing: {REQUIRED - set(alerts)}"
    for name in REQUIRED:
        assert alerts[name]["labels"]["severity"] in ("page", "ticket")
        assert alerts[name]["annotations"]["summary"]


def test_rule_unit_tests_pass(rules_dir):
    r = promtool("test", "rules", "slurm.rules.test.yml", cwd=rules_dir)
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_required_alert_has_a_firing_and_a_quiet_case(rules_dir):
    doc = yaml.safe_load((rules_dir / "slurm.rules.test.yml").read_text())
    seen = {}
    for t in doc["tests"]:
        for c in t.get("alert_rule_test", []):
            seen.setdefault(c["alertname"], set()).add(bool(c.get("exp_alerts")))
    for name in REQUIRED:
        assert seen.get(name) == {True, False}, f"{name} needs one firing and one quiet case, has {seen.get(name)}"


def mutants(text):
    """Yield (description, mutated rules text): a longer `for`, and the comparison operator inverted."""
    blocks = re.split(r"(?m)^(?=[ \t]*- alert:)", text)
    for i, block in enumerate(blocks[1:], 1):
        name = re.search(r"alert:\s*(\w+)", block).group(1)
        if re.search(r"(?m)^\s*for:\s*\S+", block):
            m = re.sub(r"(?m)^(\s*for:\s*)\S+", r"\g<1>90m", block)
            yield f"{name}: for -> 90m", "".join(blocks[:i] + [m] + blocks[i + 1:])
        expr = re.search(r"(?m)^\s*expr:.*$", block).group(0)
        flipped = re.sub(r"\s([<>])\s", lambda x: " < " if x.group(1) == ">" else " > ", expr, count=1)
        if flipped != expr:
            yield f"{name}: comparison inverted", "".join(blocks[:i] + [block.replace(expr, flipped)] + blocks[i + 1:])


def test_unit_tests_catch_mutated_rules(rules_dir, tmp_path):
    """A test suite that still passes on a broken rule proves nothing."""
    text = (rules_dir / "slurm.rules.yml").read_text()
    survivors = []
    n = 0
    for desc, mutated in mutants(text):
        n += 1
        work = tmp_path / f"m{n}"
        shutil.copytree(rules_dir, work)
        (work / "slurm.rules.yml").write_text(mutated)
        if promtool("test", "rules", "slurm.rules.test.yml", cwd=work).returncode == 0:
            survivors.append(desc)
    assert n >= 6, f"only {n} mutants generated"
    assert not survivors, f"unit tests did not notice: {survivors}"
