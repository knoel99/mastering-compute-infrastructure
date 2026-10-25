# Lab 4.4 — Lire une trace de profil

**Type : `sandbox`.** **Vérifié ici :** profil PyTorch Profiler **sur CPU** d'un petit transformeur (2 couches, d = 128, séquence 64, lot 8), export de la trace Chrome, lecture de la trace. **Synthétique, non mesuré :** les trois traces de `fixtures/` imitent la structure d'une trace GPU de Kineto avec des durées choisies pour illustrer trois goulots. Elles sont **fabriquées à la main** par `make_fixture.py` (le champ `otherData.synthetic` vaut `true`) : elles n'apportent aucune information sur un vrai GPU.

~~~bash
python3 profile_cpu.py --out trace.json              # tableau des opérateurs ; trace à ouvrir dans https://ui.perfetto.dev
python3 trace_report.py trace.json                   # temps propre par opérateur
python3 trace_report.py fixtures/launch_bound.json   # verdict : LAUNCH-BOUND
python3 make_fixture.py /tmp/fixtures                # régénère les fixtures (octet-identiques)
./verify.sh
~~~

## Ce que le test garantit (sans chronométrage)

- Les appels d'opérateurs découlent du modèle : 8 `aten::addmm`, 16 `aten::mm`, 12 `aten::bmm`.
- Les FLOP du profileur pour `mm + addmm + bmm` valent exactement 3 fois les FLOP analytiques d'une passe avant (la passe arrière fait deux produits par produit avant).
- Les temps propres s'additionnent à la durée de l'étape annotée : aucun double comptage.
- Le verdict des fixtures : lancement, GPU, transferts.

## Transposition au profil GPU (documentée, non exécutée)

~~~bash
# sur une machine à GPU NVIDIA
nsys profile -o report python train.py                       # chronologie : CPU, API CUDA, noyaux, copies
nsys stats report.nsys-rep                                   # tables récapitulatives
ncu -k regex:gemm -c 1 -o kernel_report python train.py      # un noyau en détail : débit, occupation, mémoire
~~~

Les seuils du verdict de `trace_report.py` (50 µs, 60 %, 85 %, 50 %) sont des heuristiques de ce cours, pas des règles de NVIDIA.
