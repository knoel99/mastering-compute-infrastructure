#!/usr/bin/env python3
"""Halo traffic of a Jacobi sweep for the 1-D and the 2-D decomposition.

usage: halo_sizing.py NX NY P [ALPHA_S BANDWIDTH_BPS]
Per sweep, summed over all ranks:   bytes = 16 * ((py-1)*NX + (px-1)*NY),
                                    messages = 2 * ((py-1)*px + (px-1)*py)
where py x px is the process grid (1-D: P x 1; 2-D: the most square factorisation, like MPI_Dims_create).
If ALPHA_S and BANDWIDTH_BPS are given, also prints the alpha-beta time of the busiest rank's exchange,
assuming its messages are sent one after the other (pessimistic).
"""
import sys


def grid2d(p):
    best = (p, 1)
    for a in range(1, p + 1):
        if p % a == 0 and a >= p // a and a - p // a < best[0] - best[1]:
            best = (a, p // a)
    return best


def traffic(nx, ny, py, px):
    return 16 * ((py - 1) * nx + (px - 1) * ny), 2 * ((py - 1) * px + (px - 1) * py)


def busiest_rank_bytes(nx, ny, py, px):
    """Largest number of halo bytes sent by one rank per sweep (an interior rank sends 4 sides, a 1-D one 2)."""
    lx, ly = -(-nx // px), -(-ny // py)
    sides_y = 2 if py > 2 else (1 if py == 2 else 0)
    sides_x = 2 if px > 2 else (1 if px == 2 else 0)
    return 8 * (sides_y * lx + sides_x * ly), sides_y + sides_x


if __name__ == "__main__":
    nx, ny, p = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    for name, (py, px) in (("1-D", (p, 1)), ("2-D", grid2d(p))):
        b, m = traffic(nx, ny, py, px)
        bb, mm = busiest_rank_bytes(nx, ny, py, px)
        line = f"{name} {py}x{px}: {b} bytes and {m} messages per sweep in total; busiest rank {bb} bytes in {mm} messages"
        if len(sys.argv) == 6:
            alpha, bw = float(sys.argv[4]), float(sys.argv[5])
            line += f"; alpha-beta time {(mm * alpha + bb / bw) * 1e6:.1f} us"
        print(line)
