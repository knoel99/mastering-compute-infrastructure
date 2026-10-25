#!/usr/bin/env python3
"""Lab 8.3: what does a checkpoint cost, and what part of it blocks training?

Part A  real disk: buffered / fsync+rename / O_DIRECT write time per size, snapshot copy time, alpha-beta fit.
Part B  SIMULATED training loop (GPU step = sleep) on a SIMULATED slower storage (throttled writer):
        measured overhead of sync vs async checkpoints against the model prediction.
Part C  writers in parallel (one file per writer): aggregate bandwidth on this single virtual disk.
Part D  informational: first copy into a newly allocated buffer versus the second copy into the same buffer.

Usage: python3 bench_ckpt.py [--sizes 16,64,128] [--repeat 5] [--out result.json]
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import shutil
import statistics as st
import tempfile
import time

import numpy as np

import ckpt_io as c


def timed(fn, *a, **k) -> float:
    t = time.perf_counter()
    fn(*a, **k)
    return time.perf_counter() - t


def median_time(fn, repeat: int, *a, **k) -> float:
    fn(*a, **k)  # warm-up: first-touch of page-cache memory is slow on a fresh VM
    return st.median(timed(fn, *a, **k) for _ in range(repeat))


def part_a(workdir: str, sizes_mib: list[int], repeat: int) -> dict:
    rows = []
    for mib in sizes_mib:
        state = c.make_state(mib * c.MIB, seed=mib)
        path = os.path.join(workdir, "a.bin")
        io0 = c.proc_io()
        t_atomic = median_time(c.write_atomic, repeat, path, state)
        io1 = c.proc_io()
        n_calls = repeat + 1
        stage = np.zeros(len(state), dtype=np.uint8)  # touched once, as the async checkpointer does
        rows.append({
            "size_mib": mib,
            "buffered_s": median_time(c.write_buffered, repeat, path, state),
            "atomic_s": t_atomic,
            "direct_s": median_time(c.write_direct, repeat, path, state),
            "snapshot_s": median_time(np.copyto, repeat, stage, state),
            "write_bytes_per_call_over_size": (io1["write_bytes"] - io0["write_bytes"]) / n_calls / (mib * c.MIB),
        })
        c.write_atomic(path, state)
        rows[-1]["roundtrip_ok"] = c.read_back_equal(path, state)
        os.unlink(path)
    sizes = [r["size_mib"] * c.MIB for r in rows]
    alpha, bw = c.fit_alpha_beta(sizes, [r["atomic_s"] for r in rows])
    err = c.median_rel_error(sizes, [r["atomic_s"] for r in rows], alpha, bw)
    # leave-one-out: fit without the largest size, predict it
    a2, b2 = c.fit_alpha_beta(sizes[:-1], [r["atomic_s"] for r in rows[:-1]])
    loo = abs(c.predict(a2, b2, sizes[-1]) - rows[-1]["atomic_s"]) / rows[-1]["atomic_s"]
    return {"rows": rows, "alpha_s": alpha, "B_bytes_per_s": bw, "median_rel_error": err, "leave_one_out_error": loo}


def part_b(workdir: str, size_mib: int, throttle_mbps: float, step_s: float, intervals: list[int]) -> dict:
    state = c.make_state(size_mib * c.MIB, seed=1)
    probe = os.path.join(workdir, "probe.bin")
    t_p = median_time(c.write_atomic, 3, probe, state, throttle_mbps=throttle_mbps)  # calibrate the persistence time
    ck = c.AsyncCheckpointer(workdir)
    ck.prepare(len(state))
    snap = median_time(np.copyto, 5, ck._stage, state)
    out = {"size_mib": size_mib, "throttle_mbps": throttle_mbps, "step_s": step_s, "persist_s": t_p,
           "snapshot_s": snap, "cases": []}
    for every in intervals:
        n_steps = max(3 * every, 40)
        n_steps -= n_steps % every
        interval = every * step_s
        pred_sync = t_p / interval
        pred_async = (snap + max(0.0, t_p - interval)) / interval
        row = {"every": every, "interval_s": interval, "pred_sync": pred_sync, "pred_async": pred_async}
        for mode in ("sync", "async"):
            r = c.simulate_training(n_steps, step_s, every, mode, state, workdir, throttle_mbps)
            row[mode] = r["overhead"]
        out["cases"].append(row)
    return out


def _writer(path: str, mib: int, seed: int, barrier, queue) -> None:
    state = c.make_state(mib * c.MIB, seed=seed)
    barrier.wait()
    t = time.perf_counter()
    c.write_atomic(path, state)
    queue.put(time.perf_counter() - t)


def part_c(workdir: str, total_mib: int, writers: list[int], repeat: int) -> dict:
    rows = []
    ctx = mp.get_context("fork")
    for n in writers:
        walls = []
        for _ in range(repeat + 2):
            for i in range(8):  # free the previous round's files: their pages become available again
                if os.path.exists(os.path.join(workdir, f"w{i}.bin")):
                    os.unlink(os.path.join(workdir, f"w{i}.bin"))
            barrier, queue = ctx.Barrier(n), ctx.Queue()
            procs = [ctx.Process(target=_writer, args=(os.path.join(workdir, f"w{i}.bin"), total_mib // n, i, barrier, queue))
                     for i in range(n)]
            for p in procs:
                p.start()
            times = [queue.get() for _ in procs]  # each writer times itself from the barrier to the end of its write
            for p in procs:
                p.join()
            walls.append(max(times))
        wall = st.median(walls[2:])  # the first two runs are warm-ups
        rows.append({"writers": n, "wall_s": wall, "aggregate_mib_s": total_mib / wall})
    return {"total_mib": total_mib, "rows": rows}


def part_d(mib: int = 256) -> dict:
    """The snapshot copy into a buffer that was never touched, then again into the same buffer.

    The size of the gap depends on the state of this machine's memory (page faults, and on a VM possibly the
    host backing the memory lazily); it is printed, not asserted.
    """
    src = c.make_state(mib * c.MIB, seed=2)
    dst = np.empty(len(src), dtype=np.uint8)
    first = timed(np.copyto, dst, src)
    second = timed(np.copyto, dst, src)
    return {"size_mib": mib, "first_copy_s": first, "second_copy_s": second}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="16,64,128")
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--dir", default=None, help="directory on the file system to test (default: a temp dir)")
    ap.add_argument("--throttle-mbps", type=float, default=200.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    sizes = [int(x) for x in args.sizes.split(",")]
    workdir = tempfile.mkdtemp(prefix="ckpt-io-", dir=args.dir)
    try:
        a = part_a(workdir, sizes, args.repeat)
        print("Part A - real disk, median of %d runs (MiB, ms)" % args.repeat)
        print("%8s %10s %10s %10s %10s" % ("size", "buffered", "fsync", "O_DIRECT", "snapshot"))
        for r in a["rows"]:
            print("%8d %10.1f %10.1f %10.1f %10.1f" % (r["size_mib"], 1e3 * r["buffered_s"], 1e3 * r["atomic_s"],
                                                       1e3 * r["direct_s"], 1e3 * r["snapshot_s"]))
        print("fit T = alpha + S/B on fsync: alpha = %.1f ms, B = %.0f MiB/s, median error %.0f %%, leave-one-out %.0f %%"
              % (1e3 * a["alpha_s"], a["B_bytes_per_s"] / c.MIB, 100 * a["median_rel_error"], 100 * a["leave_one_out_error"]))
        b = part_b(workdir, 32, args.throttle_mbps, 0.02, [10, 40])
        print("\nPart B - SIMULATED step (%.0f ms) and SIMULATED storage (%.0f MiB/s), state %d MiB, persist %.0f ms, snapshot %.0f ms"
              % (1e3 * b["step_s"], b["throttle_mbps"], b["size_mib"], 1e3 * b["persist_s"], 1e3 * b["snapshot_s"]))
        print("%12s %12s %12s %12s %12s" % ("every N steps", "sync meas.", "sync model", "async meas.", "async model"))
        for r in b["cases"]:
            print("%12d %11.1f%% %11.1f%% %11.1f%% %11.1f%%" % (r["every"], 100 * r["sync"], 100 * r["pred_sync"],
                                                               100 * r["async"], 100 * r["pred_async"]))
        cres = part_c(workdir, 128, [1, 2, 4], 3)
        print("\nPart C - parallel writers, one file each, %d MiB in total (single virtual disk)" % cres["total_mib"])
        for r in cres["rows"]:
            print("%8d writers  wall %6.0f ms  aggregate %6.0f MiB/s" % (r["writers"], 1e3 * r["wall_s"], r["aggregate_mib_s"]))
        d = part_d(256)
        print("\nPart D - informational: snapshot copy of %d MiB, first into a new buffer, then into the same one" % d["size_mib"])
        print("   first copy %6.0f ms   second copy %6.0f ms   ratio %.1f" % (
            1e3 * d["first_copy_s"], 1e3 * d["second_copy_s"], d["first_copy_s"] / d["second_copy_s"]))
        result = {"a": a, "b": b, "c": cres, "d": d}
        if args.out:
            with open(args.out, "w") as f:
                json.dump(result, f, indent=1)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
