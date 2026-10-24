#!/usr/bin/env python3
"""Restart supervisor — TO WRITE (milestone 3).

usage: supervisor.py --workdir W [--max-restarts 5] [--stall-timeout 30] [--startup-grace 60] -- CMD ...

Requirements (see the tests in tests/test_resume.py):
  * relaunch CMD when it exits non-zero, up to --max-restarts times, then return 1;
  * treat CMD as stalled when W/heartbeat has not been touched for --stall-timeout seconds
    (--startup-grace before the first heartbeat of an attempt): kill its whole process group;
  * on SIGTERM, forward it to the child group, do not restart, exit with 143;
  * append one JSON line per event to W/supervisor.jsonl, with an "event" field in
    launch, stall_kill, crash, success, giving_up, terminated (launch lines carry the child "pid").
"""
import sys


def main():
    raise NotImplementedError("write the supervisor")


if __name__ == "__main__":
    sys.exit(main())
