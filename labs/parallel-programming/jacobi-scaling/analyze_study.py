#!/usr/bin/env python3
"""Turn study.json into the tables and the plot of a scaling report.

usage: python3 analyze_study.py study.json [--svg speedup.svg]
For every configuration: median time with a 95 % bootstrap interval of the median, speedup S = T1/Tp,
efficiency E = S/p (strong) or T1/Tp (weak), Karp-Flatt serial fraction e(p), and a decomposition of the
time of the slowest rank into compute / halo wait / residual all-reduce ("imb" = slowest / fastest rank compute time). "comm only" is the time of the
same exchanges without arithmetic (--skip-sweep): what is above it in the halo column is waiting
(load imbalance, jitter, interference), not data transfer.
Speedup, efficiency and Karp-Flatt come from the tested reference of the scaling-study project.
"""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np

REF = Path(__file__).resolve().parents[2] / "projects" / "scaling-study" / "reference" / "analysis.py"
spec = importlib.util.spec_from_file_location("scaling_analysis", REF)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def median_ci(xs, n_boot=2000, seed=0):
    """Median and 95 % percentile-bootstrap interval of the median (seeded: reproducible)."""
    x = np.asarray(xs, float)
    rng = np.random.default_rng(seed)
    boots = np.median(rng.choice(x, size=(n_boot, x.size), replace=True), axis=1)
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return float(np.median(x)), float(lo), float(hi)


def group(runs):
    g = {}
    for r in runs:
        g.setdefault((r["kind"], r["decomp"], r["p"]), []).append(r)
    return g


def med(rs, key):
    return float(np.median([r[key] for r in rs]))


def table(path):
    d = json.load(open(path))
    g = group(d["runs"])
    out = {"meta": d["meta"], "strong": [], "weak": []}
    t1 = {k: med(g[(k, "1d", 1)], "t_total") for k in ("strong", "weak")}
    for (kind, dec, p), rs in sorted(g.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
        if kind == "comm":
            continue
        m, lo, hi = median_ci([r["t_total"] for r in rs])
        row = dict(kind=kind, decomp=dec, p=p, reps=len(rs), t=m, lo=lo, hi=hi,
                   imbalance=float(np.median([r["t_comp"] / r["t_comp_min"] for r in rs])))
        if kind == "strong":
            s = analysis.speedup(t1["strong"], m)
            row.update(speedup=s, efficiency=analysis.efficiency(t1["strong"], m, p),
                       karp_flatt=analysis.karp_flatt(s, p) if p > 1 else None)
        else:
            row.update(efficiency=t1["weak"] / m)
        comm = g.get(("comm", dec, p))
        row.update(comp=med(rs, "t_comp"), halo=med(rs, "t_halo"), red=med(rs, "t_red"),
                   comm_only=med(comm, "t_halo") if comm and kind == "strong" else None,
                   bytes_max=int(rs[0]["bytes_max"]), msgs_total=int(rs[0]["msgs_total"]))
        out[kind].append(row)
    return out


def print_tables(t):
    m = t["meta"]
    print(f"{m['date_utc']} UTC, {m['cpus']} CPUs ({m['cpu_model']}), {m['mpirun']}, {m['threads_per_rank']} thread(s)/rank, "
          f"{m['reps']} repetitions, {m['iters']} sweeps per run, seed {m['seed']}, load average at start {m['loadavg1_at_start']:.2f}")
    print("compute / halo / allreduce are medians of the per-run MAXIMUM over ranks: they do not add up to T.")
    for kind in ("strong", "weak"):
        print(f"\n{kind} scaling (times in ms; 95 % bootstrap interval of the median in brackets)")
        print(f"{'decomp':>6} {'p':>3} {'T median':>9} {'interval':>17} {'S':>6} {'E':>6} {'e(p)':>6} {'compute':>8} {'halo':>7} "
              f"{'comm only':>9} {'allreduce':>9} {'imb':>5}")
        for r in t[kind]:
            s = f"{r['speedup']:.2f}" if "speedup" in r else "-"
            e = f"{r['karp_flatt']:.3f}" if r.get("karp_flatt") is not None else "-"
            co = f"{r['comm_only'] * 1e3:.2f}" if r.get("comm_only") is not None else "-"
            print(f"{r['decomp']:>6} {r['p']:>3} {r['t'] * 1e3:>9.1f} [{r['lo'] * 1e3:6.1f},{r['hi'] * 1e3:6.1f}] {s:>6} "
                  f"{r['efficiency']:>6.2f} {e:>6} {r['comp'] * 1e3:>8.1f} {r['halo'] * 1e3:>7.2f} {co:>9} {r['red'] * 1e3:>9.3f} {r['imbalance']:>5.2f}")


def svg_speedup(t, path):
    """Strong-scaling speedup with its interval, against the ideal line. Colours: currentColor and site variables."""
    rows = [r for r in t["strong"] if r["decomp"] == "1d"]
    pmax = max(r["p"] for r in rows)
    W, H, L, R, T, B = 560, 330, 62, 20, 24, 52
    xs = lambda p: L + (p - 1) / (pmax - 1) * (W - L - R)
    t1 = rows[0]["t"]
    ymax = max(pmax * 1.08, max(t1 / r["lo"] for r in rows) * 1.06)  # room for the whole interval
    ys = lambda s: H - B - s / ymax * (H - T - B)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="sp-t" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">',
         f'<title id="sp-t">Gain du solveur de Jacobi, passage à l\u2019échelle fort</title>',
         f'<line x1="{L}" y1="{H - B}" x2="{W - R}" y2="{H - B}" stroke="currentColor" stroke-width="1.5"/>',
         f'<line x1="{L}" y1="{T}" x2="{L}" y2="{H - B}" stroke="currentColor" stroke-width="1.5"/>',
         f'<line x1="{xs(1)}" y1="{ys(1)}" x2="{xs(pmax)}" y2="{ys(pmax)}" stroke="currentColor" stroke-width="1.5" stroke-dasharray="6 5" opacity="0.6"/>',
         f'<text x="{xs(pmax) - 16}" y="{ys(pmax) - 6}" text-anchor="end" font-size="14" fill="currentColor">idéal S = p</text>']
    for p in range(1, pmax + 1):
        o.append(f'<line x1="{xs(p)}" y1="{H - B}" x2="{xs(p)}" y2="{H - B + 5}" stroke="currentColor"/>')
        o.append(f'<text x="{xs(p)}" y="{H - B + 22}" text-anchor="middle" font-size="14" fill="currentColor">{p}</text>')
    for s in range(0, int(ymax) + 1):
        o.append(f'<line x1="{L - 5}" y1="{ys(s)}" x2="{L}" y2="{ys(s)}" stroke="currentColor"/>')
        o.append(f'<text x="{L - 9}" y="{ys(s) + 5}" text-anchor="end" font-size="14" fill="currentColor">{s}</text>')
    pts = []
    for r in rows:
        s, slo, shi = t1 / r["t"], t1 / r["hi"], t1 / r["lo"]
        o.append(f'<line x1="{xs(r["p"])}" y1="{ys(slo)}" x2="{xs(r["p"])}" y2="{ys(shi)}" stroke="var(--accent)" stroke-width="2"/>')
        pts.append((xs(r["p"]), ys(s)))
    o.append('<polyline fill="none" stroke="var(--accent)" stroke-width="2.5" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '"/>')
    for x, y in pts:
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="var(--accent)"/>')
    o.append(f'<text x="{(L + W - R) / 2}" y="{H - 12}" text-anchor="middle" font-size="14" fill="currentColor">processus MPI p</text>')
    o.append(f'<text x="16" y="{(T + H - B) / 2}" text-anchor="middle" font-size="14" fill="currentColor" transform="rotate(-90 16 {(T + H - B) / 2})">gain S = T1 / Tp</text>')
    o.append("</svg>")
    Path(path).write_text("\n".join(o))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("study")
    ap.add_argument("--svg")
    a = ap.parse_args()
    tab = table(a.study)
    print_tables(tab)
    if a.svg:
        svg_speedup(tab, a.svg)
        print("wrote", a.svg)
