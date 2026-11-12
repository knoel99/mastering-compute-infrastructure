import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

from workstation_data import load_rows

OUT = Path(__file__).resolve().parent / "charts"
rows = load_rows()
nv = {
    "H200 NVL8 (Nvidia, DeepSeek R1)": ([25, 30, 40, 48, 60, 75, 90, 110], [0.15, 0.25, 0.35, 0.6, 1.1, 1.6, 2.6, 4.3], "#9acd32"),
    "Concurrence (Nvidia, DeepSeek R1)": ([75, 100, 115, 127, 138], [0.27, 0.38, 0.6, 2.3, 3.9], "#888888"),
    "GB300 NVL72 (Nvidia, DeepSeek R1)": ([25, 75, 120, 155, 200], [0.03, 0.05, 0.12, 0.3, 1.65], "#e0a050"),
}
sa = ([62, 143, 214, 305, 315], [25.0, 20.65, 12.9, 9.85, 8.95])
fig, ax = plt.subplots(figsize=(13, 8))
for name, (x, prices, color) in nv.items():
    ax.plot(x, [1 / value for value in prices], "o-", color=color, label=name)
ax.plot(*sa, "o-", color="#2ca02c", lw=2.5, label="B200 SGLang (SemiAnalysis, Muse Spark Open 816B)")
for name, color, _hourly, curve in rows:
    xs = [x for x, _y in curve]
    ys = [y for _x, y in curve]
    ax.plot(xs, ys, "s-" if len(curve) > 1 else "s", color=color, ms=9, label=f"{name} (nos calculs, en €)")
ax.set_yscale("log")
ax.set_xlim(0, 350)
ax.grid(alpha=0.3, which="both")
ax.set_xlabel("Interactivité (tokens/s par utilisateur)")
ax.set_ylabel("Millions de tokens par dollar ou par euro (échelle log)")
ax.set_title(
    "Tokens par unité de coût selon l'interactivité, toutes sources\n"
    "Nvidia : lecture visuelle de la diapo GTC (coût $/M tokens inversé, valeurs basses imprécises) · "
    "SemiAnalysis : lecture visuelle\n"
    "Workstations : prix HT sur 3 ans, 24h/24, 0,2001 €/kWh",
    fontsize=10,
)
ax.legend(fontsize=8, loc="upper right")
fig.tight_layout()
OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / "graphique-ensemble.png", dpi=130)
