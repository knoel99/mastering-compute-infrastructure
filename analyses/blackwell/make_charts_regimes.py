#!/usr/bin/env python3
"""Piecewise trends by memory class — not one global line."""
from pathlib import Path
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D

OUT = Path(__file__).resolve().parent
USD_PER_EUR = 1 / 0.893

GPUS = [
    ("GeForce RTX 50", "5090", 1785, 32, 1792, 575, False, "GDDR7"),
    ("GeForce RTX 50", "5080", 892, 16, 960, 360, False, "GDDR7"),
    ("GeForce RTX 50", "5070 Ti", 669, 16, 896, 300, False, "GDDR7"),
    ("GeForce RTX 50", "5070", 490, 12, 672, 250, False, "GDDR7"),
    ("GeForce RTX 50", "5060 Ti 16", 383, 16, 448, 180, False, "GDDR7"),
    ("GeForce RTX 50", "5060 Ti 8", 338, 8, 448, 180, False, "GDDR7"),
    ("GeForce RTX 50", "5060", 267, 8, 448, 145, False, "GDDR7"),
    ("GeForce RTX 50", "5050", 222, 8, 320, 130, False, "GDDR7"),
    ("RTX PRO", "6000 WS", 14288, 96, 1792, 600, False, "GDDR7"),
    ("RTX PRO", "6000 Max-Q", 14734, 96, 1792, 300, False, "GDDR7"),
    ("RTX PRO", "5000 72", 8929, 72, 1344, 300, False, "GDDR7"),
    ("RTX PRO", "5000 48", 7009, 48, 1344, 300, False, "GDDR7"),
    ("RTX PRO", "4500", 4196, 32, 896, 200, False, "GDDR7"),
    ("RTX PRO", "4000", 2723, 24, 672, 145, False, "GDDR7"),
    ("RTX PRO", "2000", 1607, 16, 288, 70, False, "GDDR7"),
    ("B-series", "B100", 28576, 192, 8000, 700, True, "HBM"),
    ("B-series", "B200", 42418, 192, 8000, 1000, True, "HBM"),
    ("B-series", "B300", 47329, 288, 8000, 1000, True, "HBM"),
    ("DGX personal", "Spark GB10", 6206, 128, 273, 140, False, "LPDDR5X"),
    ("DGX personal", "Station GB300", 91532, 252, 7100, 1600, True, "HBM"),
    ("NVL72 /GPU", "GB200 /GPU", 31007, 186, 8000, 1000, True, "HBM"),
    ("NVL72 /GPU", "GB300 /GPU", 43410, 279, 8000, 1000, True, "HBM"),
]

GAMME_ORDER = ["GeForce RTX 50", "RTX PRO", "B-series", "DGX personal", "NVL72 /GPU"]
COLORS = {
    "GeForce RTX 50": "#2563eb",
    "RTX PRO": "#ca8a04",
    "B-series": "#0891b2",
    "DGX personal": "#c026d3",
    "NVL72 /GPU": "#64748b",
}
REGIME_STYLE = {
    "GeForce": {"color": "#1d4ed8", "label": "GeForce fit"},
    "PRO": {"color": "#a16207", "label": "RTX PRO fit"},
    "HBM": {"color": "#0e7490", "label": "HBM cluster fit"},
}

rows = []
for gamme, model, eur, vram, bw, tdp, est, mem in GPUS:
    usd = eur * USD_PER_EUR
    rows.append({
        "gamme": gamme, "model": model, "usd": usd, "vram": vram,
        "bw": bw, "tdp": tdp, "usd_per_gb": usd / vram,
        "usd_per_gbs": usd / bw, "est": est, "mem": mem,
    })

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 11,
    "axes.titlesize": 13, "axes.labelsize": 12, "legend.fontsize": 8.5,
    "figure.dpi": 160, "savefig.dpi": 160,
    "axes.grid": True, "grid.alpha": 0.35, "grid.linestyle": "--",
})


def money_fmt(x, _pos=None):
    if x >= 1000:
        return f"${x/1000:.0f}k" if x >= 10000 else f"${x/1000:.1f}k"
    return f"${x:.0f}"


def ols(subset, y_key):
    if len(subset) < 3:
        return None
    x = np.array([math.log10(r["usd"]) for r in subset])
    y = np.array([r[y_key] for r in subset], dtype=float)
    b, a = np.polyfit(x, y, 1)
    y_hat = a + b * x
    ss_res = ((y - y_hat) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return a, b, r2, x.min(), x.max()


def draw_fit(ax, fit, style, y_floor=None):
    if fit is None:
        return
    a, b, r2, xmin, xmax = fit
    pad = 0.05
    xs = np.logspace(xmin - pad, xmax + pad, 80)
    ys = a + b * np.log10(xs)
    ax.plot(xs, ys, color=style["color"], linestyle="--", linewidth=2.0,
            zorder=4, label=f"{style['label']} (R²={r2:.2f})")


def scatter(y_key, y_label, title, filename, note):
    fig, ax = plt.subplots(figsize=(11.2, 7.2))

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
        ax.annotate(r["model"], (r["usd"], r[y_key]),
                    textcoords="offset points", xytext=(5, 4),
                    fontsize=7.5, alpha=0.85)

    geforce = [r for r in rows if r["gamme"] == "GeForce RTX 50"]
    pro = [r for r in rows if r["gamme"] == "RTX PRO"]
    hbm = [r for r in rows if r["mem"] == "HBM"]

    draw_fit(ax, ols(geforce, y_key), REGIME_STYLE["GeForce"])
    draw_fit(ax, ols(pro, y_key), REGIME_STYLE["PRO"])
    if y_key == "bw":
        bw_vals = [r["bw"] for r in hbm]
        mean_bw = float(np.mean(bw_vals))
        xs = np.logspace(math.log10(min(r["usd"] for r in hbm)) * 0.95,
                         math.log10(max(r["usd"] for r in hbm)) * 1.05, 50)
        ax.plot(xs, [mean_bw] * len(xs), color=REGIME_STYLE["HBM"]["color"],
                linestyle="--", linewidth=2.0, zorder=4,
                label=f"HBM plateau ≈ {mean_bw:.0f} GB/s")
    else:
        draw_fit(ax, ols(hbm, y_key), REGIME_STYLE["HBM"])

    spark = next(r for r in rows if r["model"] == "Spark GB10")
    ax.annotate(
        "Spark: capacity,\nnot bandwidth",
        xy=(spark["usd"], spark[y_key]),
        xytext=(spark["usd"] * 1.8, spark[y_key] * (0.55 if y_key != "bw" else 2.2)),
        fontsize=8, color="#a21caf",
        arrowprops=dict(arrowstyle="->", color="#a21caf", lw=1),
        zorder=5,
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
    seen, h2, l2 = set(), [], []
    for h, l in zip(handles, labels):
        if l not in seen:
            seen.add(l); h2.append(h); l2.append(l)
    ax.legend(h2, l2, loc="best", framealpha=0.95, fontsize=8)

    fig.text(0.5, 0.03, note, ha="center", va="bottom", fontsize=9, color="#222")
    fig.text(
        0.99, 0.002,
        "Circle = MSRP/street · Diamond = estimate · FX 1 USD = 0.893 EUR (2026-10-23) · Dashed = OLS within regime (not global)",
        ha="right", va="bottom", fontsize=7, color="#555",
    )
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    path = OUT / filename
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)

    for name, subset in [("GeForce", geforce), ("PRO", pro), ("HBM", hbm)]:
        f = ols(subset, y_key)
        if f:
            a, b, r2, *_ = f
            print(f"  {name} {y_key}: a={a:.1f} b={b:.1f}/decade R²={r2:.2f} n={len(subset)}")
        elif y_key == "bw" and name == "HBM":
            print(f"  HBM bw: plateau mean={np.mean([r['bw'] for r in hbm]):.0f}")


scatter(
    "vram", "VRAM (GB)",
    "NVIDIA Blackwell: VRAM vs Price — piecewise by product line",
    "01-vram-vs-price.png",
    "Three regimes: GeForce (cheap GB) · PRO (same GDDR7, fewer GB/$) · HBM leap. Spark = VRAM without HBM speed.",
)
scatter(
    "bw", "Memory bandwidth (GB/s)",
    "NVIDIA Blackwell: Bandwidth vs Price — step, not a line",
    "02-bw-vs-price.png",
    "Step function: GDDR7 band (~0.3–1.8 TB/s) then HBM cliff (~8 TB/s). PRO pays 10× GeForce for similar BW. Spark = floor.",
)
scatter(
    "usd_per_gb", "USD per GB of memory",
    "NVIDIA Blackwell: $/GB vs Price — stepped premiums",
    "03-usd-per-gb-vs-price.png",
    "Steps up: GeForce ~$30–60/GB → PRO ~$110–170 → HBM ~$170–250 → Station ~$360. Spark breaks the step (~$54).",
)
scatter(
    "tdp", "TDP (W)",
    "NVIDIA Blackwell: TDP vs Price — steep then flat then system",
    "04-tdp-vs-price.png",
    "GeForce: steep W/$ · PRO: flatter + Max-Q bifurcation · HBM: 700–1000 W cluster · Station 1600 W = whole system.",
)

gef = [r for r in rows if r["gamme"] == "GeForce RTX 50"]
pro = [r for r in rows if r["gamme"] == "RTX PRO"]
hbm = [r for r in rows if r["mem"] == "HBM"]
with (OUT / "regime-analysis.md").open("w") as f:
    f.write("# Regime analysis (visual)\n\n")
    for key in ["vram", "bw", "usd_per_gb", "tdp"]:
        f.write(f"## {key}\n")
        for name, subset in [("GeForce", gef), ("PRO", pro), ("HBM", hbm)]:
            fit = ols(subset, key)
            if fit:
                a, b, r2, *_ = fit
                f.write(f"- {name}: y={a:.1f}+{b:.1f}·log10(P), R²={r2:.2f}, n={len(subset)}\n")
        f.write("\n")
print("done")
