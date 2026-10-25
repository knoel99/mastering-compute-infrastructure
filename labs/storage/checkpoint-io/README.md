# Lab 8.3 — Coût d'un checkpoint

Écrit des états de 16 à 128 Mio sous trois stratégies (écriture normale, `fsync` + renommage atomique, `O_DIRECT`), mesure la copie
« snapshot » d'un checkpoint asynchrone, ajuste $T = \alpha + S/B$, puis confronte un **modèle de surcoût** à une boucle d'entraînement simulée.

## Ce qui est réel, ce qui est simulé

| Élément | Statut |
|---|---|
| Écritures, `fsync`, `rename`, `O_DIRECT`, compteur `write_bytes` de `/proc/self/io` | **réel**, sur le disque virtuel de la VM (ext4) |
| Copie « snapshot » vers un tampon hôte | **réel** (mémoire hôte) ; **remplace** la copie GPU vers hôte, il n'y a pas de GPU |
| Pas d'entraînement de 20 ms | **simulé** (`time.sleep`) |
| Stockage « lent » à 200 Mio/s (partie B) | **simulé** : l'écrivain se bride lui-même (`throttle_mbps`) |
| Écrivains parallèles (partie C) | **réel**, mais sur **un seul** disque virtuel : cela mesure la contention, pas le passage à l'échelle d'un système de fichiers parallèle |

## Fichiers

- `ckpt_io.py` : écritures, `AsyncCheckpointer` (un seul tampon de préparation, réutilisé ; une seule persistance en vol), boucle simulée, ajustement α-β.
- `bench_ckpt.py` : parties A, B, C et D (informative : première copie dans un tampon neuf contre seconde copie), sortie JSON optionnelle.
- `test_ckpt_io.py` : 11 tests (un échec d'écriture ne laisse aucun fichier final partiel et garde la version précédente ; relecture octet par octet des trois modes ; une écriture `O_DIRECT` non alignée échoue avec `EINVAL` (test sauté sur `tmpfs`) ; l'ajustement retrouve des paramètres synthétiques ; une seule persistance en vol ; erreurs propagées).
- `verify.sh`.

Le protocole d'écriture complet (somme de contrôle, manifeste, reprise) est celui du module 10, lab `labs/fault-tolerance/atomic-checkpoint` ; ce lab ne mesure que le **coût**.

```bash
export PYTHON=/chemin/vers/python
bash verify.sh        # environ 35 s
python3 bench_ckpt.py --dir /mnt/scratch   # tester un autre système de fichiers (O_DIRECT doit y être accepté)
```

Sortie réelle (VM de test à 4 vCPU, 2026-10-24) :

```
OK checkpoint-io: fit B = 518 MiB/s, error 13 %; sync 28.3 % vs model 25.7 %; async 1.4 % vs model 0.4 %
```

## Ce que `verify.sh` affirme

Relecture exacte ; erreur médiane de l'ajustement sous 60 % ; `fsync` + renommage coûte plus de 1,2 fois une écriture normale à la plus grande taille ; `write_bytes` est du même ordre que la taille ;
dans la boucle simulée, le surcoût synchrone est à moins de 35 % (relatif) ou 15 points du modèle, l'asynchrone à moins de 10 points, et l'asynchrone bloque moins de la moitié du synchrone. Aucune durée absolue.

## Réserves et hypothèses (non vérifiées)

- La première copie dans un tampon neuf de 256 Mio coûte de l'ordre de 1 s sur cette VM, contre environ 25 ms ensuite (partie D, affichée, non testée). Hypothèse non vérifiée : la mémoire invitée n'est attribuée par l'hôte qu'au premier accès. D'où le tampon de préparation réutilisé et la répétition d'échauffement.
- L'écart entre la partie A (environ 500 Mio/s avec `fsync`) et la partie C (environ 800 à 950 Mio/s en agrégé) vient peut-être du renommage qui remplace un fichier existant sur un système monté avec l'option `discard` ; hypothèse non testée.
- Les mesures varient d'une exécution à l'autre (l'erreur médiane de l'ajustement a valu de 2 % à 13 % sur nos exécutions) : on rapporte des médianes, jamais un minimum.
- Avec trois tailles seulement, l'ajustement de la partie A peut donner un α négatif (−3,5 ms dans la sortie citée sur la page) ou positif (+3,6 et +4,0 ms dans d'autres exécutions) ; `fit_alpha_beta` le ramène à 0 sans refaire l'ajustement. Seul B se lit.
- `verify.sh` écrit ses fichiers dans `$HOME` si le répertoire temporaire est en mémoire (`tmpfs`), car `O_DIRECT` et le compteur `write_bytes` n'ont pas de sens sur de la mémoire.
