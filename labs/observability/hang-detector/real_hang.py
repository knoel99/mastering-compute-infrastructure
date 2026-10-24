"""A REAL hang, on CPU: two gloo ranks, rank 1 stops before a collective, a stagnation watcher notices.

What is real: processes, torch.distributed (gloo backend, CPU), the blocked all_reduce, the OS signal, the
faulthandler stack dump, the watcher's wall-clock polling. What is NOT the GPU case: gloo is not NCCL, there is
no GPU, and the hang is injected on purpose (rank 1 sleeps), so the utilization signature is not exercised here.

    python3 real_hang.py             # runs the demonstration and prints what the operator would see
"""
import argparse
import faulthandler
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import timedelta
from pathlib import Path

HANG_STEP = 150          # rank 1 stops before the collective of this step
STEPS = 400              # the job would run this long without the fault
WINDOW_S = 3.0           # watcher: no progress for this long means hang (steps take ~10 ms here)


def log(d, rank, event, step):
    with open(d / f"rank{rank}.log", "a") as f:
        f.write(json.dumps({"t": round(time.time(), 3), "rank": rank, "event": event, "step": step}) + "\n")


def child(rank, d):
    import torch
    import torch.distributed as dist
    torch.set_num_threads(1)
    stack = open(d / f"stack{rank}.txt", "w")
    faulthandler.register(signal.SIGUSR1, file=stack, all_threads=True)   # dump all stacks on SIGUSR1
    dist.init_process_group("gloo", init_method=f"file://{d}/rdzv", rank=rank, world_size=2,
                            timeout=timedelta(minutes=30))                 # default timeout for non-NCCL backends
    x = torch.randn(64, 64)
    for step in range(STEPS):
        log(d, rank, "step_start", step)
        y = (x @ x).sum()                                                  # the "compute" of the step
        if rank == 1 and step == HANG_STEP:
            log(d, rank, "injected_hang", step)
            time.sleep(3600)  # the fault: this rank never joins the collective
        log(d, rank, "enter_allreduce", step)
        t = torch.tensor([float(y)])
        dist.all_reduce(t)
        log(d, rank, "exit_allreduce", step)
        if rank == 0:
            tmp = d / "progress.tmp"
            tmp.write_text(str(step))
            os.replace(tmp, d / "progress")                                # atomic, like a textfile-collector write
        time.sleep(0.01)


def last_event(d, rank, event):
    best = None
    for line in (d / f"rank{rank}.log").read_text().splitlines():
        r = json.loads(line)
        if r["event"] == event:
            best = r["step"]
    return best


def frames(path, limit=3):
    """Innermost frames of the main thread from a faulthandler dump, as 'file:line in function [-> source]'."""
    out = []
    for l in path.read_text().splitlines():
        m = re.match(r'\s*File "(.+)", line (\d+) in (\S+)', l)
        if not m:
            continue
        name, line = Path(m.group(1)).name, int(m.group(2))
        src = ""
        if name == Path(__file__).name:
            src = "   -> " + Path(__file__).read_text().splitlines()[line - 1].strip()
        out.append(f"{name}:{line} in {m.group(3)}{src}")
    return out[:limit]


def parent():
    from watch import Stagnation
    d = Path(tempfile.mkdtemp(prefix="real_hang."))
    here = str(Path(__file__).resolve())
    env = dict(os.environ, OMP_NUM_THREADS="1")
    procs = [subprocess.Popen([sys.executable, here, "--child", str(r), "--dir", str(d)], env=env) for r in (0, 1)]
    det, t0, alarm_at = Stagnation(WINDOW_S), time.monotonic(), None
    try:
        while time.monotonic() - t0 < 120:
            p = d / "progress"
            step = int(p.read_text()) if p.exists() and p.read_text().strip() else None
            if det.update(time.monotonic(), step):
                if det.last < HANG_STEP - 1:   # stalled long before the injected fault: a scheduling hiccup on a
                    det = Stagnation(WINDOW_S)  # loaded machine, not the hang. Keep watching instead of failing.
                    continue
                alarm_at = time.monotonic()
                break
            time.sleep(0.25)
        if alarm_at is None:
            print("FAIL: no alarm within 120 s")
            return 1
        print(f"ALARM: no progress for {WINDOW_S:.0f} s; last completed step = {det.last}")
        for p in procs:
            os.kill(p.pid, signal.SIGUSR1)
        time.sleep(1.0)
        for r in (0, 1):
            print(f"--- rank {r}: innermost frames of the stack dump (faulthandler, SIGUSR1)")
            for fr in frames(d / f"stack{r}.txt"):
                print("   ", fr)
        entered = {r: last_event(d, r, "enter_allreduce") for r in (0, 1)}
        exited = {r: last_event(d, r, "exit_allreduce") for r in (0, 1)}
        print(f"last collective entered: {entered}; last collective completed: {exited}")
        missing = [r for r in (0, 1) if entered[r] < max(entered.values())]
        print(f"rank(s) that never joined the last collective: {missing}")
        ok = (missing == [1] and det.last == HANG_STEP - 1
              and any("time.sleep(3600)" in f for f in frames(d / "stack1.txt", 2))
              and any(f.startswith("distributed_c10d.py") and "all_reduce" in f for f in frames(d / "stack0.txt", 4)))
        print("OK real-hang: localized rank 1 at step", HANG_STEP if ok else "??")
        return 0 if ok else 1
    finally:
        for p in procs:
            p.kill()
        for p in procs:
            p.wait()
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", type=int)
    ap.add_argument("--dir")
    a = ap.parse_args()
    if a.child is not None:
        child(a.child, Path(a.dir))
    else:
        sys.exit(parent())
