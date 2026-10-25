#!/usr/bin/env python3
"""Two ranks exchange a buffer. Which versions deadlock?

usage: mpirun -np 2 python3 deadlock_demo.py MODE NBYTES
  MODE send_send   both ranks call Send, then Recv       (unsafe: relies on buffering)
       ssend_ssend both ranks call Ssend, then Recv       (synchronous: never completes)
       recv_send   rank 0 receives first, rank 1 sends    (ordered: always safe)
       sendrecv    both ranks call Sendrecv               (safe)
       isend_recv  both ranks Isend, Recv, Wait           (safe)
Prints "rank R done" when a rank gets through. A deadlocked run never prints and
must be stopped from outside (verify.sh uses timeout).
"""
import sys

import numpy as np
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank, size = comm.Get_rank(), comm.Get_size()
if size != 2:
    sys.exit("run with exactly 2 ranks")
mode, nbytes = sys.argv[1], int(sys.argv[2])
other = 1 - rank
out = np.full(nbytes, rank, dtype=np.uint8)
inp = np.empty(nbytes, dtype=np.uint8)

if mode == "send_send":
    comm.Send(out, dest=other, tag=7)
    comm.Recv(inp, source=other, tag=7)
elif mode == "ssend_ssend":
    comm.Ssend(out, dest=other, tag=7)
    comm.Recv(inp, source=other, tag=7)
elif mode == "recv_send":
    if rank == 0:
        comm.Recv(inp, source=other, tag=7)
        comm.Send(out, dest=other, tag=7)
    else:
        comm.Send(out, dest=other, tag=7)
        comm.Recv(inp, source=other, tag=7)
elif mode == "sendrecv":
    comm.Sendrecv(out, dest=other, sendtag=7, recvbuf=inp, source=other, recvtag=7)
elif mode == "isend_recv":
    req = comm.Isend(out, dest=other, tag=7)
    comm.Recv(inp, source=other, tag=7)
    req.Wait()
else:
    sys.exit(f"unknown mode {mode}")
assert (inp == other).all()
print(f"rank {rank} done ({mode}, {nbytes} bytes)", flush=True)
