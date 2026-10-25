#!/usr/bin/env python3
"""Structural checks for the OpenMP lab. Reads the key=value lines written by verify.sh.

Nothing here asserts a wall-clock time: the machine may be shared. The checks are
on results, on counts, and on the iteration-to-thread assignment, which the
OpenMP specification fixes for schedule(static[,chunk]).
"""
import sys
from pathlib import Path


def parse(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        if "=" in line and not line.startswith("owner="):
            rows.append(dict(kv.split("=", 1) for kv in line.split()))
        elif line.startswith("owner="):
            rows[-1]["owner"] = line.split("=", 1)[1]
    return rows


def main(d):
    d = Path(d)
    # 1. sums: every correct variant returns exactly the expected integer-valued sum
    for r in parse(d / "sums.txt"):
        if r["variant"] == "race":
            continue  # undefined behaviour: reported, never asserted
        assert r["wrong"] == "0" and r["result"] == r["expected"], f"sum variant {r['variant']} is wrong: {r}"
    race1 = [r for r in parse(d / "race1.txt")][0]
    assert race1["wrong"] == "0", "with one thread even the racy loop is correct"
    print("OK sums: 7 correct variants exact; racy loop exact with 1 thread")

    # 2. false sharing: same histogram everywhere; shared cache lines only in the packed layout
    fs = {r["layout"]: r for r in parse(d / "false_sharing.txt")}
    threads = int(fs["packed"]["threads"])
    assert all(r["histogram_ok"] == "1" for r in fs.values()), "histograms differ"
    expected_shared = len({ln for t in range(threads) for ln in range(t * 56 // 64, (t * 56 + 55) // 64 + 1)
                           if sum(1 for u in range(threads) if u * 56 // 64 <= ln <= (u * 56 + 55) // 64) > 1})
    assert int(fs["packed"]["shared_lines"]) == expected_shared > 0, (fs["packed"], expected_shared)
    assert fs["padded"]["shared_lines"] == "0" and fs["private"]["shared_lines"] == "0"
    print(f"OK false sharing: packed layout shares {expected_shared} cache lines with {threads} threads, padded and private share none")

    # 3. schedules: assignment fixed by the specification for static
    sched = {}
    for r in parse(d / "schedule.txt"):
        sched[(r["schedule"], r["chunk"], r["cost"], r["n"])] = r
    r = sched[("static", "0", "uniform", "64")]
    assert int(r["runs"]) == int(r["threads"]), "schedule(static): one contiguous block per thread"
    assert sorted(r["owner"].count(str(t)) for t in range(int(r["threads"]))) == [16] * 4
    r = sched[("static", "1", "uniform", "64")]
    assert r["owner"] == "0123" * 16, "schedule(static,1) is round-robin"
    r = sched[("static", "4", "uniform", "64")]
    assert r["owner"] == "".join(str((i // 4) % 4) for i in range(64)), "schedule(static,4) deals chunks of 4"
    for k in (("dynamic", "1"), ("dynamic", "8"), ("guided", "1")):
        r = sched[(k[0], k[1], "uniform", "64")]
        assert r["total_units"] == r["covered_units"], f"{k} must execute every iteration exactly once"
    tri_static = float(sched[("static", "0", "triangular", "2000")]["imbalance"])
    tri_cyclic = float(sched[("static", "1", "triangular", "2000")]["imbalance"])
    assert 1.74 <= tri_static <= 1.76, tri_static  # 875250 / 500250
    assert 1.0 <= tri_cyclic <= 1.01, tri_cyclic
    print(f"OK schedules: static blocks / round-robin verified; triangular loop imbalance {tri_static:.3f} (static) vs {tri_cyclic:.3f} (static,1)")

    # 4. tasks: result and task count match the sequential walk (the program exits non-zero otherwise)
    rows = parse(d / "tasks.txt")
    assert [r["tasks"] for r in rows] == [r["expected_tasks"] for r in rows]
    assert rows[0]["tasks"] == "0" and int(rows[-1]["tasks"]) > int(rows[1]["tasks"]) > 0
    print("OK tasks: tasks created =", ",".join(r["tasks"] for r in rows), "for cutoffs", ",".join(r["cutoff"] for r in rows))


if __name__ == "__main__":
    main(sys.argv[1])
