import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "lib"))

import pytest  # noqa: E402

import run_decision  # noqa: E402


@pytest.fixture(scope="session")
def policy():
    with open(os.path.join(HERE, "policy.json"), encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="session")
def impl():
    name = os.environ.get("IMPL", "reference")
    return run_decision.load_impl(name)


@pytest.fixture()
def verdict(impl, policy):
    def run(scenario, level="full"):
        return run_decision.evaluate(os.path.join(HERE, "fixtures", scenario), impl, policy, level)
    return run
