import json
import os
import signal
import subprocess
import time

import pytest

STEPS = 120


def run(py, impl, args, env=None, timeout=120):
    e = {**os.environ, **(env or {})}
    return subprocess.run([py, str(impl / "train.py"), *args], env=e, cwd=impl, capture_output=True, text=True, timeout=timeout)


def supervised(py, impl, work, trainer_args, env=None, stall=3, timeout=180):
    e = {**os.environ, **(env or {})}
    cmd = [py, str(impl / "supervisor.py"), "--workdir", str(work), "--max-restarts", "4",
           "--stall-timeout", str(stall), "--startup-grace", "30", "--",
           py, str(impl / "train.py"), "--workdir", str(work), *trainer_args]
    return subprocess.run(cmd, env=e, cwd=impl, capture_output=True, text=True, timeout=timeout)


def losses(work):
    """step -> list of every loss ever logged for that step (several after a restart)."""
    out = {}
    for line in (work / "loss.jsonl").read_text().splitlines():
        r = json.loads(line)
        out.setdefault(r["step"], []).append(r["loss"])
    return out


def events(work, name="events.jsonl"):
    return [json.loads(line) for line in (work / name).read_text().splitlines()]


@pytest.fixture(scope="module")
def baseline(tmp_path_factory, py, impl):
    work = tmp_path_factory.mktemp("baseline")
    r = run(py, impl, ["--workdir", str(work), "--steps", str(STEPS)])
    assert r.returncode == 0, r.stderr
    return losses(work)


def assert_same_as_baseline(work, baseline):
    got = losses(work)
    assert sorted(got) == list(range(1, STEPS + 1))
    for step, values in got.items():
        assert set(values) == {baseline[step][0]}, f"loss differs at step {step}: {values} vs {baseline[step]}"


def test_kill9_resumes_bit_exactly(tmp_path, py, impl, baseline):
    r = supervised(py, impl, tmp_path, ["--steps", str(STEPS)], env={"FAULT": "kill:57"})
    assert r.returncode == 0, r.stderr
    starts = events(tmp_path)
    assert [s["resumed_from"] for s in starts] == [0, 50]
    assert_same_as_baseline(tmp_path, baseline)
    assert len(losses(tmp_path)[55]) == 2  # steps 51..56 were recomputed after the crash


def test_torn_checkpoint_write_is_survived(tmp_path, py, impl, baseline):
    # the crash itself: nothing half-written may sit under a final checkpoint name
    crashed = run(py, impl, ["--workdir", str(tmp_path / "crash"), "--steps", str(STEPS)], env={"FAULT": "torn:60"})
    assert crashed.returncode != 0
    assert "ckpt-00000060.pt" not in [p.name for p in (tmp_path / "crash" / "ckpt").iterdir()]
    r = supervised(py, impl, tmp_path, ["--steps", str(STEPS)], env={"FAULT": "torn:60"})
    assert r.returncode == 0, r.stderr
    assert [s["resumed_from"] for s in events(tmp_path)] == [0, 50]
    assert_same_as_baseline(tmp_path, baseline)


def test_corrupt_latest_checkpoint_falls_back(tmp_path, py, impl, baseline):
    assert run(py, impl, ["--workdir", str(tmp_path), "--steps", "80"]).returncode == 0
    newest = tmp_path / "ckpt" / "ckpt-00000080.pt"
    blob = bytearray(newest.read_bytes())
    blob[len(blob) // 2] ^= 0xFF
    newest.write_bytes(bytes(blob))
    assert run(py, impl, ["--workdir", str(tmp_path), "--steps", str(STEPS)]).returncode == 0
    last = events(tmp_path)[-1]
    assert last["resumed_from"] == 70
    assert [name for name, _ in last["skipped"]] == ["ckpt-00000080.pt"]
    assert_same_as_baseline(tmp_path, baseline)


def test_hung_trainer_is_killed_and_restarted(tmp_path, py, impl, baseline):
    r = supervised(py, impl, tmp_path, ["--steps", str(STEPS)], env={"FAULT": "hang:45"}, stall=3)
    assert r.returncode == 0, r.stderr
    sup = events(tmp_path, "supervisor.jsonl")
    kinds = [e["event"] for e in sup]
    assert "stall_kill" in kinds and kinds[-1] == "success"
    # detected after --stall-timeout (3 s), not after --startup-grace (30 s)
    assert 3 <= next(e for e in sup if e["event"] == "stall_kill")["silent_for"] < 30
    assert_same_as_baseline(tmp_path, baseline)


def test_gives_up_after_max_restarts(tmp_path, py, impl):
    cmd = [py, str(impl / "supervisor.py"), "--workdir", str(tmp_path), "--max-restarts", "2", "--",
           py, "-c", "import sys; sys.exit(3)"]
    r = subprocess.run(cmd, cwd=impl, capture_output=True, text=True, timeout=60)
    assert r.returncode == 1
    kinds = [e["event"] for e in events(tmp_path, "supervisor.jsonl")]
    assert kinds.count("launch") == 3 and kinds[-1] == "giving_up"


def test_sigterm_stops_supervisor_and_child(tmp_path, py, impl):
    cmd = [py, str(impl / "supervisor.py"), "--workdir", str(tmp_path), "--",
           py, "-c", "import time; time.sleep(600)"]
    p = subprocess.Popen(cmd, cwd=impl)
    log = tmp_path / "supervisor.jsonl"
    deadline = time.time() + 20
    while time.time() < deadline and not (log.exists() and "launch" in log.read_text()):
        time.sleep(0.1)
    pid = json.loads(log.read_text().splitlines()[0])["pid"]
    p.send_signal(signal.SIGTERM)
    assert p.wait(timeout=20) == 143
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
