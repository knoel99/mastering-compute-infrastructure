#!/usr/bin/env python3
"""MPI-IO: every rank writes its own slab of ONE shared file; the file must not depend on the number of ranks.

usage: mpirun -np P python3 mpiio_demo.py OUTFILE [N]
The global array is f(i) = i*i + 7 for i in [0, N) as int64. Rank r owns the contiguous slab
[b[r], b[r+1]) and writes it at byte offset 8*b[r] with a COLLECTIVE call (Write_at_all: every rank of the
communicator must call it). Then rank 0 reads the file back with plain numpy and prints its SHA-256.
Checked: the file size is 8*N, the content is f, and the bytes written by the ranks add up to 8*N.
Nothing about speed is measured here: the page cache of the machine would decide the result.
"""
import hashlib
import sys

import numpy as np
from mpi4py import MPI

comm = MPI.COMM_WORLD
p, r = comm.Get_size(), comm.Get_rank()
path = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 100003  # not divisible by most p on purpose
base, extra = divmod(n, p)
sizes = [base + (1 if k < extra else 0) for k in range(p)]
lo = sum(sizes[:r])
mine = (np.arange(lo, lo + sizes[r], dtype=np.int64) ** 2 + 7)

fh = MPI.File.Open(comm, path, MPI.MODE_WRONLY | MPI.MODE_CREATE)
fh.Set_size(0)
fh.Write_at_all(8 * lo, mine)  # collective: the library may aggregate the requests before touching the disk
fh.Sync()
fh.Close()
written = comm.allreduce(mine.nbytes, op=MPI.SUM)
comm.Barrier()
if r == 0:
    data = np.fromfile(path, dtype=np.int64)
    expected = np.arange(n, dtype=np.int64) ** 2 + 7
    assert data.size == n and written == 8 * n and np.array_equal(data, expected)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print(f"p={p} n={n} bytes={written} slab sizes={sizes} sha256={digest[:16]}")
