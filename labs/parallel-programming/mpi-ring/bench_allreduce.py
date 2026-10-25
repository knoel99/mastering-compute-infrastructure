#!/usr/bin/env python3
"""Time ping-pong and all-reduce for a range of message sizes (shared-memory MPI on one machine).

usage: mpirun -np P python3 bench_allreduce.py OUT.json [--max-exp 22] [--label NAME]
Rows: ("pingpong", n) = one-way time between ranks 0 and 1 (half a round trip), other ranks idle;
      ("exchange", n) = all ranks swap n bytes with their neighbour r^1 simultaneously (one ring step);
      ("pyloop", n) = the ring algorithm with a communicator that moves nothing (cost of the Python code alone);
      ("ring" | "recdbl" | "mpi", n) = all-reduce of n bytes of float64, time of the slowest rank.
The "mpi" row is whatever MPI_Allreduce does in this installation; force an algorithm from the
command line with  --mca coll_tuned_use_dynamic_rules 1 --mca coll_tuned_allreduce_algorithm K
(Open MPI 4.1: 3 recursive doubling, 4 ring, 6 Rabenseifner) and pass --label to tell runs apart.
Timing method: warm-up, barrier, `inner` back-to-back calls, median over repeats.
"""
import argparse
import json
import os
import time

import numpy as np
from mpi4py import MPI

from ringlib import recursive_doubling_allreduce, ring_allreduce

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--max-exp", type=int, default=22)  # largest message: 2**22 bytes = 4 MiB
ap.add_argument("--label", default="default")
args = ap.parse_args()

comm = MPI.COMM_WORLD
p, r = comm.Get_size(), comm.Get_rank()
sizes = [2 ** e for e in range(3, args.max_exp + 1, 3)]  # 8 B, 64 B, 512 B, 4 KiB, 32 KiB, 256 KiB, 2 MiB
rows = []
load_start = os.getloadavg()[0]  # 1-minute load average: a shared machine makes timings meaningless


def timed(fn, inner, repeats):
    fn()  # warm-up
    samples = []
    for _ in range(repeats):
        comm.Barrier()
        t0 = time.perf_counter()
        for _ in range(inner):
            fn()
        dt = (time.perf_counter() - t0) / inner
        samples.append(comm.allreduce(dt, op=MPI.MAX))
    return float(np.median(samples))


class NullComm:
    """Same interface as the communicator, but Sendrecv moves nothing: times the Python side of the ring only."""

    def __init__(self, p, r):
        self.p, self.r = p, r

    def Get_size(self):
        return self.p

    def Get_rank(self):
        return self.r

    def Sendrecv(self, *a, **k):
        pass


for nbytes in sizes:
    inner, repeats = (50, 7) if nbytes <= 2 ** 15 else (5, 7)
    n = max(nbytes // 8, 1)
    x = np.ones(n)
    if p >= 2:
        buf = np.zeros(nbytes, dtype=np.uint8)

        def pingpong():
            if r == 0:
                comm.Send(buf, dest=1, tag=1)
                comm.Recv(buf, source=1, tag=2)
            elif r == 1:
                comm.Recv(buf, source=0, tag=1)
                comm.Send(buf, dest=0, tag=2)
        rows.append(("pingpong", nbytes, timed(pingpong, inner, repeats) / 2))
    # "exchange": every rank swaps nbytes with its neighbour r^1 at the same time (what one ring step does)
    partner = r ^ 1 if (r ^ 1) < p else MPI.PROC_NULL
    sb, rb = np.zeros(nbytes, dtype=np.uint8), np.zeros(nbytes, dtype=np.uint8)
    rows.append(("exchange", nbytes, timed(lambda: comm.Sendrecv(sb, dest=partner, recvbuf=rb, source=partner), inner, repeats)))
    null = NullComm(p, r)
    rows.append(("pyloop", nbytes, timed(lambda: ring_allreduce(null, x.copy()), inner, repeats)))
    rows.append(("ring", nbytes, timed(lambda: ring_allreduce(comm, x.copy()), inner, repeats)))
    if p & (p - 1) == 0:
        rows.append(("recdbl", nbytes, timed(lambda: recursive_doubling_allreduce(comm, x.copy()), inner, repeats)))
    y = np.empty_like(x)
    rows.append(("mpi", nbytes, timed(lambda: comm.Allreduce(x, y, op=MPI.SUM), inner, repeats)))

if r == 0:
    json.dump({"p": p, "label": args.label, "loadavg_start": load_start, "loadavg_end": os.getloadavg()[0], "rows": [{"kind": k, "bytes": b, "seconds": t} for k, b, t in rows]},
              open(args.out, "w"), indent=1)
    print(f"wrote {len(rows)} rows for p={p} label={args.label}")
