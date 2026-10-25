#!/usr/bin/env python3
"""Every rank passes a buffer to its right neighbour and receives one from its left neighbour.

usage: mpirun -np P python3 ring_shift.py MODE NBYTES
  send_recv : Send to the right, then Recv from the left, on every rank        (BUGGY for large NBYTES)
  ssend_recv: the same with Ssend (the "Ssend test": blocks at ANY size if the program relies on buffering)
  parity    : even ranks Send then Recv, odd ranks Recv then Send               (the odd ranks break the cycle)
  sendrecv  : one Sendrecv call                                                 (safe)
  isend     : Isend, Recv, Wait                                                 (safe)
Exit code 0 and one "ok" line per rank when the shift completed.
"""
import sys

import numpy as np
from mpi4py import MPI

comm = MPI.COMM_WORLD
r, p = comm.Get_rank(), comm.Get_size()
mode, nbytes = sys.argv[1], int(sys.argv[2])
right, left = (r + 1) % p, (r - 1) % p
out = np.full(nbytes, r, dtype=np.uint8)
inp = np.empty(nbytes, dtype=np.uint8)
if mode == "send_recv":
    comm.Send(out, dest=right, tag=0)
    comm.Recv(inp, source=left, tag=0)
elif mode == "ssend_recv":
    comm.Ssend(out, dest=right, tag=0)
    comm.Recv(inp, source=left, tag=0)
elif mode == "parity":
    if r % 2 == 0:
        comm.Send(out, dest=right, tag=0)
        comm.Recv(inp, source=left, tag=0)
    else:
        comm.Recv(inp, source=left, tag=0)
        comm.Send(out, dest=right, tag=0)
elif mode == "sendrecv":
    comm.Sendrecv(out, dest=right, sendtag=0, recvbuf=inp, source=left, recvtag=0)
elif mode == "isend":
    req = comm.Isend(out, dest=right, tag=0)
    comm.Recv(inp, source=left, tag=0)
    req.Wait()
else:
    sys.exit("unknown mode")
assert (inp == left).all()
print(f"rank {r}: ok ({mode}, {nbytes} bytes)", flush=True)
