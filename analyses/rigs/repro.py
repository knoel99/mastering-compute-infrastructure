import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy.interpolate import PchipInterpolator as P

OUT = Path(__file__).resolve().parent / "charts"
plt.style.use("dark_background")


def line(axis, x, y, color, lab, lx, ly):
    xx = np.linspace(x[0], x[-1], 200)
    axis.plot(xx, P(x, y)(xx), color=color, lw=2.5)
    axis.plot(x, y, "o", color=color, ms=5)
    axis.text(lx, ly, lab, color=color, fontsize=9, weight="bold")


fig, axs = plt.subplots(1, 3, figsize=(22, 7.5))
axis = axs[0]
line(axis, [25, 60, 115, 155, 200], [8.4e6, 5.7e6, 2.8e6, 1.0e6, 0.3e6], "#f5deb3", "GB300 NVL72", 65, 5.6e6)
line(axis, [25, 35, 50, 70, 115], [1.35e6, 0.9e6, 0.4e6, 0.15e6, 0.02e6], "#9acd32", "H200 NVL8", 22, 1.6e6)
line(axis, [75, 100, 125, 150, 185], [0.6e6, 0.4e6, 0.2e6, 0.1e6, 0.05e6], "white", "Competition", 68, 0.75e6)
axis.annotate("", (115, 2.8e6), (115, 0.4e6), arrowprops=dict(arrowstyle="->", ls="--", color="w"))
axis.text(125, 3.8e6, "50X\nHigher\nPerf / Watt", fontsize=14, weight="bold", ha="center")
axis.set_xlim(0, 200)
axis.set_ylim(0, 9e6)
axis.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
axis.set_title("1. Tokens per Watt Drives Factory Revenue")
axis.set_xlabel("Interactivity (TPS/User)")
axis = axs[1]
line(axis, [25, 30, 40, 48, 60, 75, 90, 110], [0.15, 0.25, 0.35, 0.6, 1.1, 1.6, 2.6, 4.3], "#9acd32", "H200 NVL8", 110, 4.1)
line(axis, [75, 100, 115, 127, 138], [0.27, 0.38, 0.6, 2.3, 3.9], "white", "Competition", 140, 3.4)
line(axis, [25, 75, 120, 155, 200], [0.03, 0.05, 0.12, 0.3, 1.65], "#f5deb3", "GB300 NVL72", 130, 1.3)
axis.annotate("", (118, 0.3), (118, 3.3), arrowprops=dict(arrowstyle="->", ls="--", color="w"))
axis.text(118, 3.45, "35X\nLower\nCost", fontsize=14, weight="bold", ha="center")
axis.set_xlim(0, 200)
axis.set_ylim(0, 4.5)
axis.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("${x:.2f}"))
axis.set_title("2. Performance Drives Token Cost")
axis.set_xlabel("Interactivity (TPS/User)")
axis = axs[2]
x = [62, 143, 214, 305, 315]
y = [25.0, 20.65, 12.9, 9.85, 8.95]
xx = np.linspace(62, 315, 300)
axis.plot(xx, P(x, y)(xx), color="#3cb043", lw=2.5)
axis.plot(x, y, "o", color="#3cb043")
for xi, yi in zip(x, y):
    axis.text(xi, yi + 0.5, "TEP4", fontsize=8, ha="center")
axis.text(150, 21.3, "B200 (SGLang)", color="w", bbox=dict(fc="#2e7d32", ec="none"))
axis.set_xlim(0, 350)
axis.set_ylim(8, 28)
axis.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:.0f}M"))
axis.set_title("3. Muse Spark Open 816B Agentic Total Tokens per $1 TCO vs. P90 Interactivity", fontsize=10)
axis.set_xlabel("P90 Interactivity (tok/s/user)")
axis.set_ylabel("Total Tokens per $1 TCO (tok/$)")
for axis in axs:
    axis.grid(alpha=0.25)
fig.text(
    0.5,
    0.01,
    "Reproduction en code. Points relevés à l'œil sur la photo GTC (DeepSeek R1 0528, FP4, 1K/1K) "
    "et l'image SemiAnalysis (B200, 1,73 $/chip/h). Valeurs approximatives.",
    ha="center",
    fontsize=9,
    color="#aaa",
)
fig.tight_layout(rect=[0, 0.03, 1, 1])
OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / "trois-reproduits.png", dpi=130)
