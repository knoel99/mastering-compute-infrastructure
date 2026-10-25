#!/usr/bin/env python3
"""1-D three-point stencil with ghost cells ("halos"), two exchange styles.

usage: mpirun -np P python3 halo_stencil.py [N] [STEPS]
  u_new[i] = (u[i-1] + u[i] + u[i+1]) / 3 on a line of N points, u fixed to 1.0 at the left
  end and 0.0 at the right end. Each rank owns a contiguous block plus one ghost cell on
  each side. Two versions:
    blocking  : exchange the ghost cells with Sendrecv, then update every point;
    overlap   : post Irecv/Isend for the ghosts, update the points that need no ghost,
                wait, then update the two edge points.
Both must reproduce the serial result BIT FOR BIT: every point is computed by the same
floating-point expression in the same order, whatever the decomposition.
The bytes sent per step and per rank are counted and checked: 2 ghosts * 8 bytes inside, 8 bytes at an end.
"""
import sys

import numpy as np
from mpi4py import MPI

from ringlib import chunk_bounds

comm = MPI.COMM_WORLD
p, r = comm.Get_size(), comm.Get_rank()
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
steps = int(sys.argv[2]) if len(sys.argv) > 2 else 50
LEFT_BC, RIGHT_BC = 1.0, 0.0


def serial(n, steps):
    u = np.zeros(n + 2)
    u[0], u[-1] = LEFT_BC, RIGHT_BC
    for _ in range(steps):
        u[1:-1] = (u[:-2] + u[1:-1] + u[2:]) / 3.0
    return u[1:-1].copy()


def parallel(style):
    b = chunk_bounds(n, p)
    m = int(b[r + 1] - b[r])
    u = np.zeros(m + 2)  # u[0] and u[m+1] are ghost cells
    left = r - 1 if r > 0 else MPI.PROC_NULL
    right = r + 1 if r < p - 1 else MPI.PROC_NULL
    if r == 0:
        u[0] = LEFT_BC
    if r == p - 1:
        u[-1] = RIGHT_BC
    sent = 0
    new = u.copy()
    for _ in range(steps):
        if style == "blocking":
            comm.Sendrecv(u[1:2], dest=left, recvbuf=u[m + 1:m + 2], source=right)
            comm.Sendrecv(u[m:m + 1], dest=right, recvbuf=u[0:1], source=left)
            new[1:-1] = (u[:-2] + u[1:-1] + u[2:]) / 3.0
        else:
            reqs = [comm.Irecv(u[0:1], source=left), comm.Irecv(u[m + 1:m + 2], source=right),
                    comm.Isend(u[1:2], dest=left), comm.Isend(u[m:m + 1], dest=right)]
            if m > 2:  # interior points 2..m-1 need no ghost
                new[2:m] = (u[1:m - 1] + u[2:m] + u[3:m + 1]) / 3.0
            MPI.Request.Waitall(reqs)
            new[1] = (u[0] + u[1] + u[2]) / 3.0
            if m > 1:
                new[m] = (u[m - 1] + u[m] + u[m + 1]) / 3.0
        sent += 8 * ((left != MPI.PROC_NULL) + (right != MPI.PROC_NULL))
        u, new = new, u
        if r == 0:
            u[0] = LEFT_BC
        if r == p - 1:
            u[-1] = RIGHT_BC
    return u[1:-1].copy(), sent


ref = serial(n, steps)
for style in ("blocking", "overlap"):
    mine, sent = parallel(style)
    parts = comm.gather(mine, root=0)
    sents = comm.gather(sent, root=0)
    if r == 0:
        full = np.concatenate(parts)
        diff = float(np.max(np.abs(full - ref)))
        assert diff == 0.0, f"{style}: differs from serial by {diff}"
        expect = [steps * 8 * ((k > 0) + (k < p - 1)) for k in range(p)]
        assert sents == expect, (sents, expect)
        print(f"{style:9s} p={p} n={n} steps={steps}: bitwise equal to serial; bytes sent per rank = {sents}")
if r == 0:
    print("OK halo p=%d" % p)
