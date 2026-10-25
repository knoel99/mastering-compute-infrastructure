#!/usr/bin/env python3
"""Scenario scan for the cost-aware-placement lab. EVERYTHING HERE IS SYNTHETIC: prices are in arbitrary units (u per
GPU-hour), availabilities and hazards are invented, the egress rate is a made-up 0.09 u/GB. The checkpoint size is the
only derived figure: 7e9 parameters x 16 bytes per parameter = 112 GB (the ZeRO rule used in module 2).

Usage: python3 scenarios.py [--impl reference|starter] [--seeds 200] [--lam 40]
"""
import argparse
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

POOL_ROWS = [  # id, provider, price u/GPU-h, hazard /h, p_avail per 15-min slot, startup h
    ("a-od", "A", 10.0, 0.00, 0.90, 0.10),
    ("a-spot", "A", 4.0, 0.15, 0.60, 0.15),
    ("b-spot", "B", 3.0, 0.30, 0.80, 0.15),
    ("c-spot", "C", 3.4, 0.10, 0.50, 0.15),
]
DATA_GB = [0, 1_000, 10_000, 30_000, 60_000, 100_000]


def build(P, data_gb):
    pools = [P.Pool(*row) for row in POOL_ROWS]
    job = P.Job(gpus=64, work_h=120.0, deadline_h=240.0, ckpt_gb=112.0, data_gb=float(data_gb),
                ckpt_cost_h=0.05, restart_h=0.17, home="A")
    net = P.Network(egress_u_per_gb=0.09, gbit_per_s=10.0, efficiency=0.8)
    return pools, job, net


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", default="reference", choices=["reference", "starter"])
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--lam", type=float, default=40.0, help="value of one hour of delay, u per hour")
    args = ap.parse_args()
    sys.path.insert(0, str(HERE / args.impl))
    P = importlib.import_module("placement")
    seeds = range(args.seeds)
    pools, job, _ = build(P, 0)
    print("SYNTHETIC pools (u = arbitrary unit):")
    for p in pools:
        print(f"  {p.id:7s} provider {p.provider}  price {p.price:5.2f}  hazard {p.hazard:4.2f}/h  p_avail {p.p_avail:.2f}"
              f"  price per useful GPU-hour {P.price_per_useful_hour(p, job):6.3f}")
    print(f"job: {job.gpus} GPUs x {job.work_h:g} h of work, deadline {job.deadline_h:g} h, checkpoint {job.ckpt_gb:g} GB,"
          f" home provider {job.home}; {args.seeds} seeds, lam = {args.lam:g} u/h\n")
    print(f"{'data GB':>8} {'policy':>9} {'cost u':>10} {'finish h':>9} {'late %':>7} {'moves':>6} {'preempt':>8}")
    rows = {}
    for data in DATA_GB:
        pools, job, net = build(P, data)
        pol = {"stay": P.Stay("a-spot"), "cheapest": P.Cheapest(), "failover": P.FirstAvailable(), "aware": P.Aware(args.lam)}
        res = {k: P.run_many(job, pools, net, v, seeds) for k, v in pol.items()}
        rows[data] = res
        for k, r in res.items():
            s = P.summarize(r)
            print(f"{data:8d} {k:>9} {s['cost']:10.0f} {s['finish_h']:9.1f} {100 * s['late']:7.1f} {s['moves']:6.2f} {s['preemptions']:8.2f}")
        d, h = P.paired_diff(res["aware"], res["stay"])
        print(f"{'':8s} aware - stay: {d:+9.0f} u (+/- {h:.0f}, paired over {args.seeds} seeds)")
    others = ("stay", "cheapest", "failover")
    worst = max(P.summarize(r["aware"])["cost"] / min(P.summarize(r[k])["cost"] for k in others) for r in rows.values())
    print(f"\nworst ratio aware / min(other policies) over the scan: {worst:.3f}")
    moves = [P.summarize(rows[d]["aware"])["moves"] for d in DATA_GB]
    print("mean moves of 'aware' by dataset size: " + ", ".join(f"{d}:{m:.2f}" for d, m in zip(DATA_GB, moves)))
    first_stay = next((d for d in DATA_GB if P.summarize(rows[d]["aware"])["moves"] < 0.05), None)
    print(f"smallest scanned dataset for which 'aware' (almost) never moves: {first_stay} GB")
    ok = all(b <= a + 0.05 for a, b in zip(moves, moves[1:])) and worst <= 1.05
    print("CRITERION (moves of 'aware' non-increasing with data size; cost <= 1.05 x the best other policy): "
          + ("OK" if ok else "NOT MET"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
