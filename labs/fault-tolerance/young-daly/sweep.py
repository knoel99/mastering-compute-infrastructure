#!/usr/bin/env python3
"""Sweep the checkpoint interval, compare closed forms with Monte-Carlo, draw an SVG.

Example (values of the course, example 2.2):
    python3 sweep.py --delta 60 --mtbf-hours 3.09 --restart 300 --svg yd.svg
"""
import argparse
import json
import math
import sys

import yd


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--delta", type=float, required=True, help="blocking cost of one checkpoint, seconds")
    ap.add_argument("--mtbf-hours", type=float, required=True, help="MTBF of the whole job, hours")
    ap.add_argument("--restart", type=float, default=300.0, help="restart cost, seconds")
    ap.add_argument("--work-hours", type=float, default=800.0, help="useful work simulated per seed")
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--weibull-shape", type=float, default=0.7, help="shape of the bursty-failure variant")
    ap.add_argument("--svg", help="write a chart to this file")
    ap.add_argument("--json", help="write the table to this file")
    a = ap.parse_args(argv)

    m, d, r = a.mtbf_hours * 3600.0, a.delta, a.restart
    work = a.work_hours * 3600.0
    seeds = range(a.seeds)
    t_young, t_dh = yd.young(d, m), yd.daly_high(d, m)
    t_exact = yd.argmin_exact(d, m, r)
    print(f"delta={d:.0f} s  M={m:.0f} s ({a.mtbf_hours} h)  R={r:.0f} s")
    print(f"Young   tau = sqrt(2*delta*M)        = {t_young:8.1f} s")
    print(f"Daly 1  tau = sqrt(2*delta*M) - delta = {yd.daly_first(d, m):8.1f} s")
    print(f"Daly 2  higher-order estimate         = {t_dh:8.1f} s")
    print(f"exact   argmin of E[wall] (numerical) = {t_exact:8.1f} s")
    ks = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
    rows = []
    hdr = f"{'tau (s)':>9} {'1st-order':>10} {'exact':>8} {'MC exp':>8} {'+-':>6} {'MC wb':>8}"
    print(hdr)
    for k in ks:
        tau = round(t_young * k)
        g1 = 1.0 - yd.waste_first_order(tau, d, m, r)
        ge = yd.goodput_exact(tau, d, m, r)
        gm, se = yd.mean_goodput(tau, d, m, r, work, seeds)
        gw, sw = yd.mean_goodput(tau, d, m, r, work, seeds, shape=a.weibull_shape)
        rows.append({"tau": tau, "first_order": g1, "exact": ge, "mc_exp": gm, "se_exp": se, "mc_weibull": gw, "se_weibull": sw})
        print(f"{tau:9d} {g1:10.4f} {ge:8.4f} {gm:8.4f} {se:6.4f} {gw:8.4f}" + ("   <- Young" if k == 1.0 else ""))
    best = max(rows, key=lambda x: x["mc_exp"])
    best_w = max(rows, key=lambda x: x["mc_weibull"])
    at_young = next(x for x in rows if x["tau"] == round(t_young))
    summary = {
        "t_young": t_young, "t_daly_high": t_dh, "t_exact": t_exact,
        "best_sampled_tau_exp": best["tau"], "best_sampled_tau_weibull": best_w["tau"],
        "goodput_at_young_exp": at_young["mc_exp"], "goodput_best_exp": best["mc_exp"],
        "goodput_at_young_weibull": at_young["mc_weibull"], "goodput_best_weibull": best_w["mc_weibull"],
    }
    print(f"best sampled tau (exponential): {best['tau']} s; goodput at Young {at_young['mc_exp']:.4f} vs best {best['mc_exp']:.4f}")
    print(f"best sampled tau (Weibull k={a.weibull_shape}): {best_w['tau']} s; goodput at Young {at_young['mc_weibull']:.4f} vs best {best_w['mc_weibull']:.4f}")
    if a.json:
        json.dump({"params": {"delta": d, "mtbf": m, "restart": r}, "summary": summary, "rows": rows}, open(a.json, "w"), indent=1)
    if a.svg:
        open(a.svg, "w").write(svg(rows, t_young, a.weibull_shape))
    return 0


def svg(rows, t_young, shape):
    w, h, ml, mr, mt, mb = 640, 340, 56, 16, 16, 44
    xs = [math.log(r["tau"]) for r in rows]
    x0, x1 = min(xs), max(xs)
    ys = [v for r in rows for v in (r["first_order"], r["exact"], r["mc_exp"], r["mc_weibull"])]
    y0, y1 = math.floor(min(ys) * 20) / 20, math.ceil(max(ys) * 20) / 20

    def X(t):
        return ml + (math.log(t) - x0) / (x1 - x0) * (w - ml - mr)

    def Y(g):
        return mt + (y1 - g) / (y1 - y0) * (h - mt - mb)

    def path(key, extra=""):
        pts = " ".join(f"{X(r['tau']):.1f},{Y(r[key]):.1f}" for r in rows)
        return f'<polyline points="{pts}" fill="none" stroke-width="2" {extra}/>'

    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" font-family="inherit" font-size="12" role="img">']
    out.append('<title>Goodput en fonction de la période de checkpoint</title>')
    out.append(f'<rect x="{ml}" y="{mt}" width="{w - ml - mr}" height="{h - mt - mb}" fill="none" stroke="currentColor" stroke-opacity=".3"/>')
    g = y0
    while g <= y1 + 1e-9:
        out.append(f'<line x1="{ml}" x2="{w - mr}" y1="{Y(g):.1f}" y2="{Y(g):.1f}" stroke="currentColor" stroke-opacity=".12"/>')
        out.append(f'<text x="{ml - 6}" y="{Y(g) + 4:.1f}" text-anchor="end" fill="currentColor">{g:.2f}</text>')
        g += 0.05
    for r in rows:
        out.append(f'<text x="{X(r["tau"]):.1f}" y="{h - mb + 16}" text-anchor="middle" fill="currentColor">{r["tau"]}</text>')
    out.append(f'<text x="{(ml + w - mr) / 2}" y="{h - 6}" text-anchor="middle" fill="currentColor">période de calcul entre checkpoints (s), échelle log</text>')
    out.append(f'<line x1="{X(t_young):.1f}" x2="{X(t_young):.1f}" y1="{mt}" y2="{h - mb}" stroke="currentColor" stroke-dasharray="4 3"/>')
    out.append(f'<text x="{X(t_young) + 4:.1f}" y="{h - mb - 6}" fill="currentColor">Young</text>')
    out.append(path("first_order", 'stroke="currentColor" stroke-opacity=".55" stroke-dasharray="6 4"'))
    out.append(path("exact", 'stroke="currentColor"'))
    out.append(path("mc_weibull", 'stroke="var(--accent,#b45309)" stroke-opacity=".7"'))
    for r in rows:
        out.append(f'<circle cx="{X(r["tau"]):.1f}" cy="{Y(r["mc_exp"]):.1f}" r="4" fill="var(--accent,#b45309)"/>')
    out.append(f'<text x="{ml + 8}" y="{mt + 16}" fill="currentColor">trait plein : modèle exact · pointillé : premier ordre</text>')
    out.append(f'<text x="{ml + 8}" y="{mt + 32}" fill="currentColor">points : Monte-Carlo · orange fin : Weibull k={shape}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    sys.exit(main())
