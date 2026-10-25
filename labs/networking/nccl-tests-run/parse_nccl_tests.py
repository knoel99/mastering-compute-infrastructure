#!/usr/bin/env python3
"""Parse the table printed by nccl-tests (all_reduce_perf & co.) and judge it.

Usage: python3 parse_nccl_tests.py OUTPUT [--ranks N] [--expect-busbw GB/S] [--tolerance 0.8] [--json]

Columns read: size, count, type, redop, root, then (time us, algbw GB/s, busbw GB/s, #wrong) for out-of-place and in-place.
The table layout was read in nccl-tests/src/util.cu (2026-10-24); it changes between versions (-I, -U add columns):
rows that do not match are skipped.  Exit status 1 when a problem is reported.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

ROW = re.compile(
    r"^\s*(\d+)\s+(\d+)\s+(\w+)\s+(\w+)\s+(-?\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s*$"
)
AVG = re.compile(r"^#\s*Avg bus bandwidth\s*:\s*([\d.]+)")
NRANKS = re.compile(r"^#\s*Rank\s+\d+ Group")


def parse(text: str) -> dict:
    rows, avg, ranks = [], None, 0
    for line in text.splitlines():
        if NRANKS.match(line):
            ranks += 1
        m = AVG.match(line)
        if m:
            avg = float(m.group(1))
        m = ROW.match(line)
        if m:
            g = m.groups()
            wrong = lambda s: None if s in ("N/A", "-") else int(float(s))  # noqa: E731
            rows.append({"size": int(g[0]), "count": int(g[1]), "type": g[2], "redop": g[3],
                         "oop": {"time_us": float(g[5]), "algbw": float(g[6]), "busbw": float(g[7]), "wrong": wrong(g[8])},
                         "ip": {"time_us": float(g[9]), "algbw": float(g[10]), "busbw": float(g[11]), "wrong": wrong(g[12])}})
    return {"rows": rows, "avg_busbw": avg, "ranks_listed": ranks}


def fit_alpha_beta(rows: list[dict], ranks: int, min_size: int = 1 << 20) -> dict:
    """Weighted least squares T = a + b*n on the large sizes (out-of-place times), weights 1/T^2 so that the
    relative error is minimised.  Ring all-reduce: b = 2(p-1)/(p*B)  =>  B = 2(p-1)/(p*b);  a = 2(p-1)*alpha."""
    pts = [(r["size"], r["oop"]["time_us"] * 1e-6) for r in rows if r["size"] >= min_size]
    if len(pts) < 3:
        raise ValueError("need at least 3 sizes >= min_size")
    w = [1 / t**2 for _, t in pts]
    sw = sum(w)
    n_mean = sum(wi * n for wi, (n, _) in zip(w, pts)) / sw
    t_mean = sum(wi * t for wi, (_, t) in zip(w, pts)) / sw
    b = sum(wi * (n - n_mean) * (t - t_mean) for wi, (n, t) in zip(w, pts)) / sum(wi * (n - n_mean) ** 2 for wi, (n, _) in zip(w, pts))
    a = t_mean - b * n_mean
    return {"B_gbs": 2 * (ranks - 1) / (ranks * b) / 1e9, "alpha_us": a / (2 * (ranks - 1)) * 1e6, "intercept_us": a * 1e6}


def analyse(res: dict, ranks: int | None, expect: float | None, tolerance: float) -> dict:
    rows = res["rows"]
    problems: list[str] = []
    notes: list[str] = []
    if not rows:
        return {"problems": ["no data rows found"], "notes": [], "summary": {}}
    bad = [(r["size"], r[k]["wrong"]) for r in rows for k in ("oop", "ip") if r[k]["wrong"]]
    if bad:
        problems.append(f"data corruption: #wrong > 0 for sizes {sorted({s for s, _ in bad})[:5]}")
    best = [max(r["oop"]["busbw"], r["ip"]["busbw"]) for r in rows]
    plateau = max(best)
    n90 = next(r["size"] for r, b in zip(rows, best) if b >= 0.9 * plateau)
    big = [b for r, b in zip(rows, best) if r["size"] >= n90]
    dips = [rows[i]["size"] for i in range(1, len(rows)) if rows[i]["size"] >= n90 and best[i] < 0.7 * best[i - 1]]
    if dips:
        notes.append(f"busbw drops by more than 30 % at sizes {dips[:5]} after the plateau was reached (algorithm switch or instability)")
    summary = {"rows": len(rows), "plateau_busbw_gbs": plateau, "size_at_90pct_bytes": n90,
               "smallest_size_time_us": rows[0]["oop"]["time_us"], "median_busbw_above_n90": statistics.median(big), "avg_busbw_reported": res["avg_busbw"]}
    if expect:
        ratio = plateau / expect
        summary["plateau_over_expected"] = round(ratio, 3)
        if ratio < tolerance:
            problems.append(f"plateau busbw {plateau:.1f} GB/s is {ratio:.0%} of the expected {expect:g} GB/s (tolerance {tolerance:.0%})")
    p = ranks or res["ranks_listed"] or None
    if p and p > 1:
        try:
            summary["fit"] = {k: round(v, 3) for k, v in fit_alpha_beta(rows, p).items()}
        except ValueError:
            notes.append("not enough large sizes for an alpha-beta fit")
    return {"problems": problems, "notes": notes, "summary": summary}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("output")
    ap.add_argument("--ranks", type=int, help="number of ranks (default: count the 'Rank n Group' lines)")
    ap.add_argument("--expect-busbw", type=float, help="busbw plateau you expect, GB/s")
    ap.add_argument("--tolerance", type=float, default=0.8, help="problem if plateau < tolerance * expected (default 0.8)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    res = analyse(parse(Path(a.output).read_text(encoding="utf-8", errors="replace")), a.ranks, a.expect_busbw, a.tolerance)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        s = res["summary"]
        print(f"{Path(a.output).name}: {s.get('rows', 0)} sizes; plateau busbw {s.get('plateau_busbw_gbs', 0):.1f} GB/s; "
              f"90% of it reached at {s.get('size_at_90pct_bytes', 0)} B; smallest-size time {s.get('smallest_size_time_us', 0):.1f} us; fit {s.get('fit')}")
        for n in res["notes"]:
            print("  note:", n)
        for p in res["problems"]:
            print("  PROBLEM:", p)
    print("OK nccl-tests output" if not res["problems"] else "PROBLEMS found")
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
