#!/usr/bin/env python3
"""Floating-point addition is not associative: the same data, summed on p ranks, gives different bits.

usage: mpirun -np P python3 repro_sum.py [N] [BLOCK]
Data: N float64 values with a wide range of magnitudes, generated BLOCK values at a time from a seed that
depends on the block number only (so the data set is the same whatever P is).
  naive   : each rank sums its share with numpy, then MPI_Allreduce adds the P partial sums;
  blocked : the sum of every block is computed whole (independent of P), all block sums are gathered
            and added in block order on every rank: the result does not depend on P;
  exact   : math.fsum on rank 0, the correctly rounded sum, as the reference.
Prints one line per method with the result as a hexadecimal float and its error against the reference.
"""
import math
import sys

import numpy as np
from mpi4py import MPI

comm = MPI.COMM_WORLD
p, r = comm.Get_size(), comm.Get_rank()
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
block = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
assert n % block == 0
nblocks = n // block


def make_block(b):
    rng = np.random.default_rng([2024, b])  # seed = (2024, block number): independent of the number of ranks
    return rng.standard_normal(block) * 10.0 ** rng.integers(-6, 7, size=block)


per_rank = [nblocks // p + (1 if k < nblocks % p else 0) for k in range(p)]
first = sum(per_rank[:r])
mine_blocks = list(range(first, first + per_rank[r]))
data = [make_block(b) for b in mine_blocks]

naive = comm.allreduce(float(np.sum(np.concatenate(data))) if data else 0.0, op=MPI.SUM)

block_sums = np.array([float(np.sum(d)) for d in data])  # one number per block, whatever the layout
counts = comm.allgather(len(block_sums))
all_sums = np.concatenate(comm.allgather(block_sums))
assert all_sums.size == nblocks and sum(counts) == nblocks
blocked = 0.0
for s in all_sums:  # fixed order: block 0, 1, 2, ...
    blocked += float(s)

everything = comm.gather(data, root=0)
if r == 0:
    exact = math.fsum(float(v) for part in everything for d in part for v in d)
    print(f"p={p} exact={exact.hex()}")
    print(f"p={p} naive={naive.hex()} error={naive - exact:+.3e}")
    print(f"p={p} blocked={blocked.hex()} error={blocked - exact:+.3e}")
