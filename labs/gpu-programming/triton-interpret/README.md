# Lab 4.3 — Triton en mode interpréteur

**Type : `sandbox`.** **Vérifié ici (Triton 3.8.0 installé depuis PyPI, `TRITON_INTERPRET=1`) :** addition, addition fusionnée avec ReLU, softmax par ligne et produit matriciel par tuiles, comparés à PyTorch ; comptage exact du trafic mémoire du softmax en cinq opérations. **Non exécuté ici :** `bench_gpu.py` (octet-compilé seulement) : vitesse et auto-réglage demandent un GPU.

Selon la documentation de Triton, l'interpréteur court-circuite la compilation et simule chaque instance de programme en séquence avec des équivalents NumPy. Il valide la logique et les masques ; il ne dit rien de la performance.

~~~bash
python3 -m pip install triton torch pytest
TRITON_INTERPRET=1 python3 -m pytest -q test_triton_kernels.py
python3 traffic.py 4096 2048
./verify.sh
~~~

## Observation datée (2026-10-25, Triton 3.8.0, Linux sans GPU)

- `@triton.autotune` **ne s'exécute pas** dans l'interpréteur : l'appel lève `RuntimeError: 0 active drivers ([]). There should only be one.` L'auto-réglage vit donc dans `bench_gpu.py`.
- Sans masque, l'interpréteur **ne lève pas d'exception** : en supprimant le masque de `add_kernel`, le processus Python s'est arrêté brutalement (`Fatal Python error: Segmentation fault` à un essai, `Fatal Python error: Aborted` à l'autre) pour une longueur qui n'est pas un multiple du bloc.
- L'addition de deux tenseurs `bfloat16` **ne lève aucune exception** dans cette version, mais rend des valeurs fausses (1 + 1 donne environ 1,7e38) : la documentation de débogage a raison de signaler que l'interpréteur ne prend pas en charge `bfloat16`. Convertissez en `float32` ; relisez la documentation de votre version.
- `python3 probe_observations.py` refait ces trois observations sur votre installation (elles dépendent de la version de Triton : `verify.sh` ne les affirme pas).

## Contenu

| Fichier | Rôle |
|---|---|
| `triton_kernels.py` | quatre noyaux et leurs enveloppes hôte |
| `traffic.py` | registre des éléments lus et écrits par chaque opération du softmax non fusionné |
| `test_triton_kernels.py` | 13 tests |
| `probe_observations.py` | refait les trois observations datées (bfloat16, auto-réglage, masque absent) ; rien n'est affirmé par `verify.sh` |
| `bench_gpu.py` | branche GPU : `triton.testing.do_bench`, `@triton.autotune` (**non exécuté**) |
