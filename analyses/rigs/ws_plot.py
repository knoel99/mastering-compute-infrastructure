import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from workstation_data import load_rows

OUT = Path(__file__).resolve().parent / "charts"
rows = load_rows()
ymax = max(y for _name, _color, _hourly, curve in rows for _x, y in curve) * 1.25
fig, axs = plt.subplots(1, 3, figsize=(22, 7.5), sharey=True)
titles = [
    "1. Points mesurés par machine",
    "2. Même chose + « serveur parfait » de chaque machine",
    "3. Courbes lissées (seulement où il y a ≥ 2 points)",
]
for k, axis in enumerate(axs):
    for name, color, _hourly, curve in rows:
        xs = [x for x, _y in curve]
        ys = [y for _x, y in curve]
        axis.scatter(xs, ys, color=color, s=60, zorder=3, label=name)
        if len(curve) > 1:
            if k == 2:
                t = np.linspace(0, 1, 100)
                xx = xs[0] + (xs[1] - xs[0]) * t
                yy = ys[0] + (ys[1] - ys[0]) * (3 * t**2 - 2 * t**3)
                axis.plot(xx, yy, color=color, lw=2.5)
            else:
                axis.plot(xs, ys, color=color, lw=1.2, ls=":")
        if k >= 1:
            ref = max(ys)
            axis.hlines(ref, 0, 120, colors=color, ls="--", lw=1.2, alpha=0.8)
        for x, y in curve:
            axis.annotate(
                f"{y:.1f} M",
                (x, y),
                textcoords="offset points",
                xytext=(6, 6),
                fontsize=8,
                color=color,
            )
    axis.set_xlim(0, 120)
    axis.set_ylim(0, ymax)
    axis.grid(alpha=0.3)
    axis.set_xlabel("Interactivité (tokens/s par utilisateur)")
    axis.set_title(titles[k], fontsize=12)
axs[0].set_ylabel("Tokens par euro de coût total (millions)")
axs[0].legend(loc="upper right", fontsize=9)
fig.suptitle(
    "Workstations WRX90 et DGX Station : tokens par euro selon l'interactivité\n"
    "Hypothèses : prix HT amorti sur 3 ans, machine pleine 24h/24, "
    "électricité 0,2001 €/kWh à la conso génération ; "
    "modèles et formats différents selon la machine",
    fontsize=12,
)
fig.tight_layout(rect=[0, 0, 1, 0.9])
OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / "trois-graphiques-workstations.png", dpi=130)
