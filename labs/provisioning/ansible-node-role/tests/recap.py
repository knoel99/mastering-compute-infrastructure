#!/usr/bin/env python3
"""Parse the PLAY RECAP of an ansible-playbook run and assert on the counters.

Usage: recap.py LOGFILE changed>0 | changed=0 | failed>0 | ok     (applies to every host in the recap)
Counters are read from the real output: nothing here depends on wall-clock time.
"""
import re
import sys

RECAP = re.compile(r"^(?P<host>\S+)\s*:\s*ok=(?P<ok>\d+)\s+changed=(?P<changed>\d+)\s+unreachable=(?P<unreachable>\d+)\s+failed=(?P<failed>\d+)")


def parse(text):
    hosts = {}
    for line in text.splitlines():
        m = RECAP.match(line.strip())
        if m:
            hosts[m["host"]] = {k: int(m[k]) for k in ("ok", "changed", "unreachable", "failed")}
    return hosts


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    hosts = parse(open(argv[1], encoding="utf-8").read())
    if not hosts:
        print("FAIL: no PLAY RECAP found")
        return 1
    rule = argv[2]
    bad = []
    for h, c in sorted(hosts.items()):
        if rule == "changed>0":
            ok = c["changed"] > 0 and c["failed"] == 0 and c["unreachable"] == 0
        elif rule == "changed=0":
            ok = c["changed"] == 0 and c["failed"] == 0 and c["unreachable"] == 0
        elif rule == "failed>0":
            ok = c["failed"] > 0
        elif rule == "ok":
            ok = c["failed"] == 0 and c["unreachable"] == 0
        else:
            print(f"unknown rule {rule}")
            return 2
        if not ok:
            bad.append(h)
    summary = ", ".join(f"{h}: changed={c['changed']} failed={c['failed']}" for h, c in sorted(hosts.items()))
    print(f"recap [{rule}] {summary}")
    if bad:
        print(f"FAIL: rule {rule} violated on {', '.join(bad)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
