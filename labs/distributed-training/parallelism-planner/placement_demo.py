"""The snippet of example 5.1 of the course: how many nodes does each parallelism group span? (64 GPUs, 8 per node)"""
from mesh import Mesh

inner = Mesh(("dp", "pp", "tp"), (8, 2, 4))  # names from outermost to innermost
outer = Mesh(("tp", "pp", "dp"), (4, 2, 8))  # same degrees, tensor parallelism outermost
print(f"tp spans {inner.node_span('tp', 8)} node(s); dp spans {inner.node_span('dp', 8)} nodes")
print(f"same sizes, tp outermost: tp spans {outer.node_span('tp', 8)} nodes")
