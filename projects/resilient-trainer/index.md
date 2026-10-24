---
title: "Projet 3 — Entraîneur tolérant aux pannes"
subtitle: "Projet 3 · 24 h · modules : storage, distributed-training, fault-tolerance"
description: "Un entraînement qui survit à kill -9, à une écriture de checkpoint interrompue, à un checkpoint corrompu et à un processus bloqué, avec 19 tests qui le prouvent."
project:
  id: resilient-trainer
  number: 3
  hours: 24
  modules: [storage, distributed-training, fault-tolerance]
badges:
  - {label: "Portfolio", class: core}
  - {label: "Code de départ et solution vérifiés (CPU)", class: verified}
---

## Contexte et objectif {#contexte}

Un entraînement qui dure des semaines sur des milliers de GPU sera interrompu, c'est une certitude statistique et non un risque. Le rapport technique de Llama 3 donne l'ordre de grandeur : « During a 54-day snapshot period of pre-training, we experienced a total of 466 job interruptions », dont 47 prévues et « the remaining 419 were unexpected » ([Llama Team, 2024](https://arxiv.org/abs/2407.21783)). Environ 78 % des interruptions imprévues sont attribuées à des problèmes matériels confirmés ou soupçonnés, et les GPU en forment la première catégorie, avec 58,7 %.

Cela fait 419 pannes en 1 296 heures : une toutes les 3,1 heures en moyenne, soit un intervalle moyen entre pannes (MTBF) d'environ 11 100 secondes pour l'ensemble de la machine. Le même rapport annonce pourtant « higher than 90% effective training time », avec une intervention manuelle importante seulement trois fois (« only three times during this period »). L'écart entre ces deux faits, c'est l'ingénierie de la reprise automatique : c'est elle que vous construisez ici, à petite échelle.

::: key
[Objectif du projet]{.tag} Écrire un entraîneur et son superviseur tels que, après une panne quelconque, l'entraînement reprend **à l'identique** (mêmes pertes à chaque pas, au bit près), sans intervention humaine, et être capable de chiffrer ce que la tolérance aux pannes coûte et rapporte.
:::

Le projet se fait sur CPU, avec un petit réseau de neurones et PyTorch. Ce choix est délibéré : les mécanismes (écriture atomique, somme de contrôle, état complet, détection de blocage, intervalle de checkpoint) sont les mêmes qu'à grande échelle, et chaque panne y est **reproductible** par une variable d'environnement. À 8 000 GPU on ne peut pas provoquer une panne à la demande ; ici, on le peut, et c'est ce qui permet d'écrire des tests.

Le code de départ est volontairement naïf. Il fonctionne un jour normal et perd l'entraînement un mauvais jour, comme le font beaucoup de scripts écrits à la hâte. Votre travail consiste à le rendre fiable et à **démontrer** qu'il l'est.

<figure class="fig">
<svg viewBox="0 0 640 170" role="img" aria-labelledby="yd-t yd-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="yd-t">Une panne entre deux checkpoints</title>
<desc id="yd-d">Frise du temps : deux périodes de calcul de durée T séparées par des checkpoints de durée C. Une panne survient en cours de troisième période ; le calcul depuis le dernier checkpoint est perdu, puis le redémarrage coûte R et la période est recalculée.</desc>
<line x1="20" y1="120" x2="620" y2="120" stroke="currentColor" stroke-opacity=".3"/>
<rect x="30" y="92" width="100" height="28" fill="currentColor" fill-opacity=".14" stroke="currentColor"/>
<rect x="130" y="92" width="14" height="28" fill="var(--accent)" stroke="currentColor"/>
<rect x="144" y="92" width="100" height="28" fill="currentColor" fill-opacity=".14" stroke="currentColor"/>
<rect x="244" y="92" width="14" height="28" fill="var(--accent)" stroke="currentColor"/>
<rect x="258" y="92" width="80" height="28" fill="none" stroke="currentColor" stroke-dasharray="4 3"/>
<line x1="258" y1="92" x2="338" y2="120" stroke="currentColor" stroke-opacity=".5"/>
<line x1="258" y1="120" x2="338" y2="92" stroke="currentColor" stroke-opacity=".5"/>
<path d="M338 78 L338 128" stroke="currentColor" stroke-width="3"/>
<rect x="338" y="92" width="40" height="28" fill="currentColor" fill-opacity=".35" stroke="currentColor"/>
<rect x="378" y="92" width="100" height="28" fill="currentColor" fill-opacity=".14" stroke="currentColor"/>
<rect x="478" y="92" width="14" height="28" fill="var(--accent)" stroke="currentColor"/>
<rect x="492" y="92" width="100" height="28" fill="currentColor" fill-opacity=".14" stroke="currentColor"/>
<text x="80" y="84" text-anchor="middle" font-size="12" fill="currentColor">calcul T</text>
<text x="137" y="140" text-anchor="middle" font-size="12" fill="currentColor">C</text>
<text x="251" y="140" text-anchor="middle" font-size="12" fill="currentColor">C</text>
<text x="298" y="150" text-anchor="middle" font-size="12" fill="currentColor">calcul perdu</text>
<text x="338" y="68" text-anchor="middle" font-size="12" font-weight="700" fill="currentColor">panne</text>
<text x="358" y="150" text-anchor="middle" font-size="12" fill="currentColor">R</text>
<text x="428" y="84" text-anchor="middle" font-size="12" fill="currentColor">même période recalculée</text>
</svg>
<figcaption>Une panne entre deux checkpoints : le travail depuis le dernier checkpoint terminé est perdu, puis le redémarrage coûte R. En moyenne la panne tombe au milieu d'une période. Cette frise est le modèle du jalon 5.</figcaption>
</figure>

### Prérequis de connaissances {#pre}

Vous devez savoir lire un entraînement PyTorch (modèle, optimiseur, boucle, `state_dict`) et vous servir d'un terminal Linux. Les notions de signaux et de groupes de processus sont rappelées dans le [module Slurm](../../courses/slurm/index.html), chapitre 1, et son lab 5.1 montre un premier checkpoint sur signal. Les modules « stockage », « entraînement distribué » et « tolérance aux pannes » du parcours approfondissent ce que ce projet pratique ; vous pouvez le faire avant de les lire, quitte à y revenir ensuite.

## Cahier des charges {#cahier}

Le dossier `labs/projects/resilient-trainer/` contient `starter/` (à compléter), `reference/` (solution à consulter **après** votre tentative), `tests/` (19 tests) et `verify.sh`. Les exigences, chacune liée à un test :

| ID | Exigence | Test qui la vérifie |
|---|---|---|
| R1 | Écriture **atomique** : jamais de fichier de checkpoint à moitié écrit sous son nom final ; fichier temporaire puis `os.replace`, avec `fsync` du fichier et du dossier | `test_no_temporary_file_left`, `test_torn_checkpoint_write_is_survived` |
| R2 | **Intégrité** : une somme de contrôle dans le fichier ; un checkpoint corrompu ou tronqué est écarté et le précédent est utilisé | `test_flipped_byte_falls_back_to_previous`, `test_corrupt_latest_checkpoint_falls_back` |
| R3 | **État complet** : poids, état de l'optimiseur, états des générateurs aléatoires (PyTorch et Python), numéro de pas | `test_optimizer_and_rng_state_are_saved`, `test_kill9_resumes_bit_exactly` |
| R4 | **Rotation** : ne garder que les K derniers checkpoints valides, après que le nouveau est durable | `test_rotation_keeps_newest` |
| R5 | **Superviseur** : relance après un code de sortie non nul, au plus N fois, puis abandon avec le code 1 | `test_gives_up_after_max_restarts` |
| R6 | **Blocage** : un entraîneur dont le fichier de pulsation n'est plus touché depuis le délai fixé est tué (tout son groupe de processus) puis relancé | `test_hung_trainer_is_killed_and_restarted` |
| R7 | **Arrêt propre** : à la réception de SIGTERM, le superviseur le transmet à l'enfant, ne relance pas et sort avec 143 | `test_sigterm_stops_supervisor_and_child` |
| R8 | **Goodput** : la période de Young-Daly, le modèle du premier ordre et une simulation de Monte-Carlo en accord | `tests/test_goodput.py` (5 tests) |

L'entraîneur fourni, `train.py`, est identique dans `starter/` et `reference/`. Il contient trois crochets d'injection de panne, activés par la variable `FAULT` et déclenchés une seule fois par dossier de travail : `kill:N` (SIGKILL juste avant le pas N), `hang:N` (blocage éternel juste avant le pas N) et `torn:N` (arrêt brutal au milieu de l'écriture du checkpoint du pas N). Il est déterministe : le lot de données dépend uniquement du couple (graine, pas), et le réseau contient un *dropout*, qui consomme le générateur aléatoire global. C'est ce détail qui rend l'état des générateurs indispensable à la reprise exacte.

**Hors périmètre** du cœur du projet : l'entraînement multi-processus, les checkpoints répartis par rang, l'écriture asynchrone et le stockage objet. Ce sont des extensions.

## Jalons {#jalons}

| N° | Jalon | Durée | Preuve |
|---|---|---|---|
| 1 | Faire échouer le code de départ et **diagnostiquer chaque échec** | 2 h | sortie de `pytest` sauvegardée et un paragraphe de diagnostic par test en échec |
| 2 | Checkpoint durable : `pack`, `unpack`, `save`, `load_latest` | 5 h | les 8 tests de `tests/test_ckpt.py` passent |
| 3 | État complet et reprise exacte | 4 h | `test_kill9_resumes_bit_exactly` et `test_torn_checkpoint_write_is_survived` passent |
| 4 | Superviseur : relance, blocage, SIGTERM | 5 h | les trois tests du superviseur passent ; `supervisor.jsonl` d'une exécution avec blocage joint au dépôt |
| 5 | Goodput : modèle, simulation, mesure | 4 h | les 5 tests de `test_goodput.py` passent ; tableau du coût de checkpoint pour quatre tailles d'état |
| 6 | Rapport, ADR et runbook | 4 h | un `README`, un ADR d'une page, un runbook d'une page |

Commencez toujours par le jalon 1. Lancez les tests contre le code de départ et lisez **chaque** message d'échec avant d'écrire une ligne : l'exercice consiste à comprendre pourquoi un script ordinaire échoue, pas à deviner la solution.

~~~bash
cd labs/projects/resilient-trainer
export PYTHON=/chemin/vers/python-avec-torch     # PyTorch CPU suffit
IMPL=starter $PYTHON -m pytest -q tests/test_ckpt.py   # 5 échecs attendus au départ
IMPL=starter $PYTHON -m pytest -q tests                # 16 échecs sur 19 attendus
PYTHON=$PYTHON bash verify.sh                          # prouve référence verte, départ rouge
~~~

Le script `verify.sh` fait deux choses : il vérifie que la solution de référence passe les 19 tests, et que le code de départ en échoue au moins un. Un test qui passe aussi sur le code naïf ne prouve rien, et ce second contrôle le garantit.

## Livrables {#livrables}

Votre dépôt public contient :

- le code complété (`ckpt.py`, `supervisor.py`, `goodput.py`) et les tests, avec une commande unique qui les lance ;
- un `README.md` : le problème, le schéma des composants, les commandes pour reproduire, les résultats ;
- un **ADR** (*architecture decision record*) d'une page, décrit plus bas ;
- le tableau mesuré du coût de checkpoint et la sortie de `goodput.py` qui l'utilise ;
- un **runbook** d'une page : « l'entraînement ne repart pas après une panne, que vérifier, dans quel ordre ».

L'ADR doit trancher au moins quatre questions de conception, en nommant l'alternative écartée et pourquoi :

1. Où placer la somme de contrôle (dans le fichier, dans un fichier voisin, dans un manifeste) et ce que chaque choix garantit en cas de panne entre deux écritures ?
2. Combien de checkpoints garder, et que se passe-t-il si les K derniers sont tous corrompus ?
3. Pourquoi le superviseur détecte-t-il le blocage par la pulsation du programme plutôt que par un simple délai maximal d'exécution ?
4. Quelle période de checkpoint retenez-vous, avec quelles valeurs de C et de M, et quelle part de ces valeurs est mesurée plutôt que supposée ?

## Critères de réussite {#criteres}

Chaque critère est mesurable ; la commande qui le montre est indiquée.

- **Reprise exacte.** Après `FAULT=kill:57`, la perte de chaque pas 1 à 120 est identique, au bit près, à celle d'une exécution sans panne ; les pas 51 à 56 apparaissent deux fois dans `loss.jsonl`, avec la même valeur. Commande : `IMPL=starter pytest tests/test_resume.py -k kill9`.
- **Aucun checkpoint cassé sous son nom final.** Après `FAULT=torn:60`, le dernier `ckpt-*.pt` valide est celui du pas 50 et la relance reprend de 50. Commande : `pytest -k torn`.
- **Repli sur corruption.** Avec un octet du checkpoint 80 modifié, la relance reprend de 70 et `events.jsonl` nomme le fichier écarté. Commande : `pytest -k corrupt_latest`.
- **Détection de blocage bornée.** Avec `FAULT=hang:45` et `--stall-timeout 3`, le superviseur écrit un événement `stall_kill`, relance, et l'entraînement se termine avec la même trajectoire. Commande : `pytest -k hung`.
- **Goodput.** La simulation à la période T\* est à moins de 2 points de pourcentage du modèle du premier ordre, et T\* donne un meilleur goodput que 0,25 T\* et 4 T\*. Commande : `pytest tests/test_goodput.py`.
- **Mesure.** Le rapport donne le coût de checkpoint **mesuré** pour au moins trois tailles d'état (option `--pad-mb`), la commande qui l'a produit et le MTBF **supposé**, avec sa source.
- **Tout ensemble.** `bash verify.sh` se termine par « ok: reference passes, starter fails as intended » sur la référence, et `IMPL=starter pytest tests` passe en entier sur **votre** code.

## Pistes et indices {#pistes}

Ces indices ne donnent pas la solution ; ils indiquent où chercher. Essayez d'abord sans.

**Écriture atomique.** `os.replace` est atomique sur un système de fichiers POSIX local, mais seulement si le fichier temporaire est sur le **même** système de fichiers que la cible. Sans `fsync`, le renommage peut survivre à une coupure de courant alors que les données non : le fichier final existe, vide ou partiel. Pensez aussi à synchroniser le **dossier**. Sur un système de fichiers réseau ou parallèle, lisez la documentation des garanties de renommage avant de supposer quoi que ce soit.

**Somme de contrôle.** Placer un en-tête (marque de format, empreinte SHA-256) devant la charge utile permet de valider le fichier sans le désérialiser ; un format sérialisé par `pickle` ne doit jamais être chargé avant validation. Dans la solution fournie, `torch.load(..., weights_only=True)` limite en plus ce que le fichier peut contenir.

**Rotation.** Supprimez les anciens checkpoints **après** que le nouveau est durable, jamais avant : une panne entre la suppression et l'écriture ne laisserait rien. Ignorez et nettoyez les fichiers `.tmp` orphelins au démarrage.

**Reprise exacte.** Posez-vous la question pour chaque source d'aléa : qui consomme le générateur, et son état est-il dans le checkpoint ? Le curseur de données est ici le numéro de pas. Dans un vrai chargeur de données avec mélange, il faut sauvegarder la position dans la permutation.

**Superviseur.** Lancez l'enfant dans son propre groupe de processus (`start_new_session=True`) pour pouvoir tuer ses descendants. Mesurez le blocage sur la date de modification du fichier de pulsation, avec un délai de grâce plus long avant la première pulsation (l'import de PyTorch prend plusieurs secondes). Ajoutez un délai d'attente croissant entre relances, plafonné, pour ne pas saturer la machine en cas de panne immédiate et répétée.

**Goodput.** Le modèle du premier ordre est une approximation valable quand C est petit devant M. Rappelez-vous ce qu'il néglige : une panne pendant un checkpoint, et la loi de la position de la panne dans la période.

## Extensions {#extensions}

- **Plusieurs processus.** Lancer l'entraîneur avec `torchrun` sur deux ou quatre processus (backend `gloo`) et sauvegarder l'état réparti avec `torch.distributed.checkpoint`. Que doit-il se passer si un seul rang est tué ?
- **Écriture asynchrone.** Copier l'état en mémoire puis l'écrire dans un fil séparé. Mesurez l'effet sur C et prouvez que l'atomicité tient encore.
- **Intégration Slurm.** Reprendre le script `checkpoint_on_signal.sbatch` du lab 5.1 pour que le job soit remis en file avec `--requeue` et reçoive un signal de préavis ; le superviseur disparaît alors, car Slurm assume son rôle.
- **Corruption silencieuse.** Provoquer une altération d'un poids sans panne visible, puis la détecter en comparant les pertes de deux répliques. C'est la catégorie « soupçonnée » du rapport de Llama 3.
- **Variante GPU.** Même code, un GPU, un modèle plus gros. Le coût dépend du fournisseur et de la région : **relevez-le vous-même** le jour de l'essai plutôt que de vous fier à un chiffre d'une page.

## Pour le portfolio {#portfolio}

**Structure du dépôt.** Un `README.md` qui tient sur un écran : le problème en trois phrases, le schéma de la frise ci-dessus, la commande qui lance les 19 tests, le tableau du coût de checkpoint, et un paragraphe « ce que ce prototype ne fait pas ».

**Ce qu'il faut montrer.** Les tests en intégration continue, un exemple de `supervisor.jsonl` après un blocage, l'ADR et le runbook. Le recruteur lira l'ADR avant le code.

**Ce qu'un recruteur d'infrastructure de calcul cherche.** Que vous raisonnez sur les pannes comme sur un cas courant, que vous savez les reproduire pour les tester, que vous distinguez le mesuré du supposé et que vous nommez les limites de votre travail.

::: note
[Mesures de départ, à refaire chez vous]{.tag} Dans le bac à sable de référence (VM à quatre processeurs, disque virtuel), le coût médian d'un checkpoint mesuré par `train.py` a été d'environ 0,014 s pour 1 Mo d'état, 0,2 s pour 16 Mo, 1,0 s pour 64 Mo et 3,9 s pour 256 Mo, avec une forte variabilité d'un checkpoint à l'autre.

Avec le MTBF de 11 100 s calculé plus haut et R = 300 s, la période T\* de Young-Daly est alors d'environ 17, 66, 150 et 293 s. Ce sont des ordres de grandeur d'une machine précise : votre disque donnera d'autres valeurs, et le MTBF d'un cluster de 16 000 GPU n'est pas celui d'un ordinateur portable.
:::

Trois accroches **honnêtes**, à adapter à ce que vous avez réellement fait :

1. « J'ai écrit un entraîneur qui reprend à l'identique après un `kill -9`, une écriture de checkpoint interrompue et un checkpoint corrompu, avec 19 tests automatisés. »
2. « J'ai comparé le modèle de Young-Daly à une simulation de Monte-Carlo et mesuré le coût de checkpoint pour quatre tailles d'état sur ma machine. »
3. « Je sais dire ce que ce prototype ne couvre pas : l'entraînement multi-processus, le stockage partagé et la corruption silencieuse. »

### Formules du jalon 5 {#formules}

Notations (en secondes) : C est le coût d'un checkpoint, M le temps moyen entre pannes, R le coût d'un redémarrage et T la durée de calcul entre deux checkpoints. Le gaspillage au premier ordre est la somme du coût des checkpoints et du travail perdu et redémarré par panne :

$$W(T) \approx \frac{C}{T} + \frac{T/2 + R}{M}$$

Le travail perdu vaut en moyenne T/2 parce que la panne tombe, en moyenne, au milieu d'une période. En annulant la dérivée, on obtient la période optimale de Young :

$$T^{*} = \sqrt{2\,C\,M}$$

Le goodput est alors 1 − W : la part du temps réel passée à calculer ce qui sera effectivement conservé. Ces résultats viennent de Young (1974) et de Daly (2006), qui ajoute des termes d'ordre supérieur. Le test `test_simulation_agrees_with_model_near_optimum` vérifie ici que votre simulation et votre modèle s'accordent à 2 points près.

### Pour aller plus loin {#lectures}

- Llama Team, *The Llama 3 Herd of Models*, 2024 : section sur la fiabilité de l'entraînement, [arxiv.org/abs/2407.21783](https://arxiv.org/abs/2407.21783).
- J. W. Young, « A first order approximation to the optimum checkpoint interval », *Communications of the ACM* 17(9), 1974.
- J. T. Daly, « A higher order estimate of the optimum checkpoint interval for restart dumps », *Future Generation Computer Systems* 22(3), 2006.
