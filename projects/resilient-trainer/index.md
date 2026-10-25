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
numbered: true
---

## Contexte et objectif {#contexte}

Un entraînement qui dure des semaines sur des milliers de GPU sera interrompu, c'est une certitude statistique et non un risque. Le rapport technique de Llama 3 (§ 3.3.4) donne l'ordre de grandeur : « During a 54-day snapshot period of pre-training, we experienced a total of 466 job interruptions », dont 47 prévues et « the remaining 419 were unexpected » ([Llama Team, 2024](https://arxiv.org/abs/2407.21783)).

Environ 78 % des interruptions imprévues sont attribuées à des problèmes matériels confirmés ou soupçonnés, et les GPU en forment la première catégorie : 268 des 419 interruptions imprévues (64 % recalculé à partir des comptes du tableau 5 ; le texte de l'article dit 58,7 %, voir le [module 10, § 1.3](../../courses/fault-tolerance/index.html#ce-que-disent-les-données-publiées)).

Cela fait 419 interruptions imprévues, que nous assimilons ici à des pannes, en 1 296 heures : une toutes les 3,1 heures en moyenne, soit un intervalle moyen entre pannes (MTBF) d'environ 11 100 secondes pour l'ensemble de la machine. Le même rapport annonce pourtant « higher than 90% effective training time », avec une intervention manuelle importante seulement trois fois (« only three times during this period »). L'écart entre ces deux faits, c'est l'ingénierie de la reprise automatique : c'est elle que vous construisez ici, à petite échelle.

::: key
[Objectif du projet]{.tag} Écrire un entraîneur et son superviseur tels que, après une panne quelconque, l'entraînement reprend **à l'identique** (mêmes pertes à chaque pas, au bit près), sans intervention humaine, et être capable de chiffrer ce que la tolérance aux pannes coûte et rapporte.
:::

Le projet se fait sur CPU, avec un petit réseau de neurones et PyTorch. Ce choix est délibéré : les mécanismes (écriture atomique, somme de contrôle, état complet, détection de blocage, intervalle de checkpoint) sont les mêmes qu'à grande échelle, et chaque panne y est **reproductible** par une variable d'environnement. Sur des milliers de GPU, on ne peut pas provoquer une panne à la demande ; ici, on le peut, et c'est ce qui permet d'écrire des tests.

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

Le projet suppose de savoir lire un entraînement PyTorch (modèle, optimiseur, boucle, `state_dict`) et de se servir d'un terminal Linux. `SIGTERM` et `SIGKILL` sont expliqués au [module 1, § 1.1](../../courses/linux-systems/index.html#processus-états-et-signaux) ; `SIGUSR1`, `--signal` et `--requeue` au [module Slurm, § 2.4](../../courses/slurm/index.html#écrire-un-script-qui-survit-à-slurm), dont le lab 5.1 montre un premier checkpoint sur signal. Le superviseur de relance est décrit au [module 10, § 6.3](../../courses/fault-tolerance/index.html#un-superviseur-de-relance) ; les groupes de processus sont expliqués ici, dans les pistes du superviseur.

Les modules [stockage](../../courses/storage/index.html) (chapitre 6, E/S de checkpoint) et [tolérance aux pannes](../../courses/fault-tolerance/index.html) approfondissent ce que ce projet pratique ; le module [entraînement distribué](../../courses/distributed-training/index.html) (chapitre 2, `torchrun`) sert à l'extension « Plusieurs processus ». Vous pouvez faire le projet avant de les lire, quitte à y revenir ensuite.

## Cahier des charges {#cahier}

Le dossier `labs/projects/resilient-trainer/` contient `starter/` (à compléter), `reference/` (solution à consulter **après** votre tentative), `tests/` (19 tests) et `verify.sh`. Ils ont été vérifiés avec Python 3.13, PyTorch 2.14.1 pour CPU et pytest 9.1, la [configuration testée](../../lab-setup/index.html#testee) du site. Les exigences, chacune liée à un test :

| ID | Exigence | Test qui la vérifie |
|---|---|---|
| R1 | Écriture **atomique** : jamais de fichier de checkpoint à moitié écrit sous son nom final ; fichier temporaire puis `os.replace`, avec `fsync` du fichier et du dossier | `test_no_temporary_file_left` (un espion sur `os.fsync` constate les deux appels : la coupure de courant elle-même n'est pas testée), `test_torn_checkpoint_write_is_survived` |
| R2 | **Intégrité** : une somme de contrôle dans le fichier ; un checkpoint corrompu ou tronqué est écarté et le précédent est utilisé | `test_flipped_byte_falls_back_to_previous`, `test_corrupt_latest_checkpoint_falls_back` |
| R3 | **État complet** : poids, état de l'optimiseur, états des générateurs aléatoires (PyTorch et Python), numéro de pas | `test_optimizer_and_rng_state_are_saved`, `test_kill9_resumes_bit_exactly` |
| R4 | **Rotation** : ne garder que les K derniers checkpoints (par numéro de pas, sans les revalider), en supprimant les anciens seulement après que le nouveau est durable | `test_rotation_keeps_newest` |
| R5 | **Superviseur** : relance après un code de sortie non nul, au plus N fois, puis abandon avec le code 1 | `test_gives_up_after_max_restarts` |
| R6 | **Blocage** : un entraîneur dont le fichier de pulsation n'est plus touché depuis le délai fixé est tué (tout son groupe de processus) puis relancé | `test_hung_trainer_is_killed_and_restarted` (le test ne crée pas de petit-enfant : la mort du groupe entier n'est pas vérifiée) |
| R7 | **Arrêt propre** : à la réception de SIGTERM, le superviseur le transmet à l'enfant, ne relance pas et sort avec 143 | `test_sigterm_stops_supervisor_and_child` |
| R8 | **Goodput** (part du temps réel passée à calculer ce qui sera conservé, voir les [formules](#formules)) : la période de Young-Daly, le modèle du premier ordre et une simulation de Monte-Carlo en accord | `tests/test_goodput.py` (5 tests) |

L'entraîneur fourni, `train.py`, est identique dans `starter/` et `reference/`. Il contient trois crochets d'injection de panne, activés par la variable `FAULT` et déclenchés une seule fois par dossier de travail : `kill:N` (SIGKILL juste avant le pas N), `hang:N` (blocage éternel juste avant le pas N) et `torn:N` (arrêt brutal au milieu de l'écriture du checkpoint du pas N).

Il est déterministe : le lot de données (synthétique : une régression linéaire bruitée) dépend uniquement du couple (graine, pas), et le réseau contient un *dropout*, qui consomme le générateur aléatoire global. C'est ce détail qui rend l'état du générateur PyTorch indispensable à la reprise exacte. L'état du générateur Python est sauvegardé par principe, mais rien dans `train.py` ne le consomme : aucun test ne détecte son oubli.

**Hors périmètre** du cœur du projet : l'entraînement multi-processus, les checkpoints répartis par rang, l'écriture asynchrone et le stockage objet. Ce sont des extensions.

## Jalons {#jalons}

| N° | Jalon | Durée | Preuve |
|---|---|---|---|
| 1 | Faire échouer le code de départ et **diagnostiquer chaque échec** | 2 h | sortie de `pytest` sauvegardée et un paragraphe de diagnostic par cause d'échec (les 5 tests de goodput échouent tous pour la même raison) |
| 2 | Checkpoint durable : `pack`, `unpack`, `save`, `load_latest` | 5 h | les 8 tests de `tests/test_ckpt.py` passent |
| 3 | État complet et reprise exacte | 4 h | une reprise à la main (`FAULT=kill:57`, puis relance) redonne les mêmes pertes qu'une exécution sans panne ; `test_kill9_resumes_bit_exactly` et `test_torn_checkpoint_write_is_survived` passent dès que le superviseur du jalon 4 existe |
| 4 | Superviseur : relance, blocage, SIGTERM | 5 h | les trois tests du superviseur passent ; `supervisor.jsonl` d'une exécution avec blocage joint au dépôt |
| 5 | Goodput : modèle, simulation, mesure | 4 h | les 5 tests de `test_goodput.py` passent ; tableau du coût de checkpoint pour quatre tailles d'état |
| 6 | Rapport, ADR et runbook | 4 h | un `README`, un ADR d'une page, un runbook d'une page |

Commencez toujours par le jalon 1. Lancez les tests contre le code de départ et lisez **chaque** message d'échec avant d'écrire une ligne : l'exercice consiste à comprendre pourquoi un script ordinaire échoue, pas à deviner la solution.

Certains échecs en cachent d'autres : les tests de reprise échouent d'abord parce que le superviseur n'existe pas, et `test_corrupt_latest_checkpoint_falls_back` échoue d'abord sur `KeyError: 'opt'` (l'état de l'optimiseur n'est pas sauvegardé) avant de révéler, selon l'octet touché, un chargeur qui accepte sans broncher un fichier altéré. Pour voir ces pannes sans superviseur, lancez `train.py` à la main : `FAULT=kill:57 $PYTHON starter/train.py --workdir /tmp/w1`, puis relancez la même commande sans `FAULT`.

~~~bash
cd labs/projects/resilient-trainer
export PYTHON=/chemin/vers/python-avec-torch     # PyTorch CPU suffit
IMPL=starter $PYTHON -m pytest -q tests/test_ckpt.py   # 6 échecs sur 8 attendus au départ
IMPL=starter $PYTHON -m pytest -q tests                # 17 échecs sur 19 attendus
PYTHON=$PYTHON bash verify.sh                          # prouve référence verte, départ rouge
~~~

Le script `verify.sh` fait deux choses : il vérifie que la solution de référence passe les 19 tests, et que le code de départ en échoue au moins un. Un test qui passe aussi sur le code naïf ne prouve rien, et ce second contrôle le garantit. Il échoue donc dès que `starter/` est complété : travaillez dans une copie (`cp -r starter mon-code`, puis `IMPL=mon-code`).

## Livrables {#livrables}

Votre dépôt public contient :

- le code complété (`ckpt.py`, `supervisor.py`, `goodput.py`) et les tests, avec une commande unique qui les lance ;
- un `README.md` : le problème, le schéma des composants, les commandes pour reproduire, les résultats ;
- un **ADR** (*architecture decision record*) d'une page au format de `adr_template.md` et vérifié par `adr_lint.py` (voir « [Écrire un ADR et un runbook](../../lab-setup/index.html#adr-runbook) »), décrit plus bas ;
- le tableau mesuré du coût de checkpoint et la sortie de `goodput.py` qui l'utilise ;
- un **runbook** d'une page : « l'entraînement ne repart pas après une panne, que vérifier, dans quel ordre », avec la structure (symptôme, vérifications, action, retour arrière) de la même page.

L'ADR doit trancher au moins quatre questions de conception, en nommant l'alternative écartée et pourquoi :

1. Où placer la somme de contrôle (dans le fichier, dans un fichier voisin, dans un manifeste) et ce que chaque choix garantit en cas de panne entre deux écritures ?
2. Combien de checkpoints garder, et que se passe-t-il si les K derniers sont tous corrompus ?
3. Pourquoi le superviseur détecte-t-il le blocage par la pulsation du programme plutôt que par un simple délai maximal d'exécution ?
4. Quelle période de checkpoint retenez-vous, avec quelles valeurs de C et de M, et quelle part de ces valeurs est mesurée plutôt que supposée ?

## Critères de réussite {#criteres}

Chaque critère est mesurable ; la commande qui le montre est indiquée.

- **Reprise exacte.** Après `FAULT=kill:57`, la perte de chaque pas 1 à 120 est identique, au bit près, à celle d'une exécution sans panne ; les pas 51 à 56 apparaissent deux fois dans `loss.jsonl`, avec la même valeur. Commande : `IMPL=mon-code pytest tests/test_resume.py -k kill9`.
- **Aucun checkpoint cassé sous son nom final.** Après `FAULT=torn:60`, aucun fichier `ckpt-00000060.pt` n'existe, le dernier `ckpt-*.pt` valide est celui du pas 50 et la relance reprend de 50. Commande : `pytest -k torn`.
- **Repli sur corruption.** Avec un octet du checkpoint 80 modifié, la relance reprend de 70 et `events.jsonl` nomme le fichier écarté. Commande : `pytest -k corrupt_latest`.
- **Détection de blocage bornée.** Avec `FAULT=hang:45`, `--stall-timeout 3` et `--startup-grace 30` (les valeurs du test ; la solution prend 60 s de grâce par défaut), le superviseur écrit un événement `stall_kill` dont le champ `silent_for` est d'au moins 3 s et de moins de 30 s : le blocage est détecté par le délai de blocage, pas par le délai de grâce. Il relance, et l'entraînement se termine avec la même trajectoire. Commande : `pytest -k hung`.
- **Goodput.** La simulation à la période T\* est à moins de 2 points de pourcentage du modèle du premier ordre, et T\* donne un meilleur goodput que 0,25 T\* et 4 T\*. Commande : `pytest tests/test_goodput.py`.
- **Mesure.** Le rapport donne le coût de checkpoint **mesuré** pour au moins quatre tailles d'état (option `--pad-mb`), la commande qui l'a produit et le MTBF **supposé**, avec sa source.
- **Tout ensemble.** `bash verify.sh`, lancé sur le dépôt tel que fourni, se termine par « ok: reference passes, starter fails as intended », et `IMPL=mon-code pytest tests` passe en entier sur **votre** code.

## Pistes et indices {#pistes}

Ces indices ne donnent pas la solution ; ils indiquent où chercher. Essayez d'abord sans.

**Écriture atomique.** `os.replace` est atomique sur un système de fichiers POSIX local, mais seulement si le fichier temporaire est sur le **même** système de fichiers que la cible. Sans `fsync`, le renommage peut survivre à une coupure de courant alors que les données non : le fichier final existe, vide ou partiel (c'est le problème « zero-length » que la [documentation d'ext4](https://docs.kernel.org/admin-guide/ext4.html) décrit à propos de l'option `auto_da_alloc`). Pensez aussi à synchroniser le **dossier**. Sur un système de fichiers réseau ou parallèle, lisez la documentation des garanties de renommage avant de supposer quoi que ce soit.

**Somme de contrôle.** Placer un en-tête (marque de format, empreinte SHA-256) devant la charge utile permet de valider le fichier sans le désérialiser ; un format sérialisé par `pickle` ne doit jamais être chargé avant validation. Une empreinte SHA-256 stockée dans le fichier détecte la corruption accidentelle, pas un adversaire qui la recalcule : dans la solution fournie, `torch.load(..., weights_only=True)` limite en plus ce que le fichier peut contenir.

**Rotation.** Supprimez les anciens checkpoints **après** que le nouveau est durable, jamais avant : une panne entre la suppression et l'écriture ne laisserait rien. Ignorez les fichiers `.tmp` orphelins et nettoyez-les avant l'écriture suivante (la solution le fait dans `save`). La solution compte les K derniers fichiers par numéro de pas, sans revérifier leur somme de contrôle : si les K derniers sont corrompus, il ne reste rien à quoi se replier, ce que votre ADR doit assumer.

**Reprise exacte.** Posez-vous la question pour chaque source d'aléa : qui consomme le générateur, et son état est-il dans le checkpoint ? Le curseur de données est ici le numéro de pas. Dans un vrai chargeur de données avec mélange, il faut sauvegarder la position dans la permutation.

**Superviseur.** Lancez l'enfant dans son propre groupe de processus (`start_new_session=True`, qui appelle `setsid`) : un signal envoyé au groupe avec `os.killpg` atteint aussi ses descendants, par exemple les processus de chargement de données. Mesurez le blocage sur la date de modification du fichier de pulsation, avec un délai de grâce plus long avant la première pulsation (l'import de PyTorch prend de l'ordre de 2 s sur un système chaud, bien plus à froid). Ajoutez un délai d'attente croissant entre relances, plafonné, pour ne pas saturer la machine en cas de panne immédiate et répétée (aucun test ne le vérifie).

**Pulsation et temps.** Le délai de blocage doit dépasser largement la durée d'un checkpoint, car la pulsation n'est pas émise pendant l'écriture : avec 256 Mo d'état, C vaut environ 3 s et un délai de 3 s tuerait un entraîneur sain.

Les tests de reprise utilisent un délai de 3 s : c'est leur principale dépendance au temps. Ils sont restés verts ici sous une charge d'environ trois processus par processeur avec écritures disque concurrentes, mais une machine plus saturée pourrait provoquer un faux positif. Enfin, la solution attend indéfiniment un enfant qui ignorerait `SIGTERM` ; en production on ajoute un délai puis `SIGKILL`.

**Goodput.** Le modèle du premier ordre est une approximation valable quand C est petit devant M. Rappelez-vous ce qu'il néglige : une panne pendant un checkpoint, et la loi de la position de la panne dans la période. Il suppose aussi C petit devant T : sans panne, le goodput réel vaut T/(T + C) et non 1 − C/T.

## Extensions {#extensions}

- **Plusieurs processus.** Lancer l'entraîneur avec `torchrun` sur deux ou quatre processus (backend `gloo`) et sauvegarder l'état réparti avec `torch.distributed.checkpoint`. Que doit-il se passer si un seul rang est tué ?
- **Écriture asynchrone.** Copier l'état en mémoire puis l'écrire dans un fil séparé. Mesurez l'effet sur C et prouvez que l'atomicité tient encore.
- **Intégration Slurm.** Adapter le script `checkpoint_on_signal.sbatch` du lab 5.1, qui demande déjà `--requeue` et un signal de préavis (`--signal=B:USR1@30`), pour qu'il lance `train.py`, lequel doit alors sauvegarder sur `SIGUSR1`. Slurm remet un job en file après une panne de nœud ou une préemption ([`sbatch --requeue`](https://slurm.schedmd.com/sbatch.html)), mais pas après un code de sortie non nul (sauf `RequeueExit` dans [`slurm.conf`](https://slurm.schedmd.com/slurm.conf.html)) ni après un blocage du programme : la relance et la détection de blocage du superviseur ne disparaissent donc que partiellement.
- **Corruption silencieuse.** Provoquer une altération d'un poids sans panne visible, puis la détecter en comparant les pertes de deux répliques. C'est la catégorie « soupçonnée » du rapport de Llama 3.
- **Variante GPU.** Le même entraîneur sur une machine avec un GPU NVIDIA (un seul suffit) et un modèle plus gros. Placez modèle et lots sur le GPU, et sauvegardez aussi l'état du générateur CUDA : [`torch.get_rng_state`](https://docs.pytorch.org/docs/2.14/generated/torch.get_rng_state.html) ne rend que celui du processeur. Chiffrez la location avec la méthode de la page [Environnement de travail](../../lab-setup/index.html#budget) : durée prévue multipliée par trois, nombre de machines, tarif relevé **le jour même**.

## Pour le portfolio {#portfolio}

**Structure du dépôt.** Un `README.md` qui tient sur un écran : le problème en trois phrases, le schéma de la frise ci-dessus, la commande qui lance les 19 tests, le tableau du coût de checkpoint, et un paragraphe « ce que ce prototype ne fait pas ».

**Ce qu'il faut montrer.** Les tests en intégration continue, un exemple de `supervisor.jsonl` après un blocage, l'ADR et le runbook. Le recruteur lira l'ADR avant le code.

**Ce qu'un recruteur d'infrastructure de calcul cherche.** Que vous raisonnez sur les pannes comme sur un cas courant, que vous savez les reproduire pour les tester, que vous distinguez le mesuré du supposé et que vous nommez les limites de votre travail.

::: note
[Mesures de départ, à refaire chez vous]{.tag} Dans le bac à sable de référence (VM à quatre processeurs, système de fichiers ext4 sur disque virtuel), le coût médian d'un checkpoint de la solution de référence, mesuré par `train.py --pad-mb`, a été lors de deux exécutions d'environ 0,009 s pour 1 Mo d'état, 0,12 à 0,17 s pour 16 Mo, 0,5 à 0,7 s pour 64 Mo et 2,8 à 3,1 s pour 256 Mo. D'un checkpoint à l'autre, le plus lent peut valoir deux fois le plus rapide.

Avec le MTBF de 11 100 s calculé plus haut, la période T\* de Young-Daly est alors d'environ 14, 52, 105 et 250 s (en prenant le bas de chaque fourchette : C = 0,009 ; 0,12 ; 0,5 et 2,8 s). Ce sont des ordres de grandeur d'une machine précise : votre disque donnera d'autres valeurs, et le MTBF d'un cluster de 16 000 GPU n'est pas celui d'un ordinateur portable.

Le coût de redémarrage R n'entre pas dans T\* mais dans le gaspillage W : `goodput.py` le prend par défaut à 300 s, une valeur **supposée** (sans source : c'est un ordre de grandeur de reprise, à remplacer par votre mesure).
:::

Trois accroches **honnêtes**, à adapter à ce que vous avez réellement fait :

1. « J'ai écrit un entraîneur qui reprend à l'identique après un `kill -9`, une écriture de checkpoint interrompue et un checkpoint corrompu, avec 19 tests automatisés. »
2. « J'ai comparé le modèle de Young-Daly à une simulation de Monte-Carlo et mesuré le coût de checkpoint pour quatre tailles d'état sur ma machine. »
3. « Je sais dire ce que ce prototype ne couvre pas : l'entraînement multi-processus, le stockage partagé et la corruption silencieuse. »

### Formules du jalon 5 {#formules}

Notations (en secondes) : C est le coût d'un checkpoint, M le temps moyen entre pannes, R le coût d'un redémarrage et T la durée de calcul entre deux checkpoints. Le [module 10, § 2.1](../../courses/fault-tolerance/index.html#les-quatre-durées) note $\delta$ ce que nous notons C, et $\tau$ ce que nous notons T. Le gaspillage au premier ordre est la somme du coût des checkpoints et du travail perdu et redémarré par panne :

$$W(T) \approx \frac{C}{T} + \frac{T/2 + R}{M}$$

Le travail perdu vaut en moyenne T/2 parce que la panne tombe, en moyenne, au milieu d'une période. En annulant la dérivée, on obtient la période optimale de Young :

$$T^{*} = \sqrt{2\,C\,M}$$

Le goodput est alors 1 − W : la part du temps réel passée à calculer ce qui sera effectivement conservé. Ces résultats viennent de Young (1974) et de Daly (2006), qui ajoute des termes d'ordre supérieur.

Le test `test_simulation_agrees_with_model_near_optimum` vérifie ici que votre simulation et votre modèle s'accordent à 2 points près, puis compare la simulation à une référence exacte là où les pannes sont fréquentes : avec des pannes exponentielles, une panne pendant un checkpoint qui le perd et aucune panne pendant un redémarrage, sécuriser un segment de T + C secondes prend en moyenne $(M + R)\,(e^{(T+C)/M} - 1)$ secondes.

Le modèle exact du [module 10, § 2.3](../../courses/fault-tolerance/index.html#le-modèle-exact-et-la-correction-de-daly) admet en plus des pannes pendant le redémarrage. Il donne $M\,e^{R/M}\,(e^{(T+C)/M} - 1)$, plus grand d'un facteur $e^{R/M}/(1 + R/M)$, proche de 1 quand R est petit devant M. Avec les valeurs du test (T = 100, C = 50, M = 300 et R = 10 s), les deux goodputs diffèrent de 0,05 % en valeur relative : l'écart reste sous la tolérance relative de 2 % du test, mais ce n'est pas la même formule.

### Pour aller plus loin {#lectures}

- Llama Team, *The Llama 3 Herd of Models*, 2024 : § 3.3.4 « Reliability and Operational Challenges », [arxiv.org/abs/2407.21783](https://arxiv.org/abs/2407.21783).
- J. W. Young, « A first order approximation to the optimum checkpoint interval », *Communications of the ACM* 17(9), 1974.
- J. T. Daly, « A higher order estimate of the optimum checkpoint interval for restart dumps », *Future Generation Computer Systems* 22(3), 2006.
