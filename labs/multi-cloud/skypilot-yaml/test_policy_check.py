import copy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import policy_check as pc

HERE = Path(__file__).resolve().parent
JOB = yaml.safe_load((HERE / "job.yaml").read_text(encoding="utf-8"))
DEV = yaml.safe_load((HERE / "dev-cluster.yaml").read_text(encoding="utf-8"))
BAD = yaml.safe_load((HERE / "bad-job.yaml").read_text(encoding="utf-8"))
EU = yaml.safe_load((HERE / "job-eu.yaml").read_text(encoding="utf-8"))


def codes(task, kind="managed"):
    return {c for c, _, _ in pc.check(task, kind)}


def test_shipped_files_have_no_error():
    assert not [f for f in pc.check(JOB) if f[1] == "error"]
    assert not [f for f in pc.check(DEV, "cluster") if f[1] == "error"]


def test_job_has_no_warning_either():
    assert pc.check(JOB) == []


@pytest.mark.parametrize("label", ["team", "project", "owner"])
def test_missing_label_is_an_error(label):
    t = copy.deepcopy(JOB)
    del t["resources"]["labels"][label]
    assert "E1" in codes(t)


def test_spot_without_recovery_or_checkpoint():
    t = copy.deepcopy(JOB)
    del t["resources"]["job_recovery"]
    assert "E2" in codes(t)
    t = copy.deepcopy(JOB)
    t["file_mounts"]["/checkpoint"]["mode"] = "COPY"
    assert "E3" in codes(t)
    t = copy.deepcopy(JOB)
    t["file_mounts"] = {}
    assert "E3" in codes(t)


def test_on_demand_job_needs_neither_recovery_nor_checkpoint():
    t = copy.deepcopy(JOB)
    t["resources"]["use_spot"] = False
    del t["resources"]["job_recovery"]
    t["file_mounts"] = {}
    assert not ({"E2", "E3"} & codes(t))


def test_secret_in_envs():
    t = copy.deepcopy(JOB)
    t["envs"]["HF_TOKEN"] = "hf_abc"
    assert "E4" in codes(t)
    t["envs"]["HF_TOKEN"] = ""
    assert "E4" not in codes(t)


def test_cluster_autostop_rules():
    t = copy.deepcopy(DEV)
    assert "E5" not in codes(t, "cluster")
    for bad in ({"idle_minutes": 120, "down": True}, {"idle_minutes": 30, "down": False}, {"idle_minutes": 30}):
        t = copy.deepcopy(DEV)
        t["resources"]["autostop"] = bad
        assert "E5" in codes(t, "cluster")
    t = copy.deepcopy(DEV)
    del t["resources"]["autostop"]
    assert "E5" in codes(t, "cluster")


def test_warnings():
    t = copy.deepcopy(JOB)
    del t["resources"]["max_hourly_cost"]
    assert "W1" in codes(t)
    t = copy.deepcopy(JOB)
    t["resources"]["any_of"] = t["resources"]["any_of"][:1]
    assert "W2" in codes(t)
    t = copy.deepcopy(JOB)
    t["file_mounts"]["/checkpoint"]["source"] = "s3://my-bucket"
    assert "W3" in codes(t)                      # candidates include gcp and k8s
    t["resources"]["any_of"] = [{"infra": "aws/us-east-1"}, {"infra": "aws/us-west-2"}]
    assert "W3" not in codes(t)


def test_command_line_exit_status():
    def run(path, *extra):
        return subprocess.run([sys.executable, "-B", str(HERE / "policy_check.py"), str(path), *extra],
                              capture_output=True, text=True)
    ok = run(HERE / "job.yaml")
    assert ok.returncode == 0 and "0 error(s), 0 warning(s)" in ok.stdout
    # the same dev cluster file used as a managed job is fine; as a cluster without autostop it is not
    assert run(HERE / "dev-cluster.yaml", "--kind", "cluster").returncode == 0
    assert run(HERE / "job.yaml", "--kind", "cluster").returncode == 1


def test_bad_job_breaks_exactly_the_expected_rules():
    got = pc.check(BAD)
    assert {c for c, _, _ in got} == {"E1", "E2", "E3", "E4", "W1", "W2"}
    assert sum(1 for c, _, _ in got if c == "E1") == 2          # project and owner


def test_residency_rule():
    eu = ["aws/eu-", "gcp/europe-"]
    got = pc.check(JOB, allow=eu)
    assert {c for c, _, _ in got} == {"E6", "W4"}
    assert [m for c, _, m in got if c == "E6"][0].startswith("aws/us-east-1")
    t = copy.deepcopy(JOB)
    t["resources"]["any_of"] = [{"infra": "aws/eu-west-3"}, {"infra": "gcp/europe-west4"}]
    assert pc.check(t, allow=eu) == []
    t["resources"]["any_of"] = [{"infra": "aws"}]                # no region: could be anywhere
    assert "E6" in {c for c, _, _ in pc.check(t, allow=eu)}
    assert pc.check(JOB) == []                                    # without --allow-prefix the rule is off


def test_bad_job_exit_status_is_one():
    r = subprocess.run([sys.executable, "-B", str(HERE / "policy_check.py"), str(HERE / "bad-job.yaml")],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "5 error(s), 2 warning(s)" in r.stdout


def test_eu_variant_passes_the_residency_rule_with_one_warning():
    got = pc.check(EU, allow=["aws/eu-", "gcp/europe-"])
    assert [c for c, _, _ in got] == ["W4"]
