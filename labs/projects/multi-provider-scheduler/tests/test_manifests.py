import copy
import subprocess
import sys

import pytest
import yaml

import data
import manifests as M

INFRA = {"cloud-a/r1": "infra-a/zone-1", "cloud-b/r2": "infra-b/zone-2", "cloud-c/r3": "infra-c/zone-3"}


def test_skypilot_task_shape():
    t = M.skypilot_task("train", "H100", 8, True, "python train.py", ["infra-a/zone-1", "infra-b/zone-2"],
                        recovery="EAGER_NEXT_REGION")
    r = t["resources"]
    assert r["accelerators"] == "H100:8" and r["use_spot"] is True
    assert r["ordered"] == [{"infra": "infra-a/zone-1"}, {"infra": "infra-b/zone-2"}]
    assert r["job_recovery"] == {"strategy": "EAGER_NEXT_REGION"} and t["run"] == "python train.py"
    assert "any_of" in M.skypilot_task("t", "H100", 1, False, "x", ["a/b"], ordered=False)["resources"]


def test_skypilot_task_rejects_bad_input():
    with pytest.raises(ValueError):
        M.skypilot_task("t", "H100", 8, True, "x", [])
    with pytest.raises(ValueError):
        M.skypilot_task("t", "H100", 8, True, "x", ["a/b"], recovery="SOMETIMES")


def test_plan_tasks_groups_by_market_in_ranking_order():
    by = {o.id: o for o in data.default_offers()}
    ranked = [by["b-spot"], by["a-spot"], by["a-od"], by["c-od"]]
    spot, od = M.plan_tasks("job7", "H100", 16, ranked, INFRA, "python train.py")
    assert spot["resources"]["use_spot"] is True and od["resources"]["use_spot"] is False
    assert spot["resources"]["ordered"] == [{"infra": "infra-b/zone-2"}, {"infra": "infra-a/zone-1"}]
    assert od["resources"]["ordered"] == [{"infra": "infra-a/zone-1"}, {"infra": "infra-c/zone-3"}]
    assert "job_recovery" in spot["resources"] and "job_recovery" not in od["resources"]
    assert (spot["name"], od["name"]) == ("job7-spot", "job7-on-demand")


def test_yaml_roundtrip_and_yamllint(tmp_path):
    t = M.skypilot_task("train", "H100", 8, True, "python train.py", ["infra-a/zone-1"])
    assert yaml.safe_load(M.dump(t)) == t
    assert list(yaml.safe_load(M.dump(t))["resources"]) == ["accelerators", "use_spot", "ordered"]  # insertion order
    f = tmp_path / "task.yaml"
    f.write_text(M.dump(t))
    r = subprocess.run([sys.executable, "-m", "yamllint", "-d", "relaxed", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_kueue_manifests_are_consistent_and_ordered():
    docs = M.kueue_manifests(data.default_offers(), order=["a-spot", "b-spot", "a-od", "c-od"])
    assert M.validate_kueue(docs)
    assert {d["apiVersion"] for d in docs} == {"kueue.x-k8s.io/v1beta2"}
    cq = next(d for d in docs if d["kind"] == "ClusterQueue")
    names = [f["name"] for f in cq["spec"]["resourceGroups"][0]["flavors"]]
    assert names == ["a-spot", "b-spot", "a-od", "c-od"]
    quotas = {f["name"]: f["resources"][0]["nominalQuota"] for f in cq["spec"]["resourceGroups"][0]["flavors"]}
    assert quotas == {o.id: o.capacity for o in data.default_offers()}
    assert cq["spec"]["namespaceSelector"] == {} and cq["spec"]["resourceGroups"][0]["coveredResources"] == ["nvidia.com/gpu"]
    lq = next(d for d in docs if d["kind"] == "LocalQueue")
    assert lq["metadata"] == {"namespace": "team-a", "name": "gpu-lq"} and lq["spec"] == {"clusterQueue": "gpu-cq"}
    rf = {d["metadata"]["name"]: d["spec"] for d in docs if d["kind"] == "ResourceFlavor"}
    assert rf["a-spot"] == {"nodeLabels": {"market": "spot", "provider": "cloud-a"}}


def test_validate_kueue_catches_each_kind_of_structural_error():
    good = M.kueue_manifests(data.default_offers())
    cases = {}
    d = copy.deepcopy(good); d[-2]["spec"]["resourceGroups"][0]["flavors"][0]["name"] = "ghost"; cases["unknown flavor"] = d
    d = copy.deepcopy(good); d[-1]["spec"]["clusterQueue"] = "ghost"; cases["unknown cluster queue"] = d
    d = copy.deepcopy(good); d[-2]["spec"]["resourceGroups"][0]["flavors"][0]["resources"][0]["nominalQuota"] = "64"; cases["string quota"] = d
    d = copy.deepcopy(good); d.append(copy.deepcopy(good[0])); cases["duplicate"] = d
    d = copy.deepcopy(good); d[0]["apiVersion"] = "kueue.x-k8s.io/v1beta1"; cases["api version"] = d
    d = copy.deepcopy(good); d[-2]["spec"]["resourceGroups"][0]["flavors"][0]["resources"][0]["nominalQuota"] = -1; cases["negative quota"] = d
    d = copy.deepcopy(good); d[-2]["spec"]["resourceGroups"][0]["flavors"][0]["resources"][0]["nominalQuota"] = True; cases["boolean quota"] = d
    d = copy.deepcopy(good); d[-2]["spec"]["resourceGroups"][0]["flavors"][0]["resources"][0]["name"] = "example.com/other"; cases["uncovered resource"] = d
    for name, docs in cases.items():
        with pytest.raises(ValueError):
            M.validate_kueue(docs)
        assert name  # each mutation is rejected for its own reason
    assert M.validate_kueue(good)
    other_ns = copy.deepcopy(good[-1]); other_ns["metadata"]["namespace"] = "team-b"
    assert M.validate_kueue(good + [other_ns])  # same name in another namespace is not a duplicate


def test_dump_writes_multi_document_yaml():
    docs = M.kueue_manifests(data.default_offers())
    loaded = list(yaml.safe_load_all(M.dump(docs)))
    assert loaded == docs
