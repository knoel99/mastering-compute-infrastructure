#!/usr/bin/env python3
"""Structural checks of the Jacobi lab; reads the lines written by verify.sh (one jacobi output line per file line).

1. the field is bit-identical for every p, decomposition, overlap mode and thread count (same checksum);
2. the halo traffic counters equal the closed forms of the course:
       messages per sweep = 2 ((py-1) px + (px-1) py)       bytes per sweep = 16 ((py-1) nx + (px-1) ny)
3. the max-norm residual is identical everywhere, the 2-norm residual agrees to rounding but not bit for bit.
No wall-clock time is asserted.
"""
import sys


def parse(line):
    d = {}
    for kv in line.split():
        k, v = kv.split("=", 1)
        try:
            d[k] = int(v)
        except ValueError:
            try:
                d[k] = float(v)
            except ValueError:
                d[k] = v
    return d


def main(path):
    rows = [parse(l) for l in open(path) if l.startswith("p=")]
    ref = [r for r in rows if r["nx"] == 200 and r["skip_sweep"] == 0]
    assert len(ref) >= 9, len(ref)
    sums = {r["checksum"] for r in ref}
    assert len(sums) == 1, f"field differs between runs: {sums}"
    assert len({r["res_max"] for r in ref}) == 1, "max-norm residual must not depend on the decomposition"
    l2 = [r["res_l2"] for r in ref]
    spread = (max(l2) - min(l2)) / max(l2)
    assert spread < 1e-9, spread
    print(f"OK reproducibility: {len(ref)} runs (p=1..4, 1-D and 2-D, overlap, 2 threads) share checksum {sums.pop()}; "
          f"2-norm residual takes {len(set(l2))} distinct values, relative spread {spread:.1e}")
    for r in ref[:4] + ref[-1:]:
        print(f"  p={r['p']} threads={r['threads']} decomp={r['decomp']} overlap={r['overlap']} checksum={r['checksum']} "
              f"res_max={r['res_max']:.17g} res_l2={r['res_l2']:.17g}")
    for r in rows:
        py, px, nx, ny, it = r["py"], r["px"], r["nx"], r["ny"], r["iters"]
        assert r["msgs_total"] == it * 2 * ((py - 1) * px + (px - 1) * py), r
        assert r["bytes_total"] == it * 16 * ((py - 1) * nx + (px - 1) * ny), r
    sq = {(r["decomp"], r["p"]): r["bytes_total"] // r["iters"] for r in rows if r["nx"] == 96}
    print("OK halo counters match 16((py-1)nx+(px-1)ny) on", len(rows), "runs; bytes per sweep on a 96x96 grid:",
          ", ".join(f"{k[0]} p={k[1]}: {v}" for k, v in sorted(sq.items(), key=lambda kv: (kv[0][0], kv[0][1]))))


if __name__ == "__main__":
    main(sys.argv[1])
