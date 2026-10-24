import copy
import os
from pathlib import Path

import pytest

import config
from fake_sacctmgr import FakeSacctmgr

IMPL = Path(__file__).resolve().parent.parent / os.environ.get("IMPL", "starter")
FIX = Path(__file__).resolve().parent.parent / "fixtures"
CFG = config.load(IMPL / "cluster.yml")
BASE_ASSOC = "sandbox|root|||1|normal\nsandbox|root|root||1|normal\nsandbox|research||root|1|normal\nsandbox|research|root||1|normal\n"


def real_state():
    return config.parse_state((FIX / "assoc.txt").read_text(), (FIX / "qos.txt").read_text())


def base_state():
    return config.parse_state(BASE_ASSOC, "normal|0|\n")


def test_the_shipped_desired_state_is_valid():
    assert config.validate(CFG)


def test_validate_reports_every_kind_of_mistake():
    bad = copy.deepcopy(CFG)
    bad["accounts"]["Team_C"] = {"parent": "ghost", "fairshare": -1}
    bad["accounts"]["x"] = {"parent": "y", "fairshare": 1}
    bad["accounts"]["y"] = {"parent": "x", "fairshare": 1}
    bad["qos"]["z"] = {"priority": 1, "preempt": ["ghost"]}
    bad["users"]["carol"] = {"account": "ghost", "qos": ["ghost"]}
    with pytest.raises(ValueError) as e:
        config.validate(bad)
    msg = str(e.value)
    for needle in ("lower-cases", "unknown parent ghost", "non-negative integer", "parent cycle",
                   "preempts unknown qos ghost", "unknown account ghost", "unknown qos ghost"):
        assert needle in msg, needle


def test_parse_state_reads_the_real_sacctmgr_output():
    st = real_state()
    assert st["accounts"]["teama"] == {"parent": "research", "fairshare": 2}
    assert st["accounts"]["root"]["parent"] is None
    assert st["user_accounts"]["alice"] == {"teama"} and st["user_accounts"]["root"] >= {"teama", "teamb", "research"}
    assert st["user_qos"]["alice"] == {"normal", "urgent"} and st["user_qos"]["bob"] == {"normal"}
    assert st["qos"]["urgent"] == {"priority": 2000, "preempt": frozenset({"normal"})}


def test_the_real_captured_state_is_already_converged():
    assert config.plan(CFG, real_state()) == []
    assert config.drift(CFG, real_state()) == {"accounts": [], "qos": [], "users": []}


def test_plan_from_an_empty_cluster_is_ordered_and_uses_the_syntax_verified_on_slurm():
    cmds = [" ".join(c) for c in config.plan(CFG, base_state())]
    assert cmds == [
        "sacctmgr -i add qos urgent Priority=2000 Preempt=normal",
        "sacctmgr -i add account teama parent=research fairshare=2",
        "sacctmgr -i add account teamb parent=research fairshare=3",
        "sacctmgr -i add user alice account=teama",
        "sacctmgr -i modify user where name=alice set qos+=urgent",
        "sacctmgr -i add user bob account=teamb",
    ]


def test_parents_come_before_children_whatever_the_order_in_the_file():
    cfg = {"accounts": {"leaf": {"parent": "mid", "fairshare": 1}, "mid": {"parent": "research", "fairshare": 1}},
           "qos": {}, "users": {}}
    names = [c[4] for c in config.plan(cfg, base_state())]
    assert names == ["mid", "leaf"]


def test_changes_become_modify_commands():
    cfg = copy.deepcopy(CFG)
    cfg["accounts"]["teama"]["fairshare"] = 5
    cfg["qos"]["urgent"] = {"priority": 3000, "preempt": ["normal"]}
    cmds = [" ".join(c) for c in config.plan(cfg, real_state())]
    assert cmds == ["sacctmgr -i modify qos where name=urgent set Priority=3000 Preempt=normal",
                    "sacctmgr -i modify account where name=teama set fairshare=5"]
    cfg = copy.deepcopy(CFG)  # a decrease, a change of Preempt alone and a new account for an existing user are changes too
    cfg["accounts"]["teamb"]["fairshare"] = 1
    cfg["qos"]["low"] = {"priority": 1}
    cfg["qos"]["urgent"]["preempt"] = ["normal", "low"]
    cfg["users"]["bob"]["account"] = "teama"
    assert [" ".join(c) for c in config.plan(cfg, real_state())] == [
        "sacctmgr -i add qos low Priority=1",
        "sacctmgr -i modify qos where name=urgent set Priority=2000 Preempt=low,normal",
        "sacctmgr -i modify account where name=teamb set fairshare=1",
        "sacctmgr -i add user bob account=teama"]


def test_applying_the_plan_converges_and_a_second_plan_is_empty():
    fake = FakeSacctmgr(base_state())
    n = config.apply(config.plan(CFG, fake.state), fake.run)
    assert n == 6
    assert config.plan(CFG, fake.state) == []  # idempotence by difference
    assert config.apply(config.plan(CFG, fake.state), fake.run) == 0


def test_the_plan_is_never_destructive_and_drift_is_reported_not_removed():
    cmds = config.plan(CFG, base_state())
    assert not any(x in " ".join(c) for c in cmds for x in ("delete", "remove", "-="))
    cur = real_state()
    cur["accounts"]["old"] = {"parent": "research", "fairshare": 1}
    cur["qos"]["legacy"] = {"priority": 5, "preempt": frozenset()}
    assert config.drift(CFG, cur) == {"accounts": ["old"], "qos": ["legacy"], "users": []}
    assert config.plan(CFG, cur) == []


def test_apply_stops_at_the_first_failure_and_says_which():
    fake = FakeSacctmgr(base_state())
    cmds = config.plan(CFG, base_state())
    fake.run(cmds[0])  # the QOS now exists: adding it again exits 1, like the real sacctmgr
    with pytest.raises(RuntimeError) as e:
        config.apply(cmds, fake.run)
    assert "add qos urgent" in str(e.value) and len(fake.calls) == 2
