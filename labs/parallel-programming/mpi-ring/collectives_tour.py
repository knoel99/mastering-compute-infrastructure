#!/usr/bin/env python3
"""One call of each main collective on 4 ranks, with the data layout printed.

usage: mpirun -np 4 python3 collectives_tour.py
Rank r starts with the 4 integers [10 r, 10 r + 1, 10 r + 2, 10 r + 3] (r = 0..3).
Every result is checked against the definition of the operation.
"""
import numpy as np
from mpi4py import MPI

comm = MPI.COMM_WORLD
p, r = comm.Get_size(), comm.Get_rank()
assert p == 4, "this tour is written for exactly 4 ranks"
x = (10 * r + np.arange(4)).astype(np.int64)
lines = []


def show(name, arrays):
    """Rank 0 prints what every rank holds after the call (identical results are printed once)."""
    if r == 0:
        rows = [a.tolist() for a in arrays]
        if all(row == rows[0] for row in rows):
            lines.append(f"{name:15s} every rank: {rows[0]}")
        else:
            lines.append(f"{name:15s}" + " ".join(f"r{k}:{row}" for k, row in enumerate(rows)))


show("input", comm.gather(x, root=0) or [])

b = comm.bcast(x if r == 0 else None, root=0)
show("bcast(root=0)", comm.gather(b, root=0) or [])

red = np.full(4, -1, dtype=np.int64)
comm.Reduce(x, red, op=MPI.SUM, root=0)
show("reduce(root=0)", comm.gather(red if r == 0 else np.full(4, -1, dtype=np.int64), root=0) or [])  # -1 = untouched

allr = np.empty(4, dtype=np.int64)
comm.Allreduce(x, allr, op=MPI.SUM)
show("allreduce", comm.gather(allr, root=0) or [])
assert (allr == sum(10 * k + np.arange(4) for k in range(4))).all()

rs = np.empty(1, dtype=np.int64)
comm.Reduce_scatter_block(x, rs, op=MPI.SUM)
show("reduce_scatter", comm.gather(rs, root=0) or [])
assert rs[0] == allr[r]  # reduce-scatter = allreduce, keeping only block r

ag = np.empty(16, dtype=np.int64)
comm.Allgather(x, ag)
show("allgather", comm.gather(ag, root=0) or [])
assert (ag == np.concatenate([10 * k + np.arange(4) for k in range(4)])).all()

a2a = np.empty(4, dtype=np.int64)
comm.Alltoall(x, a2a)
show("alltoall", comm.gather(a2a, root=0) or [])
assert (a2a == np.array([10 * k + r for k in range(4)])).all()  # transpose of the 4x4 matrix

# reduce-scatter followed by allgather IS an allreduce (the ring algorithm's two phases)
rs_ag = np.empty(4, dtype=np.int64)
comm.Allgather(rs, rs_ag)
assert (rs_ag == allr).all()
if r == 0:
    print("\n".join(lines))
    print("OK collectives: allreduce == reduce_scatter + allgather; alltoall == transpose")
