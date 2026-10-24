#!/usr/bin/env python3
"""Supervisor: launch the trainer, detect crashes and hangs, isolate bad nodes, relaunch.

The contract (what the tests check):
  * the trainer runs in its own process group; on a hang or on SIGTERM the WHOLE group is killed;
  * a hang = the heartbeat file is older than policy.hang_timeout (startup counts as a heartbeat);
  * an exit is classified (see classify): done / fatal (not worth retrying) / node (self-diagnosed
    bad node) / hang / retry;
  * a node that reports itself bad, or that causes policy.node_strikes failures, is excluded;
  * the supervisor gives up (exit 1) after policy.max_restarts relaunches, or after
    policy.max_no_progress consecutive attempts that did not advance the last durable checkpoint,
    or when no healthy node is left;
  * SIGTERM is forwarded to the trainer, nothing is relaunched, exit status 143.
Events are appended to <workdir>/supervisor.jsonl.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Policy:
    max_restarts: int = 10
    hang_timeout: float = 5.0
    poll: float = 0.05
    fatal_codes: tuple = (2,)  # e.g. 2 = bad command line / configuration: retrying cannot help
    node_bad_code: int = 42  # the trainer's own health check failed on this node
    node_strikes: int = 2
    max_no_progress: int = 2
    backoff_base: float = 0.0  # seconds; doubled after each consecutive failure
    backoff_cap: float = 60.0
    kill_grace: float = 1.0


def classify(returncode, hung, policy):
    """'done' | 'hang' | 'fatal' | 'node' | 'retry' for one finished attempt."""
    if hung:
        return "hang"
    if returncode == 0:
        return "done"
    if returncode in policy.fatal_codes:
        return "fatal"
    if returncode == policy.node_bad_code:
        return "node"
    return "retry"  # any other exit status or a signal (negative return code)


def kill_group(proc, grace):
    """SIGTERM the process group, then SIGKILL whatever survives `grace` seconds later."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline and proc.poll() is None:
        time.sleep(0.02)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait()


@dataclass
class Supervisor:
    cmd: list
    workdir: Path
    nodes: list
    policy: Policy = field(default_factory=Policy)
    stop: bool = False
    child: object = None

    def __post_init__(self):
        self.workdir = Path(self.workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.excluded, self.strikes, self.last_index = set(), {}, -1

    def log(self, **ev):
        with open(self.workdir / "supervisor.jsonl", "a") as f:
            f.write(json.dumps({"t": round(time.time(), 3), **ev}) + "\n")

    def progress(self):
        p = self.workdir / "state.json"
        try:
            return json.loads(p.read_text())["step"]
        except (OSError, ValueError, KeyError):
            return 0

    def pick_node(self):
        """Round-robin over the nodes that are not excluded, starting after the last one used."""
        for k in range(1, len(self.nodes) + 1):
            i = (self.last_index + k) % len(self.nodes)
            if self.nodes[i] not in self.excluded:
                self.last_index = i
                return self.nodes[i]
        return None

    def _on_term(self, signum, frame):
        self.stop = True
        if self.child is not None and self.child.poll() is None:
            try:
                os.killpg(self.child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    def attempt(self, node, n):
        env = dict(os.environ, NODE_NAME=node, SUP_ATTEMPT=str(n))
        hb = self.workdir / "heartbeat"
        hb.unlink(missing_ok=True)  # a heartbeat left by the previous attempt must not count
        launched = time.time()
        self.child = subprocess.Popen(self.cmd, env=env, start_new_session=True)
        hung = False
        while self.child.poll() is None:
            if self.stop:
                kill_group(self.child, self.policy.kill_grace)
                return self.child.returncode, False
            try:
                mtime = hb.stat().st_mtime
            except FileNotFoundError:
                mtime = 0.0
            if time.time() - max(mtime, launched) > self.policy.hang_timeout:  # startup counts as a heartbeat
                hung = True
                kill_group(self.child, self.policy.kill_grace)
                break
            time.sleep(self.policy.poll)
        else:
            try:  # the trainer exited: no member of its group may survive it
                os.killpg(self.child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        return self.child.returncode, hung

    def run(self):
        signal.signal(signal.SIGTERM, self._on_term)
        signal.signal(signal.SIGINT, self._on_term)
        pol, no_progress, consecutive = self.policy, 0, 0
        for n in range(1, pol.max_restarts + 2):
            node = self.pick_node()
            if node is None:
                self.log(event="give_up", reason="no healthy node left")
                return 1
            before = self.progress()
            self.log(event="launch", attempt=n, node=node, resume_step=before)
            rc, hung = self.attempt(node, n)
            if self.stop:
                self.log(event="terminated", attempt=n)
                return 143
            kind = classify(rc, hung, pol)
            after = self.progress()
            self.log(event="exit", attempt=n, node=node, rc=rc, kind=kind, step_before=before, step_after=after)
            if kind == "done":
                self.log(event="done", attempts=n)
                return 0
            if kind == "fatal":
                self.log(event="give_up", reason=f"fatal exit status {rc}")
                return rc
            no_progress = 0 if after > before else no_progress + 1
            if kind == "node":
                self.excluded.add(node)
                self.log(event="exclude", node=node, why="self-diagnosed")
            else:
                self.strikes[node] = self.strikes.get(node, 0) + 1
                if self.strikes[node] >= pol.node_strikes:
                    self.excluded.add(node)
                    self.log(event="exclude", node=node, why=f"{self.strikes[node]} strikes")
            if no_progress >= pol.max_no_progress:
                self.log(event="give_up", reason=f"{no_progress} attempts without progress")
                return 1
            consecutive += 1
            delay = min(pol.backoff_cap, pol.backoff_base * 2 ** (consecutive - 1)) if pol.backoff_base else 0.0
            if delay:
                time.sleep(delay)
        self.log(event="give_up", reason="restart budget exhausted")
        return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--nodes", default="n0,n1,n2", help="comma-separated labels exported as NODE_NAME")
    ap.add_argument("--max-restarts", type=int, default=10)
    ap.add_argument("--hang-timeout", type=float, default=5.0)
    ap.add_argument("--max-no-progress", type=int, default=2)
    ap.add_argument("--backoff", type=float, default=0.0)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    pol = Policy(max_restarts=a.max_restarts, hang_timeout=a.hang_timeout, max_no_progress=a.max_no_progress, backoff_base=a.backoff)
    return Supervisor(cmd, a.workdir, a.nodes.split(","), pol).run()


if __name__ == "__main__":
    sys.exit(main())
