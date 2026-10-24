"""The validator accepts the lab manifests and rejects each of the defects below (mutation testing of the validator)."""
import copy
from pathlib import Path

import pytest
import yaml

import validate_manifests as vm

MANIFESTS = Path(__file__).resolve().parent.parent / "manifests"


def docs(name):
    return list(yaml.safe_load_all((MANIFESTS / name).read_text()))


def test_every_lab_manifest_is_valid():
    for f, _, doc in vm.load_docs([MANIFESTS]):
        assert vm.validate_doc(doc) == [], (f.name, doc["kind"])


def cq(name="research"):
    return copy.deepcopy(next(d for d in docs("30-clusterqueues.yaml") if d["metadata"]["name"] == name))


def res(doc, resource="nvidia.com/gpu"):
    return next(r for r in doc["spec"]["resourceGroups"][0]["flavors"][0]["resources"] if r["name"] == resource)


def mut_typo_field(d):
    d["spec"]["queueingStrategie"] = "StrictFIFO"

def mut_bad_enum(d):
    d["spec"]["queueingStrategy"] = "FIFO"

def mut_missing_nominal(d):
    del res(d)["nominalQuota"]

def mut_borrow_without_cohort(d):
    del d["spec"]["cohortName"]

def mut_lending_above_nominal(d):
    res(d)["lendingLimit"] = 40

def mut_reclaim_never_with_borrow(d):
    d["spec"]["preemption"]["reclaimWithinCohort"] = "Never"
    d["spec"]["preemption"]["borrowWithinCohort"] = {"policy": "LowerPriority"}

def mut_resource_order(d):
    rs = d["spec"]["resourceGroups"][0]["flavors"][0]["resources"]
    rs[0], rs[2] = rs[2], rs[0]

def mut_wrong_version(d):
    d["apiVersion"] = "kueue.x-k8s.io/v1beta1"

def mut_missing_resource(d):
    del d["spec"]["resourceGroups"][0]["flavors"][0]["resources"][1]


@pytest.mark.parametrize("mutation, expected", [
    (mut_typo_field, "queueingStrategie"),
    (mut_bad_enum, "FIFO"),
    (mut_missing_nominal, "nominalQuota"),
    (mut_borrow_without_cohort, "borrowingLimit must be nil when cohort is empty"),
    (mut_lending_above_nominal, "exceeds nominalQuota"),
    (mut_reclaim_never_with_borrow, "reclaimWithinCohort=Never"),
    (mut_resource_order, "order of coveredResources"),
    (mut_wrong_version, "expected 'kueue.x-k8s.io/v1beta2'"),
    (mut_missing_resource, "same number of resources"),
])
def test_validator_rejects(mutation, expected):
    doc = cq()
    mutation(doc)
    errors = vm.validate_doc(doc)
    assert errors and any(expected in e for e in errors), errors


def test_priority_value_must_be_an_integer():
    d = copy.deepcopy(docs("20-priorityclasses.yaml")[1])
    d["value"] = "500"
    assert vm.validate_doc(d)


def test_core_kinds_are_checked_strictly():
    job = copy.deepcopy(docs("50-job.yaml")[0])
    job["spec"]["parallelsim"] = 4        # typo: strict mode must see it
    assert vm.validate_doc(job)
