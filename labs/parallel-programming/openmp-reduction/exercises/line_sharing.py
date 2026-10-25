#!/usr/bin/env python3
"""Which cache lines hold the data of more than one thread?

usage: line_sharing.py THREADS SLOT_BYTES [--line 64] [--used BYTES]
Thread t owns the bytes [t*SLOT, t*SLOT + USED) of an array whose start is aligned on a cache line
(USED defaults to SLOT). Prints the number of lines that contain bytes of two or more threads, and the
size of the slot once padded to a whole number of lines.
"""
import argparse


def shared_lines(threads, slot, used=None, line=64):
    used = slot if used is None else used
    owners = {}
    for t in range(threads):
        for ln in range(t * slot // line, (t * slot + used - 1) // line + 1):
            owners.setdefault(ln, set()).add(t)
    return sum(1 for v in owners.values() if len(v) > 1)


def padded(slot, line=64):
    return -(-slot // line) * line


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("threads", type=int)
    ap.add_argument("slot", type=int)
    ap.add_argument("--line", type=int, default=64)
    ap.add_argument("--used", type=int)
    a = ap.parse_args()
    s = shared_lines(a.threads, a.slot, a.used, a.line)
    print(f"{a.threads} threads, slot {a.slot} B, line {a.line} B: {s} shared line(s); padded slot = {padded(a.slot, a.line)} B")
