#!/usr/bin/env python3
"""Blackwell GPU charts: price (log X) vs properties. USD, English."""
from pathlib import Path
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

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
    "GeForce RTX 50",
    "RTX PRO",
    "B-series",
    "DGX personal",
    "NVL72 /GPU",
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
        "gamme": gamme,
        "model": model,
        "usd": usd,
        "vram": vram,
        "bw": bw,
        "tdp": tdp,
        "usd_per_gb": usd / vram,
        "usd_per_gbs": usd / bw,
        "est": est,
    })

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "legend.fontsize": 9,
    "figure.dpi": 160,
    "savefig.dpi": 160,
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})


def money_fmt(x, _pos=None):
    if x >= 1000:
        if x >= 10000:
            return f"${x/1000:.0f}k"
        return f"${x/1000:.1f}k"
    return f"${x:.0f}"


def scatter(y_key, y_label, title, filename, annotate=True):
    fig, ax = plt.subplots(figsize=(11, 7))
    for gamme in GAMME_ORDER:
        pts = [r for r in rows if r["gamme"] == gamme]
        xs = [r["usd"] for r in pts]
        ys = [r[y_key] for r in pts]
        sizes = [max(40, min(220, math.sqrt(r["vram"]) * 18)) for r in pts]
        markers = ["o" if not r["est"] else "D" for r in pts]
        firm = [r for r in pts if not r["est"]]
        est = [r for r in pts if r["est"]]
        if firm:
            ax.scatter(
                [r["usd"] for r in firm],
                [r[y_key] for r in firm],
                s=[max(40, min(220, math.sqrt(r["vram"]) * 18)) for r in firm],
                c=COLORS[gamme],
                label=gamme,
                alpha=0.9,
                edgecolors="white",
                linewidths=0.6,
                zorder=3,
            )
        if est:
            ax.scatter(
                [r["usd"] for r in est],
                [r[y_key] for r in est],
                s=[max(40, min(220, math.sqrt(r["vram"]) * 18)) for r in est],
                c=COLORS[gamme],
                label=f"{gamme} (est.)" if not firm else None,
                marker="D",
                alpha=0.9,
                edgecolors="white",
                linewidths=0.6,
                zorder=3,
            )
    if annotate:
        for r in rows:
            ax.annotate(
                r["model"],
                (r["usd"], r[y_key]),
                textcoords="offset points",
                xytext=(5, 4),
                fontsize=7.5,
                alpha=0.85,
            )

    ax.set_xscale("log")
    ax.set_xlim(200, 120000)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(money_fmt))
    ax.xaxis.set_major_locator(mticker.LogLocator(base=10))
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.set_xlabel("Price (USD, log scale)")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    handles, labels = ax.get_legend_handles_labels()
    seen = set()
    h2, l2 = [], []
    for h, l in zip(handles, labels):
        if l not in seen:
            seen.add(l)
            h2.append(h)
            l2.append(l)
    leg = ax.legend(h2, l2, title="Product line", loc="upper left", framealpha=0.95)
    fig.text(
        0.99,
        0.01,
        "Circle = MSRP / marketplace / street · Diamond = estimate · FX 1 USD = 0.893 EUR (2026-10-23) · Size ∝ √VRAM",
        ha="right",
        va="bottom",
        fontsize=8,
        color="#555",
    )
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    path = OUT / filename
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


def bar_chart(key, title, xlabel, filename, fmt):
    sorted_rows = sorted(rows, key=lambda r: r[key])
    fig, ax = plt.subplots(figsize=(11, 8))
    y_pos = np.arange(len(sorted_rows))
    colors = [COLORS[r["gamme"]] for r in sorted_rows]
    vals = [r[key] for r in sorted_rows]
    ax.barh(y_pos, vals, color=colors, edgecolor="white", linewidth=0.4)
    ax.set_yticks(y_pos)
    labels = [f"{r['model']}{' *' if r['est'] else ''}" for r in sorted_rows]
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.invert_yaxis()
    for i, r in enumerate(sorted_rows):
        ax.text(vals[i] * 1.01, i, fmt(r[key]), va="center", fontsize=8)
    from matplotlib.patches import Patch
    patches = [Patch(facecolor=COLORS[g], label=g) for g in GAMME_ORDER]
    ax.legend(handles=patches, title="Product line", loc="lower right", framealpha=0.95)
    fig.text(
        0.99,
        0.01,
        "* = estimate · FX 1 USD = 0.893 EUR (2026-10-23) · Lower is better",
        ha="right",
        va="bottom",
        fontsize=8,
        color="#555",
    )
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    path = OUT / filename
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


scatter(
    "vram",
    "VRAM (GB)",
    "NVIDIA Blackwell: VRAM vs Price (log)",
    "01-vram-vs-price.png",
)
scatter(
    "bw",
    "Memory bandwidth (GB/s)",
    "NVIDIA Blackwell: Bandwidth vs Price (log)",
    "02-bw-vs-price.png",
)
scatter(
    "usd_per_gb",
    "USD per GB of memory",
    "NVIDIA Blackwell: $/GB vs Price (log)",
    "03-usd-per-gb-vs-price.png",
)
scatter(
    "tdp",
    "TDP (W)",
    "NVIDIA Blackwell: TDP vs Price (log)",
    "04-tdp-vs-price.png",
)
bar_chart(
    "usd_per_gb",
    "NVIDIA Blackwell: USD per GB (lower is better)",
    "USD / GB",
    "05-usd-per-gb-bars.png",
    lambda v: f"${v:.0f}",
)
bar_chart(
    "usd_per_gbs",
    "NVIDIA Blackwell: USD per GB/s bandwidth (lower is better)",
    "USD / (GB/s)",
    "06-usd-per-gbs-bars.png",
    lambda v: f"${v:.2f}",
)

print("done")
