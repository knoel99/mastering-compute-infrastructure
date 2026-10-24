import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

import supervisor as S

HERE = Path(__file__).resolve().parent
IMPL = os.environ.get("IMPL", "reference")
WORKER = [sys.executable, str(HERE / "worker.py")]


def make(tmp_path, plan=None, nodes=("n0", "n1", "n2"), steps=30, extra=(), **pol):
    os.environ["FAULT_PLAN"] = json.dumps(plan or {})
    policy = S.Policy(hang_timeout=pol.pop("hang_timeout", 1.0), kill_grace=0.3, **pol)
    cmd = WORKER + ["--workdir", str(tmp_path), "--steps", str(steps), "--ckpt-every", "5", "--step-ms", "10", *extra]
    return S.Supervisor(cmd, tmp_path, list(nodes), policy)


def events(tmp_path):
    return [json.loads(line) for line in (tmp_path / "supervisor.jsonl").read_text().splitlines()]


def alive(pid):
    """True if the process exists and is not a zombie (an orphan whose parent is gone may stay a zombie
    for a while if PID 1 does not reap it: it is dead for our purpose)."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except FileNotFoundError:
        return False
    return stat.rsplit(")", 1)[1].split()[0] != "Z"


def test_classify():
    p = S.Policy()
    assert S.classify(0, False, p) == "done"
    assert S.classify(-9, True, p) == "hang"
    assert S.classify(2, False, p) == "fatal"
    assert S.classify(42, False, p) == "node"
    assert S.classify(1, False, p) == "retry"
    assert S.classify(-11, False, p) == "retry"


def test_clean_run(tmp_path):
    assert make(tmp_path).run() == 0
    assert [e["event"] for e in events(tmp_path)] == ["launch", "exit", "done"]


def test_crash_then_resume_from_checkpoint_on_another_node(tmp_path):
    plan = {"n0": {"mode": "exit", "at_step": 7, "code": 1, "once": True}}
    assert make(tmp_path, plan).run() == 0
    ev = events(tmp_path)
    launches = [e for e in ev if e["event"] == "launch"]
    assert len(launches) == 2
    assert launches[0]["node"] == "n0" and launches[1]["node"] == "n1"
    assert launches[1]["resume_step"] == 5  # last durable checkpoint before step 7
    assert json.loads((tmp_path / "state.json").read_text())["step"] == 30


def test_hang_is_detected_and_the_whole_group_is_killed(tmp_path):
    plan = {"n0": {"mode": "hang", "at_step": 6, "once": True}}
    assert make(tmp_path, plan, extra=["--with-child"]).run() == 0
    ex = [e for e in events(tmp_path) if e["event"] == "exit"]
    assert ex[0]["kind"] == "hang" and ex[-1]["kind"] == "done"
    child = int((tmp_path / "child-1.pid").read_text())
    time.sleep(0.2)
    assert not alive(child), "the grandchild of the hung trainer must be killed with its group"


def test_bad_node_is_excluded_and_never_used_again(tmp_path):
    plan = {"n0": {"mode": "exit", "at_step": 7, "code": 1, "once": True},
            "n1": {"mode": "exit", "at_step": 0, "code": 42}}  # n1 reports itself bad as soon as it starts
    assert make(tmp_path, plan).run() == 0
    ev = events(tmp_path)
    assert {"event": "exclude", "node": "n1", "why": "self-diagnosed"} == {k: v for k, v in next(e for e in ev if e["event"] == "exclude").items() if k != "t"}
    first_exclusion = next(i for i, e in enumerate(ev) if e["event"] == "exclude")
    assert all(e.get("node") != "n1" for e in ev[first_exclusion + 1:] if e["event"] == "launch")


def test_two_strikes_exclude_a_node(tmp_path):
    plan = {"n0": {"mode": "decay", "after": 6, "code": 1},  # n0 always dies 6 steps after it starts
            "n1": {"mode": "exit", "at_step": 8, "code": 1, "once": True}}
    assert make(tmp_path, plan, nodes=("n0", "n1")).run() == 0
    ev = events(tmp_path)
    ex = [e for e in ev if e["event"] == "exclude"]
    assert ex and ex[0]["node"] == "n0" and ex[0]["why"] == "2 strikes"


def test_same_failure_everywhere_stops_quickly(tmp_path):
    plan = {"*": {"mode": "exit", "at_step": 0, "code": 1}}  # a software bug: every node fails at once
    sup = make(tmp_path, plan, max_restarts=10, max_no_progress=2)
    assert sup.run() == 1
    assert len([e for e in events(tmp_path) if e["event"] == "launch"]) == 2  # not 11


def test_fatal_exit_status_is_not_retried(tmp_path):
    plan = {"*": {"mode": "exit", "at_step": 0, "code": 2}}
    assert make(tmp_path, plan).run() == 2
    assert len([e for e in events(tmp_path) if e["event"] == "launch"]) == 1


def test_restart_budget_is_enforced(tmp_path):
    plan = {"*": {"mode": "decay", "after": 6, "code": 1}}  # makes progress, then dies, forever
    sup = make(tmp_path, plan, nodes=("n0", "n1", "n2", "n3", "n4", "n5"), steps=1000, max_restarts=3, node_strikes=99)
    assert sup.run() == 1
    assert len([e for e in events(tmp_path) if e["event"] == "launch"]) == 4  # first launch + 3 restarts
    assert "budget" in events(tmp_path)[-1]["reason"]


def test_sigterm_is_forwarded_and_nothing_is_relaunched(tmp_path):
    env = dict(os.environ, FAULT_PLAN="{}", IMPL=IMPL)
    cmd = [sys.executable, str(HERE / IMPL / "supervisor.py"), "--workdir", str(tmp_path), "--nodes", "n0,n1", "--",
           *WORKER, "--workdir", str(tmp_path), "--steps", "100000", "--step-ms", "10"]
    p = subprocess.Popen(cmd, env=env)
    t0 = time.time()
    while not (tmp_path / "heartbeat").exists() and time.time() - t0 < 20:
        time.sleep(0.05)
    assert (tmp_path / "heartbeat").exists()
    p.send_signal(signal.SIGTERM)
    assert p.wait(timeout=20) == 143
    assert len([e for e in events(tmp_path) if e["event"] == "launch"]) == 1
