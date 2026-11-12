# Brief: interpret Blackwell price curves (log + linear)

## Context
Kim (Inference Lead) fitted NVIDIA Blackwell SKUs: GeForce RTX 50, RTX PRO, B100/B200/B300, DGX Spark/Station, NVL72/GPU.
Prices in EUR converted to USD at 1 USD = 0.893 EUR (2026-10-23).

## Key fitted parameters already computed

### VRAM ∝ P^α (power law, log–log)
| Panel | n | α | R² |
| all | 22 | 0.641 | 0.878 |
| no Spark/Station | 20 | 0.649 | 0.930 |
| GeForce only | 8 | 0.652 | 0.899 |
| PRO only | 7 | 0.832 | 0.987 |
| HBM + Station | 6 | 0.281 | 0.259 |
| HBM no Station | 5 | 0.744 | 0.586 |

### $/GB vs P — per regime
GeForce: $/GB = -55.9 + 36.7·log10(P) R²=0.70 | linear: 32.5+0.0177·P R²=0.61 | power: 4.78·P^0.35 R²=0.68
PRO: $/GB = -61.3 + 54.5·log10(P) R²=0.81 | linear: 119.9+0.0031·P R²=0.71 | power: 33.2·P^0.17 R²=0.80
HBM: $/GB = -1910 + 456·log10(P) R²=0.78 | linear: 49.1+0.0034·P R²=0.87 | power: 0.091·P^0.72 R²=0.84
Global $/GB power: 4.80·P^0.36 R²=0.82

### Bandwidth — piecewise on log P (NOT one power law)
GeForce: BW = -3431 + 1547·log10(P) R²=0.93
PRO: BW = -4684 + 1551·log10(P) R²=0.99  (same slope ≈ +1.55 TB/s per decade)
HBM: plateau ≈ 7850 GB/s

## Manufacturing hypothesis already proposed
GDDR7 = discrete BGA on PCB; HBM = TSV stack + CoWoS (Epoch B200: HBM ~$2900, CoWoS ~$1100, yield scrap ~$1000). α differences = process jump + pricing tiers, not silicon physics law.

## Your job
1. Open every attached chart (log AND linear).
2. For each chart family (VRAM, $/GB, BW, TDP if present): state what the axes mean, what a good fit looks like, and give physical/industrial meaning to each parameter (α, intercept, slope per decade, R²).
3. Contrast log-X linear (Y = a + b log P) vs power (Y ∝ P^α) vs linear-X — when each is the right reading.
4. Search web (<90 days preferred) for corroborating industrial interpretations; cite with dates.
5. Deliver a single markdown report `interpretations-blackwell-curves.md` with: verdict per chart, parameter glossary, manufacturing link, what NOT to overclaim.
6. French or English OK; prefer French for Kim.
