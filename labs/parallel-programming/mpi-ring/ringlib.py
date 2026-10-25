"""Hand-written all-reduce algorithms on top of point-to-point MPI (mpi4py).

Two algorithms, both summing a 1-D numpy array in place on every rank:
  ring_allreduce               reduce-scatter then all-gather on a ring (any number of ranks)
  recursive_doubling_allreduce log2(p) pairwise exchanges of the whole vector (p a power of two)
A Counter records the messages and bytes THIS rank sends, so that the cost
formulas of the course can be checked by counting instead of by timing.
"""
import numpy as np
from mpi4py import MPI


class Counter:
    """Messages and bytes sent by this rank."""

    def __init__(self):
        self.msgs = 0
        self.nbytes = 0

    def add(self, buf):
        self.msgs += 1
        self.nbytes += buf.nbytes


def chunk_bounds(n, p):
    """p chunks covering [0, n); sizes differ by at most one element."""
    base, extra = divmod(n, p)
    sizes = [base + (1 if c < extra else 0) for c in range(p)]
    return np.concatenate(([0], np.cumsum(sizes))).astype(int)


def ring_allreduce(comm, x, counter=None):
    """Sum-all-reduce x in place. 2(p-1) steps; each rank sends about n/p elements per step."""
    p, r = comm.Get_size(), comm.Get_rank()
    if p == 1:
        return
    b = chunk_bounds(x.size, p)
    right, left = (r + 1) % p, (r - 1) % p
    tmp = np.empty(int(np.diff(b).max()), dtype=x.dtype)
    # Phase 1, reduce-scatter. Step s: send chunk (r - s), receive chunk (r - s - 1) and add it.
    for s in range(p - 1):
        cs, cr = (r - s) % p, (r - s - 1) % p
        send = x[b[cs]:b[cs + 1]]
        recv = tmp[:b[cr + 1] - b[cr]]
        comm.Sendrecv(send, dest=right, recvbuf=recv, source=left)
        x[b[cr]:b[cr + 1]] += recv
        if counter:
            counter.add(send)
    # Rank r now owns the fully reduced chunk (r + 1) mod p.
    # Phase 2, all-gather. Step s: send chunk (r + 1 - s), receive chunk (r - s) and keep it.
    for s in range(p - 1):
        cs, cr = (r + 1 - s) % p, (r - s) % p
        send = x[b[cs]:b[cs + 1]]
        comm.Sendrecv(send, dest=right, recvbuf=x[b[cr]:b[cr + 1]], source=left)
        if counter:
            counter.add(send)


def recursive_doubling_allreduce(comm, x, counter=None):
    """Sum-all-reduce x in place with log2(p) exchanges of the whole vector (p must be a power of two)."""
    p, r = comm.Get_size(), comm.Get_rank()
    if p & (p - 1):
        raise ValueError("recursive doubling needs a power-of-two number of ranks")
    tmp = np.empty_like(x)
    dist = 1
    while dist < p:
        partner = r ^ dist
        comm.Sendrecv(x, dest=partner, recvbuf=tmp, source=partner)
        x += tmp
        if counter:
            counter.add(x)
        dist <<= 1
