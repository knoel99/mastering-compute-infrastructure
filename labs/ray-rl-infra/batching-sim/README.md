# Lab 11.4 — Batching statique, batching continu et cache KV paginé

Un moteur d'inférence **simulé** (`sim.py`) compare trois façons de servir les mêmes requêtes : lot statique avec mémoire réservée, lot continu avec mémoire réservée, lot continu avec cache KV paginé. Il sert au chapitre 9 du module 11 (exemples 9.3 et 9.5). Le temps est **simulé** : aucune assertion ne dépend d'une horloge, et la charge vient d'un générateur congruentiel à graine fixe, identique sur toute machine.

```
sim.py        moteur jouet : politiques "static" et "continuous", cache "reserve" et "paged" (préemption par recalcul),
              charge hors ligne (vague de rollouts) ou en ligne (arrivées de Poisson), balayage SLO et goodput
test_sim.py   11 tests structurels ; bibliothèque standard seule (python3 test_sim.py), ou pytest
verify.sh     tests, table hors ligne, balayage en ligne, « OK batching-sim »
```

```bash
PYTHON=python3 bash verify.sh                  # quelques secondes, aucun GPU, aucune dépendance
python3 sim.py --kv-budget 65536               # cache plus grand : la pagination ne change plus rien
python3 sim.py --sweep --tpot-slo-ms 6         # SLO plus serré sur le TPOT : le goodput baisse
```

## Le modèle

- Une itération fait avancer chaque séquence en cours d'un jeton. Sa durée est la borne du roofline de l'exemple 9.2 : poids (16,38 Go, Qwen3-8B en BF16) et cache KV lus une fois, à 3,35 To/s (H100 SXM), plus 16,6 µs par jeton de prompt traité dans l'itération (2 × 8,19·10⁹ FLOP par jeton à 989 TFLOP/s, une borne basse).
- `static` : un lot se forme quand le moteur est vide et tourne jusqu'à la fin de sa **plus longue** séquence.
- `continuous` : après chaque itération, les séquences finies sortent et les requêtes en attente entrent, s'il reste une place et assez de cache (ordonnancement par itération d'Orca).
- `reserve` : chaque requête réserve prompt + `max_tokens` (1 024) jetons de cache dès son admission.
- `paged` : chaque requête occupe des blocs de 16 jetons alloués au fil de la génération ; s'il manque un bloc, la séquence la plus récente est préemptée, puis recalculée (prompt et jetons déjà produits) à sa réadmission.

## Sortie réelle (2026-10-25, Python 3.13, graine 1 hors ligne, graine 3 en ligne)

```
offline workload: 64 requests at t=0, seed 1, 15679 output tokens ; max_seqs=32, KV budget=16384 tokens
    policy       kv  steps  time s   tok/s slot use mean run max run preempt
    static  reserve   4967   25.00     627     0.10      3.2      12       0
continuous  reserve   1889    9.95    1575     0.26      8.3      12       0
continuous    paged   1114    6.16    2544     0.44     14.1      32       0
goodput (continuous, paged): 16 req/s on 1 simulated GPU (highest swept rate meeting the target)
```

## Limites

- Ce n'est pas un moteur : pas de noyau réel, pas d'activations, pas de graphes CUDA, pas de parallélisme. La durée d'une itération est une **borne basse** ; un vrai moteur est plus lent, et ses rapports peuvent différer.
- Le cache de 16 384 jetons est volontairement petit pour que la mémoire limite le lot ; un vrai GPU de 80 Go en offre environ 388 000 pour ce modèle (exemple 9.1).
- Pas de cache de préfixes ni de prefill découpé : ce sont les pistes de « Pour aller plus loin ».
