import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

from workstation_data import load_rows

OUT = Path(__file__).resolve().parent / "charts"
rows = load_rows()
sa = [(62, 25.0), (143, 20.65), (214, 12.9), (305, 9.85), (315, 8.95)]
nv = [
    ("GB200 · DeepSeek-R1", 75, 10.0, "#76b900"),
    ("GB300 · modèle non nommé", 116, 8.13, "#2f6f00"),
]
fig, axs = plt.subplots(1, 3, figsize=(22, 7.5))
axis = axs[0]
for name, color, _hourly, curve in rows:
    xs = [x for x, _y in curve]
    ys = [y for _x, y in curve]
    axis.scatter(xs, ys, color=color, s=60, zorder=3, label=name)
    if len(curve) > 1:
        axis.plot(xs, ys, color=color, ls=":", lw=1.2)
    for x, y in curve:
        axis.annotate(
            f"{y:.2f} M",
            (x, y),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8,
            color=color,
        )
axis.set_xlim(0, 120)
axis.set_ylim(0, 4.5)
axis.set_ylabel("Millions de tokens par euro")
axis.set_title("1. Workstations (nos calculs, en euros)")
axis.legend(fontsize=8, loc="lower left")
axis = axs[1]
x, y = zip(*sa)
axis.plot(x, y, "o-", color="#1f77b4")
axis.axhline(25, ls="--", color="gray", label="Serveur parfait (25)")
for point in sa:
    axis.annotate(f"{point[1]:.2f} M", point, textcoords="offset points", xytext=(6, 6), fontsize=8)
axis.set_xlim(0, 350)
axis.set_ylim(0, 28)
axis.set_ylabel("Millions de tokens par dollar")
axis.set_title("2. SemiAnalysis · B200 SGLang (lecture visuelle)")
axis.legend(fontsize=8)
axis = axs[2]
for name, x, y, color in nv:
    axis.scatter(x, y, color=color, s=60, label=name)
    axis.annotate(f"{y:.2f} M", (x, y), textcoords="offset points", xytext=(6, 6), fontsize=8)
axis.axhline(10, ls="--", color="gray", label="Serveur parfait (10)")
axis.set_xlim(0, 350)
axis.set_ylim(0, 28)
axis.set_ylabel("Millions de tokens par dollar")
axis.set_title("3. Nvidia · blog oct. 2025 et page inférence")
axis.legend(fontsize=8)
for axis in axs:
    axis.grid(alpha=0.3)
    axis.set_xlabel("Interactivité (tokens/s par utilisateur)")
fig.suptitle(
    "Tokens par unité de coût selon l'interactivité · workstations : "
    "prix HT sur 3 ans, 24h/24, électricité 0,2001 €/kWh",
    fontsize=12,
)
fig.tight_layout(rect=[0, 0, 1, 0.94])
OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / "trois-graphiques-comparaison.png", dpi=130)
