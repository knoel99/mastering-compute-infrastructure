#!/usr/bin/env python3
"""Blackwell charts with global log-price trend lines. USD, English."""
from pathlib import Path
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

OUT = Path(__file__).resolve().parent
USD_PER_EUR = 1 / 0.893

GPUS = [
    ("GeForce RTX 50", "5090", 1785, 32, 1792, 575, False),
    ("GeForce RTX 50", "5080", 892, 16, 960, 360, False),
    ("GeForce RTX 50", "5070 Ti", 669, 16, 896, 300, False),
    ("GeForce RTX 50", "5070", 490, 12, 672, 250, False),
    ("GeForce RTX 50", "5060 Ti 16", 383, 16, 448, 180, False),
    ("GeForce RTX 50", "5060 Ti 8", 338, 8, 448, 180, False),
    ("GeForce RTX 50", "5060", 267, 8, 448, 145, False),
    ("GeForce RTX 50", "5050", 222, 8, 320, 130, False),
    ("RTX PRO", "6000 WS", 14288, 96, 1792, 600, False),
    ("RTX PRO", "6000 Max-Q", 14734, 96, 1792, 300, False),
    ("RTX PRO", "5000 72", 8929, 72, 1344, 300, False),
    ("RTX PRO", "5000 48", 7009, 48, 1344, 300, False),
    ("RTX PRO", "4500", 4196, 32, 896, 200, False),
    ("RTX PRO", "4000", 2723, 24, 672, 145, False),
    ("RTX PRO", "2000", 1607, 16, 288, 70, False),
    ("B-series", "B100", 28576, 192, 8000, 700, True),
    ("B-series", "B200", 42418, 192, 8000, 1000, True),
    ("B-series", "B300", 47329, 288, 8000, 1000, True),
    ("DGX personal", "Spark GB10", 6206, 128, 273, 140, False),
    ("DGX personal", "Station GB300", 91532, 252, 7100, 1600, True),
    ("NVL72 /GPU", "GB200 /GPU", 31007, 186, 8000, 1000, True),
    ("NVL72 /GPU", "GB300 /GPU", 43410, 279, 8000, 1000, True),
]

GAMME_ORDER = [
    "GeForce RTX 50", "RTX PRO", "B-series", "DGX personal", "NVL72 /GPU",
]
COLORS = {
    "GeForce RTX 50": "#2563eb",
    "RTX PRO": "#ca8a04",
    "B-series": "#0891b2",
    "DGX personal": "#c026d3",
    "NVL72 /GPU": "#64748b",
}

rows = []
for gamme, model, eur, vram, bw, tdp, est in GPUS:
    usd = eur * USD_PER_EUR
    rows.append({
        "gamme": gamme, "model": model, "usd": usd,
        "vram": vram, "bw": bw, "tdp": tdp,
        "usd_per_gb": usd / vram, "usd_per_gbs": usd / bw, "est": est,
    })

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 11,
    "axes.titlesize": 14, "axes.labelsize": 12, "legend.fontsize": 9,
    "figure.dpi": 160, "savefig.dpi": 160,
    "axes.grid": True, "grid.alpha": 0.35, "grid.linestyle": "--",
})


def money_fmt(x, _pos=None):
    if x >= 1000:
        return f"${x/1000:.0f}k" if x >= 10000 else f"${x/1000:.1f}k"
    return f"${x:.0f}"


def fit_log_price(y_key):
    """OLS: y = a + b * log10(usd). Returns a, b, r2, equation string."""
    x = np.array([math.log10(r["usd"]) for r in rows])
    y = np.array([r[y_key] for r in rows], dtype=float)
    b, a = np.polyfit(x, y, 1)
    y_hat = a + b * x
    ss_res = np.sum((y - y_hat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    eq = f"y = {a:.1f} + {b:.1f}·log₁₀(price)  ·  R² = {r2:.2f}  ·  +{b:.1f} per 10× price"
    return a, b, r2, eq


def scatter(y_key, y_label, title, filename):
    a, b, r2, eq = fit_log_price(y_key)
    fig, ax = plt.subplots(figsize=(11, 7))

    for gamme in GAMME_ORDER:
        pts = [r for r in rows if r["gamme"] == gamme]
        firm = [r for r in pts if not r["est"]]
        est = [r for r in pts if r["est"]]
        if firm:
            ax.scatter(
                [r["usd"] for r in firm], [r[y_key] for r in firm],
                s=[max(40, min(220, math.sqrt(r["vram"]) * 18)) for r in firm],
                c=COLORS[gamme], label=gamme, alpha=0.9,
                edgecolors="white", linewidths=0.6, zorder=3,
            )
        if est:
            ax.scatter(
                [r["usd"] for r in est], [r[y_key] for r in est],
                s=[max(40, min(220, math.sqrt(r["vram"]) * 18)) for r in est],
                c=COLORS[gamme],
                label=None if firm else f"{gamme} (est.)",
                marker="D", alpha=0.9,
                edgecolors="white", linewidths=0.6, zorder=3,
            )

    for r in rows:
        ax.annotate(
            r["model"], (r["usd"], r[y_key]),
            textcoords="offset points", xytext=(5, 4),
            fontsize=7.5, alpha=0.85,
        )

    xs = np.logspace(math.log10(220), math.log10(100000), 200)
    ys = a + b * np.log10(xs)
    ax.plot(xs, ys, color="#111", linestyle="--", linewidth=2.0, zorder=4,
            label="Trend (all lines)")

    ax.set_xscale("log")
    ax.set_xlim(200, 120000)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(money_fmt))
    ax.xaxis.set_major_locator(mticker.LogLocator(base=10))
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.set_xlabel("Price (USD, log scale)")
    ax.set_ylabel(y_label)
    ax.set_title(title)

    handles, labels = ax.get_legend_handles_labels()
    seen, h2, l2 = set(), [], []
    for h, l in zip(handles, labels):
        if l not in seen:
            seen.add(l)
            h2.append(h)
            l2.append(l)
    ax.legend(h2, l2, title="Product line", loc="upper left", framealpha=0.95)

    fig.text(0.5, 0.035, eq, ha="center", va="bottom", fontsize=10,
             style="italic", color="#222")
    fig.text(
        0.99, 0.005,
        "Circle = MSRP / street · Diamond = estimate · FX 1 USD = 0.893 EUR (2026-10-23) · Size ∝ √VRAM · Dashed = OLS on all GPUs",
        ha="right", va="bottom", fontsize=7.5, color="#555",
    )
    fig.tight_layout(rect=[0, 0.07, 1, 1])
    path = OUT / filename
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"{filename}: {eq}")
    return {"metric": y_key, "a": a, "b": b, "r2": r2, "eq": eq}


stats = []
stats.append(scatter("vram", "VRAM (GB)",
    "NVIDIA Blackwell: VRAM vs Price (log) — trend across all lines",
    "01-vram-vs-price.png"))
stats.append(scatter("bw", "Memory bandwidth (GB/s)",
    "NVIDIA Blackwell: Bandwidth vs Price (log) — trend across all lines",
    "02-bw-vs-price.png"))
stats.append(scatter("usd_per_gb", "USD per GB of memory",
    "NVIDIA Blackwell: $/GB vs Price (log) — trend across all lines",
    "03-usd-per-gb-vs-price.png"))
stats.append(scatter("tdp", "TDP (W)",
    "NVIDIA Blackwell: TDP vs Price (log) — trend across all lines",
    "04-tdp-vs-price.png"))

md = OUT / "trend-equations.md"
with md.open("w") as f:
    f.write("# OLS trends: y = a + b·log10(price_USD)\n\n")
    f.write("| Metric | a (intercept) | b (per decade) | R² |\n|---|---:|---:|---:|\n")
    for s in stats:
        f.write(f"| {s['metric']} | {s['a']:.2f} | {s['b']:.2f} | {s['r2']:.3f} |\n")
print("wrote", md)
