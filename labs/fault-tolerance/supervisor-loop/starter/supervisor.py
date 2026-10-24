#!/usr/bin/env python3
"""STARTER. Same interface as reference/supervisor.py; the logic is yours to write.

Read the contract in reference/supervisor.py's docstring only AFTER your first attempt, and run
    IMPL=starter python3 -m pytest -q test_supervisor.py
to see what each test expects. Keep the names: the tests import Policy, classify, kill_group, Supervisor.
"""
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Policy:
    max_restarts: int = 10
    hang_timeout: float = 5.0
    poll: float = 0.05
    fatal_codes: tuple = (2,)
    node_bad_code: int = 42
    node_strikes: int = 2
    max_no_progress: int = 2
    backoff_base: float = 0.0
    backoff_cap: float = 60.0
    kill_grace: float = 1.0


def classify(returncode, hung, policy):
    """Return 'done' | 'hang' | 'fatal' | 'node' | 'retry' for one finished attempt."""
    raise NotImplementedError("classify: map (returncode, hung) to a kind")


def kill_group(proc, grace):
    """Terminate the whole process group of `proc` (SIGTERM, then SIGKILL after `grace` seconds)."""
    raise NotImplementedError("kill_group")


@dataclass
class Supervisor:
    cmd: list
    workdir: Path
    nodes: list
    policy: Policy = field(default_factory=Policy)

    def run(self):
        """Launch / watch / classify / relaunch loop. Return the supervisor's exit status."""
        raise NotImplementedError("Supervisor.run")


def main(argv=None):
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
