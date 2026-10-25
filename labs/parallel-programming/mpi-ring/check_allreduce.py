#!/usr/bin/env python3
"""Check the hand-written all-reduces against MPI_Allreduce and against the cost formulas.

usage: mpirun -np P python3 check_allreduce.py [N]
Integers: results must be EXACTLY equal to comm.Allreduce. Floats: equal within rounding
(the order of the additions differs between algorithms). Counters: messages and bytes sent
by each rank must match the closed forms of the course.
"""
import sys

import numpy as np
from mpi4py import MPI

from ringlib import Counter, chunk_bounds, recursive_doubling_allreduce, ring_allreduce

comm = MPI.COMM_WORLD
p, r = comm.Get_size(), comm.Get_rank()
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
rng = np.random.default_rng(1234 + r)  # a different, reproducible vector on every rank

xi = rng.integers(-1000, 1000, size=n).astype(np.int64)
ref_i = np.empty_like(xi)
comm.Allreduce(xi, ref_i, op=MPI.SUM)
mine = xi.copy()
c = Counter()
ring_allreduce(comm, mine, c)
assert np.array_equal(mine, ref_i), "ring result differs from MPI_Allreduce on integers"

b = chunk_bounds(n, p)
expected_msgs = 2 * (p - 1)
# bytes sent: every chunk but one is sent once per phase; which chunk is skipped depends on r
sent = 0
for s in range(p - 1):
    sent += b[(r - s) % p + 1] - b[(r - s) % p]
    sent += b[(r + 1 - s) % p + 1] - b[(r + 1 - s) % p]
assert c.msgs == expected_msgs and c.nbytes == sent * xi.itemsize, (c.msgs, c.nbytes, expected_msgs, sent)
if n % p == 0:  # the closed form of the course: 2 (p-1)/p * n elements
    assert c.nbytes == 2 * (p - 1) * (n // p) * xi.itemsize

xf = rng.standard_normal(n)
ref_f = np.empty_like(xf)
comm.Allreduce(xf, ref_f, op=MPI.SUM)
mine_f = xf.copy()
ring_allreduce(comm, mine_f)
assert np.allclose(mine_f, ref_f, rtol=1e-12, atol=1e-12)
float_diff = float(np.max(np.abs(mine_f - ref_f)))

rd_msgs = rd_bytes = -1
if p & (p - 1) == 0:
    mine = xi.copy()
    c2 = Counter()
    recursive_doubling_allreduce(comm, mine, c2)
    assert np.array_equal(mine, ref_i)
    assert c2.msgs == int(np.log2(p)) and c2.nbytes == int(np.log2(p)) * xi.nbytes
    rd_msgs, rd_bytes = c2.msgs, c2.nbytes

rows = comm.gather((r, c.msgs, c.nbytes, rd_msgs, rd_bytes), root=0)
maxdiff = comm.reduce(float_diff, op=MPI.MAX, root=0)
if r == 0:
    print(f"p={p} n={n} int64: ring == MPI_Allreduce exactly; float64: max|ring - MPI_Allreduce| = {maxdiff:.1e}")
    print(f"  ring per rank: {rows[0][1]} messages, {rows[0][2]} bytes (2(p-1)/p*n*8 = {2 * (p - 1) * n * 8 // p} bytes)")
    if rd_msgs >= 0:
        print(f"  recursive doubling per rank: {rows[0][3]} messages, {rows[0][4]} bytes (log2(p)*n*8 = {int(np.log2(p)) * n * 8})")
    print("OK allreduce p=%d" % p)
