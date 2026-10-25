"""Rank arithmetic of an N-D parallelism grid (pure Python).

Dimensions are listed from the OUTERMOST to the INNERMOST, as in a PyTorch DeviceMesh shape: the last
dimension varies fastest with the global rank. Llama 3 orders its groups [TP, CP, PP, DP] (TP innermost),
which in this notation is names=("dp", "pp", "cp", "tp"). Keeping tensor parallelism innermost puts its
ranks on neighbouring GPUs, i.e. inside one node when tp <= GPUs per node.
"""
import math


class Mesh:
    def __init__(self, names, sizes):
        if len(names) != len(sizes) or len(set(names)) != len(names):
            raise ValueError("names and sizes must have the same length, names must be distinct")
        self.names, self.sizes = tuple(names), tuple(sizes)
        self.world = math.prod(self.sizes)
        self.strides = tuple(math.prod(self.sizes[i + 1:]) for i in range(len(self.sizes)))

    def coords(self, rank):
        """Coordinates of a global rank, one per dimension (outermost first)."""
        if not 0 <= rank < self.world:
            raise ValueError("rank out of range")
        return tuple((rank // st) % sz for st, sz in zip(self.strides, self.sizes))

    def rank(self, **coords):
        return sum(coords[n] * st for n, st in zip(self.names, self.strides))

    def group(self, rank, name):
        """Global ranks that share every coordinate with `rank` except along dimension `name`."""
        i, c = self.names.index(name), list(self.coords(rank))
        out = []
        for k in range(self.sizes[i]):
            c[i] = k
            out.append(sum(x * st for x, st in zip(c, self.strides)))
        return out

    def node_span(self, name, gpus_per_node):
        """Number of distinct nodes touched by the group of dimension `name` that contains rank 0."""
        return len({r // gpus_per_node for r in self.group(0, name)})
