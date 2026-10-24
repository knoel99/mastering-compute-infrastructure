# Lab 14.3 — Détecteur de job bloqué

Deux parties dans un même dossier.

## Partie A — Détecteurs sur séries **simulées**

`sim.py` produit, toutes les 15 s, ce que verrait Prometheus pour un entraînement de 6 h : compteur de pas, phase (`train`, `ckpt`, `eval`), utilisation GPU, activité tensorielle, puissance. Trois familles de runs : sains, avec un blocage (`hang`), avec un plantage (`crash`).

**Tout est supposé, rien n'est mesuré.** Les durées des pauses (checkpoint de 30 à 90 s, 10 % de checkpoints lents de 120 à 420 s, évaluations de 120 à 300 s, blocages de données de 20 à 200 s) sont des choix de ce lab. La signature du blocage (utilisation haute, tensor à zéro, battement de cœur toujours actif) est l'hypothèse du cours, rapportée par des utilisateurs mais non mesurée sur GPU par l'auteur. Le lab montre ce que ces hypothèses impliquent pour un détecteur ; **mesurez vos pauses avant de reprendre un seuil**.

`detectors.py` : `UtilLow` (naïf), `TensorIdle`, `StepStall`, `Heartbeat`, `PhaseAware`, `AnyOf`. `evaluate.py` imprime le tableau de comparaison et le balayage de fenêtre (150 runs sains + 150 blocages + 100 plantages, graines fixes, donc reproductible).

## Partie B — Un **vrai** blocage, sur CPU

`real_hang.py` lance deux processus `torch.distributed` (backend `gloo`, CPU). Au pas 150, le rang 1 s'arrête avant la collective (`time.sleep`), le rang 0 reste bloqué dans `all_reduce`. Un observateur à l'horloge réelle (`watch.py`) voit le compteur de progression stagner 3 s, déclenche l'alarme, puis le programme envoie `SIGUSR1` : `faulthandler` écrit la pile de chaque rang. On retrouve le rang fautif de deux façons : sa pile (dans `time.sleep`) et le dernier pas où chaque rang est entré dans la collective.

**Réel** : processus, `gloo`, collective bloquée, signal, piles Python, horloge. **Pas le cas GPU** : `gloo` n'est pas NCCL, il n'y a pas de GPU, et le blocage est injecté volontairement ; la signature « utilisation haute » n'est donc pas exercée ici.

## Partie C — Système ou modèle ?

`regress.py` enregistre trois runs **simulés** de 1 200 pas (référence, `thermal` : fréquence du GPU le plus lent à 65 % dès le pas 600, `lrbug` : taux d'apprentissage trois fois trop grand dès le pas 600) par l'API **réelle** de MLflow (base SQLite temporaire), puis les classe en comparant débit, perte à pas égal et fréquence minimale à la référence. `drift.py` compare un CUSUM à un seuil fixe sur une baisse de 3 % (séries simulées). Prérequis : `pip install mlflow-skinny sqlalchemy alembic` ; sans MLflow, la partie C s'annonce « SKIPPED » et ne valide rien. MLflow 3.17.2 refuse le magasin de fichiers (mode maintenance) : d'où SQLite.

## Lancer

```bash
export PYTHON=/chemin/vers/python      # torch (CPU suffit), pytest, mlflow-skinny, sqlalchemy, alembic
bash verify.sh                          # ~35 s ; aucune assertion sur une durée
python3 evaluate.py --quick             # tableau en 2 s
python3 real_hang.py                    # la partie B seule (~8 s)
```

## Branches vérifiées

Parties A, B et C exécutées par l'auteur le 2026-10-24 sur la VM du bac à sable (4 vCPU, sans GPU). **Non vérifié** : tout ce qui concerne NCCL et de vrais GPU (le comportement du watchdog NCCL, la signature de l'utilisation GPU pendant un blocage).

## Pour aller plus loin

1. Ajoutez à `sim.py` une phase de « redémarrage après préemption » de 2 à 10 minutes : quel détecteur casse, et que faut-il ajouter au contrat de l'entraîneur ?
2. Mesurez les durées de checkpoint de votre propre entraîneur et remplacez les lois de `sim.pauses`.
3. Sur un nœud GPU, activez le *flight recorder* de PyTorch (`TORCH_NCCL_TRACE_BUFFER_SIZE`, `TORCH_NCCL_DUMP_ON_TIMEOUT`) et comparez son verdict à celui de la partie B.
