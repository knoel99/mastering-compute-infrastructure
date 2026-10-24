#!/usr/bin/env python3
"""SIMULATED training process used to test supervisors. It does no real training.

It counts steps, writes an atomic "checkpoint" (state.json) every --ckpt-every steps, touches a
heartbeat file after every step, and misbehaves on purpose according to FAULT_PLAN, a JSON
object {node_name_or_*: {"mode": ..., ...}} read together with the NODE_NAME the supervisor sets.
The "nodes" are only labels: no hardware is involved.

modes:  exit   at_step=N code=C [once=true]     exit with code C when reaching step N
        hang   at_step=N [once=true]            stop touching the heartbeat and sleep forever
        decay  after=K code=C                   exit with code C K steps after every (re)start
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def atomic_write(path, text):
    tmp = Path(str(path) + ".tmp")
    with open(tmp, "w") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--ckpt-every", type=int, default=5)
    ap.add_argument("--step-ms", type=float, default=20.0)
    ap.add_argument("--with-child", action="store_true", help="spawn a grandchild, to test process-group kills")
    a = ap.parse_args(argv)
    wd = Path(a.workdir)
    wd.mkdir(parents=True, exist_ok=True)
    node, attempt = os.environ.get("NODE_NAME", "n0"), os.environ.get("SUP_ATTEMPT", "0")
    plan = json.loads(os.environ.get("FAULT_PLAN", "{}"))
    fault = plan.get(node) or plan.get("*")
    state = wd / "state.json"
    step = json.loads(state.read_text())["step"] if state.exists() else 0
    start = step
    if a.with_child:
        child = subprocess.Popen(["sleep", "600"])
        (wd / f"child-{attempt}.pid").write_text(str(child.pid))
    hb = wd / "heartbeat"
    atomic_write(hb, json.dumps({"step": step, "node": node}))
    print(f"worker node={node} attempt={attempt} resume_step={step}", flush=True)
    while step < a.steps:
        if fault:
            once_marker = wd / f"fired-{node}.marker"
            armed = not (fault.get("once") and once_marker.exists())
            mode = fault["mode"]
            if armed and mode in ("exit", "hang") and step >= fault["at_step"]:
                if fault.get("once"):
                    once_marker.write_text("1")
                if mode == "exit":
                    sys.exit(fault.get("code", 1))
                while True:  # hang: alive, but silent
                    time.sleep(3600)
            if mode == "decay" and step - start >= fault["after"]:
                sys.exit(fault.get("code", 1))
        time.sleep(a.step_ms / 1000.0)
        step += 1
        if step % a.ckpt_every == 0 or step == a.steps:
            atomic_write(state, json.dumps({"step": step}))
        os.utime(hb)  # heartbeat: "I finished a step"
    print("worker done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
