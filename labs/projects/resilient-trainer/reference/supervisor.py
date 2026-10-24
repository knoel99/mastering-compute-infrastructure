#!/usr/bin/env python3
"""Restart supervisor: relaunch a command after a crash or a stall.

usage: supervisor.py --workdir W [--max-restarts 5] [--stall-timeout 30] [--startup-grace 60] -- CMD ...

A child is "stalled" when its heartbeat file (W/heartbeat) has not been touched
for --stall-timeout seconds (--startup-grace before its first heartbeat).
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def log(path, **fields):
    fields["t"] = round(time.time(), 3)
    with open(path, "a") as f:
        f.write(json.dumps(fields) + "\n")


def kill_group(proc, sig):
    try:
        os.killpg(proc.pid, sig)
    except ProcessLookupError:
        pass


def supervise(cmd, workdir, max_restarts=5, stall_timeout=30.0, startup_grace=60.0, backoff=0.2, poll=0.2):
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    events = work / "supervisor.jsonl"
    heartbeat = work / "heartbeat"
    state = {"proc": None, "term": False}

    def on_term(signum, frame):
        state["term"] = True
        if state["proc"] is not None:
            kill_group(state["proc"], signal.SIGTERM)

    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)

    attempt = 0
    while True:
        started = time.time()
        proc = subprocess.Popen(cmd, start_new_session=True)
        state["proc"] = proc
        log(events, event="launch", attempt=attempt, pid=proc.pid)
        last_beat = started
        progressed = False
        stalled = False
        while proc.poll() is None:
            time.sleep(poll)
            try:
                mtime = heartbeat.stat().st_mtime
            except FileNotFoundError:
                mtime = 0.0
            if mtime >= started and mtime > last_beat:
                last_beat, progressed = mtime, True
            limit = stall_timeout if progressed else startup_grace
            if not state["term"] and time.time() - last_beat > limit:
                log(events, event="stall_kill", attempt=attempt, silent_for=round(time.time() - last_beat, 1))
                kill_group(proc, signal.SIGKILL)
                stalled = True
                proc.wait()
        rc = proc.returncode
        if state["term"]:
            log(events, event="terminated", rc=rc)
            return 143
        if rc == 0 and not stalled:
            log(events, event="success", attempts=attempt + 1)
            return 0
        log(events, event="crash", attempt=attempt, rc=rc, stalled=stalled)
        attempt += 1
        if attempt > max_restarts:
            log(events, event="giving_up", attempts=attempt)
            return 1
        time.sleep(min(backoff * 2 ** (attempt - 1), 5.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--max-restarts", type=int, default=5)
    ap.add_argument("--stall-timeout", type=float, default=30.0)
    ap.add_argument("--startup-grace", type=float, default=60.0)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    args = ap.parse_args()
    cmd = args.cmd[1:] if args.cmd and args.cmd[0] == "--" else args.cmd
    if not cmd:
        ap.error("missing command after --")
    return supervise(cmd, args.workdir, args.max_restarts, args.stall_timeout, args.startup_grace)


if __name__ == "__main__":
    sys.exit(main())
