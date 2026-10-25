"""The snippet of example 1.2 of the course: coordinates and groups of rank 5 in a 16-GPU grid (Llama 3, figure 5)."""
from mesh import Mesh

m = Mesh(("dp", "pp", "cp", "tp"), (2, 2, 2, 2))
print("rank 5 coords (dp, pp, cp, tp):", m.coords(5))
for name in m.names:
    print(f"group {name}:", m.group(5, name))
