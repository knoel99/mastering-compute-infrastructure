---
title: "Projet 2 — Étude de passage à l'échelle d'un entraînement"
subtitle: "Projet 2 · 20 h · modules : perf-models, parallel-programming, distributed-training"
description: "Mesurer, modéliser et expliquer comment un entraînement en parallélisme de données passe (ou ne passe pas) à l'échelle, avec un rapport reproductible, des intervalles de confiance et une liste honnête des limites."
project:
  id: scaling-study
  number: 2
  hours: 20
  modules: [perf-models, parallel-programming, distributed-training]
badges:
  - {label: "Portfolio", class: core}
  - {label: "Code de départ et solution vérifiés (CPU)", class: verified}
numbered: true
---

## Contexte et objectif {#contexte}

Quand on double le nombre de processus d'un entraînement, va-t-il deux fois plus vite ? Presque jamais, et la bonne réponse d'un ingénieur d'infrastructure n'est pas « oui » ou « non » mais un **chiffre accompagné de sa cause** : de combien, pourquoi, et jusqu'où l'on peut extrapoler. Ce projet vous fait produire une telle réponse, avec des mesures que vous pouvez défendre en entretien.

Vous allez concevoir un plan d'expériences, mesurer un entraînement en parallélisme de données sur 1, 2 et 4 processus, ajuster le modèle α-β de l'all-reduce avec un intervalle de confiance, calculer gain, efficacité et fraction séquentielle de Karp-Flatt (formules en fin de page), **prédire** le temps d'un pas à partir d'une seule mesure, puis expliquer l'écart entre prédiction et mesure. Le tout tient dans un rapport qu'une seule commande régénère.

::: key
[Objectif du projet]{.tag} Un rapport honnête vaut mieux qu'un beau graphe. Un résultat négatif (« ça ne passe pas à l'échelle ») correctement mesuré, modélisé et expliqué est un excellent livrable ; un gain flatteur sans barre d'erreur, sans modèle et sans limites n'en est pas un.
:::

Le projet se fait **sans GPU** : les « rangs » sont des processus PyTorch qui communiquent avec le backend `gloo` sur l'interface locale. Le matériel est donc très différent d'un cluster de GPU (le débit est de l'ordre du Go/s et non de centaines de Go/s), mais la **méthode** est la même : plan, mesure, modèle, décomposition, limites. La variante GPU est une extension.

Le code de départ fournit la mesure d'un point (`bench.py`) : à vous de bâtir autour l'expérience complète. Un point de vigilance de méthode traverse tout le projet : on ne tire de conclusion que des écarts plus grands que la dispersion des mesures.

### Prérequis de connaissances {#pre}

Le [module 2 « Architecture matérielle et modèles de performance »](../../courses/perf-models/index.html) donne ce qu'il faut : loi d'Amdahl, modèle α-β, all-reduce en anneau, MFU. Son lab 2.2 mesure déjà un all-reduce et ajuste α et B ; ce projet reprend et complète ce travail, avec des intervalles de confiance et un entraînement réel.

Deux modules approfondissent le cœur du projet : le [module 3, chapitre 8](../../courses/parallel-programming/index.html#ch8), pour le plan d'expérience et le rapport, et le [module 9, chapitre 2](../../courses/distributed-training/index.html#ch2), pour ce que `DistributedDataParallel` ajoute à l'entraîneur élémentaire (seaux, recouvrement). Les extensions GPU et à deux machines relèvent du [module 4](../../courses/gpu-programming/index.html) et du [module 7](../../courses/networking/index.html) ; le cœur du projet ne les exerce pas.

## Cahier des charges {#cahier}

Le dossier `labs/projects/scaling-study/` contient `starter/` (à compléter), `reference/` (à consulter **après** votre tentative), `tests/` (23 tests) et `verify.sh`.

| ID | Exigence | Test qui la vérifie |
|---|---|---|
| R1 | **Plan d'expériences** : régimes fort et faible, p dans {1, 2, 4}, au moins 3 exécutions indépendantes par point, chacune de plusieurs pas mesurés après chauffe (le protocole du [module 2, § 8.1](../../courses/perf-models/index.html#ch8) demande dix répétitions : signalez ce nombre réduit parmi les menaces à la validité, comme le rapport de référence), ordre des exécutions mélangé de façon reproductible (graine) | `test_plan_*`, `test_dry_run_prints_the_plan` |
| R2 | **Exécuteur** : lance `bench.py` pour chaque exécution et écrit un `results.json` brut | `test_end_to_end_small_study` |
| R3 | **Ajustement α-β** par moindres carrés sur l'erreur relative, avec exclusion des petits messages et **intervalle de confiance bootstrap** reproductible | `tests/test_fit.py` (7 tests) |
| R4 | **Métriques** : gain, efficacité, fraction séquentielle de Karp-Flatt, médiane et interquartile | `test_speedup_efficiency_karp_flatt`, `test_summarize` |
| R5 | **Prédiction** du temps d'un pas à partir d'**une seule** mesure à p = 1 et du modèle | `test_predict_step_strong_and_weak` |
| R6 | **Utilisation du pic mesuré** ($U_c$, phase de calcul seule : ce n'est pas le MFU du module 2) : formule implémentée, colonne remplie quand vous fournissez un pic mesuré (extension « Un pic mesuré »), jamais un pic de fiche technique | `test_utilization`, `test_analyze_*` (ils vérifient la formule ; l'origine du pic est à votre charge) |
| R7 | **Décomposition** de la communication (empaquetage, attente, all-reduce) et explication de l'écart modèle-mesure | `test_decompose_*`, `test_report_adds_breakdown_*` |
| R8 | **Rapport** régénérable en une commande, avec définitions et menaces à la validité | `test_report_has_required_sections_and_numbers` |

L'entraîneur mesuré est volontairement **élémentaire** : chaque processus calcule la passe avant et arrière sur son lot, puis **tous** les gradients sont aplatis dans un seul tenseur et sommés par un unique `all_reduce`, sans découpage en seaux ni recouvrement avec la passe arrière. C'est le parallélisme de données du manuel, celle que décrit le modèle α-β ; ce n'est pas `DistributedDataParallel`, que vous comparerez en extension.

Deux régimes sont étudiés. En **passage à l'échelle fort**, le lot global est fixé (256 exemples) et chaque processus en traite une part de plus en plus petite. En **passage à l'échelle faible**, chaque processus garde son lot (64 exemples) et le travail total grandit avec p. Le second régime teste surtout la communication, le premier teste aussi la loi d'Amdahl.

## Jalons {#jalons}

| N° | Jalon | Durée | Preuve |
|---|---|---|---|
| 1 | Plan d'expériences et exécuteur (`run_study.py`) | 4 h | les tests du plan et `--dry-run` passent ; un `results.json` brut est joint |
| 2 | Ajustement α-β avec intervalle de confiance (`fit_model.py`) | 4 h | les 7 tests de `test_fit.py` passent ; α et B pour p = 2 et p = 4 avec leurs intervalles |
| 3 | Métriques et prédiction (`analysis.py`) | 4 h | les 6 tests de `test_analysis.py` passent |
| 4 | Étude complète puis exécution décomposée | 3 h | `results.json` avec les deux régimes ; une seconde exécution avec `--decompose` |
| 5 | Rapport, ADR et lecture critique (`report.py`) | 5 h | `report.md` généré par une commande ; ADR d'une page ; section « menaces » écrite pour **votre** machine |

Commencez par lancer `bench.py` à la main pour p = 1, 2 et 4, et **regardez** les nombres avant d'écrire le moindre code d'analyse : vous saurez ce que vous cherchez à expliquer.

~~~bash
cd labs/projects/scaling-study
export PYTHON=/chemin/vers/python-avec-torch      # PyTorch CPU, numpy, pytest
OMP_NUM_THREADS=1 $PYTHON starter/bench.py --world-size 2 --batch-per-rank 64 --out /tmp/b2.json
IMPL=starter $PYTHON -m pytest -q tests           # 20 échecs sur 23 au départ
PYTHON=$PYTHON bash verify.sh                      # référence verte, départ rouge
~~~

Pour le balayage des tailles de message qui alimente l'ajustement, réutilisez `labs/perf-models/allreduce-model/bench_allreduce.py` du lab 2.2, lancé avec `torchrun --nproc_per_node=2` puis `=4` (une sortie JSON par valeur de p ; `fit_model.load_rows` la relit).

Les jalons 4 et 5 s'enchaînent ainsi. Les options de `report.py` ne sont pas imposées par les tests : ce sont celles de la référence. `fit.json` contient les deux clés `alpha_s` et `B_bytes_per_s` : les deux premières commandes l'écrivent avec `fit_model.fit`, à partir du balayage à p = 4 et des messages d'au moins 64 Kio, comme le rapport de référence.

~~~bash
OMP_NUM_THREADS=1 $PYTHON -m torch.distributed.run --nproc_per_node=4 ../../perf-models/allreduce-model/bench_allreduce.py --out sweep_p4.json   # torchrun
$PYTHON -c "import json,sys; sys.path.insert(0,'starter'); import fit_model as f; rows,p=f.load_rows(sys.argv[1]); json.dump(f.fit(rows,p,min_bytes=65536),open('fit.json','w'))" sweep_p4.json
$PYTHON starter/run_study.py --out results.json                   # 18 exécutions, quelques minutes
$PYTHON starter/run_study.py --decompose --out results_dec.json   # même plan, avec décomposition
$PYTHON -c "import json,sys; a,b=(json.load(open(f)) for f in sys.argv[1:3]); a['points']+=b['points']; json.dump(a,open('all.json','w'))" results.json results_dec.json
$PYTHON starter/report.py --results all.json --fit fit.json --out report.md
~~~

## Livrables {#livrables}

Votre dépôt public contient :

- le code complété et les tests, avec une commande unique qui les lance ;
- les résultats **bruts** (`results.json`, le balayage de l'all-reduce) : un rapport sans données brutes n'est pas vérifiable ;
- `report.md`, généré, et la commande qui le régénère ;
- un **ADR** d'une page au format de `adr_template.md`, vérifié par `adr_lint.py` (voir « [Écrire un ADR et un runbook](../../lab-setup/index.html#adr-runbook) ») ;
- une page « lecture critique » : trois choses que votre étude **ne permet pas** de conclure.

L'ADR tranche au moins quatre questions, en nommant l'alternative écartée :

1. Pourquoi mélanger l'ordre des exécutions plutôt que de les enchaîner par configuration, et qu'est-ce que cela protège ?
2. Pourquoi la médiane et l'écart interquartile plutôt que la moyenne et l'écart-type pour des temps de pas ?
3. Pourquoi ajuster sur l'erreur relative, et pourquoi exclure les petits messages de l'ajustement ?
4. Que concluez-vous si votre modèle se trompe de 30 % ? Que modifieriez-vous : le modèle, la mesure, ou la question ?

## Critères de réussite {#criteres}

Chaque critère est mesurable ; la commande qui le montre est indiquée.

- **Tests.** `IMPL=starter pytest tests` passe en entier sur **votre** code (23 tests), et `bash verify.sh` affiche « ok: reference passes, starter fails as intended » sur la référence.
- **Plan.** `run_study.py --dry-run` liste 18 exécutions pour 3 tailles, 2 régimes et 3 répétitions, et deux appels avec la même graine produisent des listes identiques (`diff` vide).
- **Ajustement.** Sur des données synthétiques avec 3 % de bruit, B est retrouvé à 10 % près et l'intervalle bootstrap contient l'estimation. Commande : `pytest tests/test_fit.py`.
- **Couverture.** Vous savez dire quelle part des intervalles de confiance contient la vraie valeur : le test de couverture le mesure (environ 85 % pour un niveau annoncé de 95 %, voir plus bas).
- **Rapport.** Le tableau donne, pour chaque (régime, p), le pas médian, l'écart interquartile, le gain ou l'efficacité, la part de communication, la prédiction et son erreur ; vos conclusions ne portent que sur des écarts supérieurs à l'écart interquartile.
- **Explication.** Pour au moins un point, le tableau de décomposition donne le rapport « all-reduce mesuré sur modèle » et une phrase attribue l'écart restant à une cause nommée et vérifiable.
- **Honnêteté.** Les « menaces à la validité » décrivent **votre** matériel : nombre de processeurs, backend, charge de la machine, nombre de répétitions.

## Pistes et indices {#pistes}

Ces indices ne donnent pas la solution ; essayez d'abord sans.

**Mesurer.** Écartez les premiers pas (caches, allocations, initialisation de `gloo`) : `bench.py` le fait déjà et le test vérifie que la série n'en contient pas. Fixez `OMP_NUM_THREADS=1` et `torch.set_num_threads(1)` : sans cela, chaque processus lance plusieurs fils et vous mesurez la contention entre processus, pas le passage à l'échelle. Sur une machine à quatre processeurs, quatre processus occupent tout : le système et tout autre processus actif se disputent les mêmes cœurs.

**Plan.** Un enchaînement « toutes les mesures à p = 1, puis toutes à p = 2 » confond le facteur étudié avec la dérive de la machine (fréquence, voisins bruyants). Mélangez, avec une graine pour pouvoir rejouer. Trois répétitions sont un minimum : l'intervalle interquartile de trois valeurs est grossier, signalez-le.

**Ajuster.** Le modèle est linéaire en taille de message, mais ne l'est qu'au-delà d'une taille : les petits messages dépendent du pilote et de l'ordonnanceur. Ajustez sur l'erreur relative (divisez chaque équation par le temps mesuré) pour ne pas laisser les plus gros messages écraser les autres. Le bootstrap rééchantillonne les couples (taille, temps) ; avec une dizaine de points il est optimiste, comme le montre le test de couverture.

**Prédire.** Un modèle qui explique la **collective** n'explique pas pour autant le **pas** : relisez ce que `comm_s` contient. La communication mesurée inclut l'aplatissement des gradients, leur recopie, et l'attente du rang le plus lent. Séparez-les avec `--decompose` avant de blâmer le modèle.

**Lire un maximum.** Chaque phase est le maximum sur les rangs, car une étape synchrone dure autant que son rang le plus lent. Conséquence : la somme des maxima par phase peut dépasser le maximum de la somme, et vous ne devez pas attendre que « empaquetage + attente + all-reduce » égale exactement la communication totale.

**Karp-Flatt.** Si la fraction séquentielle calculée croît avec p, la perte n'est pas une part séquentielle fixe au sens d'Amdahl : c'est un coût qui grandit avec le nombre de processus. Si elle dépasse 1, vous êtes plus lent qu'en séquentiel et la formule ne représente plus une fraction : dites-le, ne la recopiez pas.

### Résultats de la solution de référence {#reference-results}

À lire **après** votre propre étude. Les valeurs dépendent de la machine : celles-ci viennent d'une VM à quatre processeurs virtuels avec PyTorch 2.14 CPU, un réseau de 1,05 million de paramètres (4,2 Mo de gradients), 3 répétitions de 30 pas par point.

::: sol
**Balayage de l'all-reduce (jalon 2).** Ajustement sur les messages d'au moins 64 Kio, avec intervalle bootstrap à 95 % :

| p | α | B |
|---|---|---|
| 2 | 164 µs (91 à 189) | 1,08 Go/s (0,93 à 1,31) |
| 4 | 300 µs (260 à 429) | 1,05 Go/s (0,98 à 1,26) |

Les intervalles de B se recouvrent : rien ne dit que la bande passante change. En revanche les intervalles de α ne se recouvrent pas : α **n'est pas** une constante de la machine, il est nettement plus grand à p = 4 (×1,8 ici). Le modèle suppose un α fixe par saut. Une cause plausible, non testée ici, est que les quatre processus occupent les quatre processeurs et que l'ordonnanceur ajoute de la latence.

Ces nombres ne se reproduisent pas à l'identique : un second balayage dans le même bac à sable a donné α = 250 puis 332 µs et B = 1,43 puis 1,21 Go/s (p = 2 puis 4). Seuls l'ordre de grandeur et le sens de l'écart de α sont stables ; c'est une raison de plus de publier les barres d'erreur.

Le rapport de référence utilise un **seul** couple (α, B), celui de p = 4 (300 µs ; 1,05 Go/s), pour toutes les prédictions, y compris à p = 2. C'est une simplification, et donc une limite à nommer dans vos menaces à la validité.

**Étude complète (jalon 4).** Pas médian en millisecondes, gain S du régime fort, efficacité E, part de communication :

| régime | p | pas (ms) | S | E | communication | erreur du modèle |
|---|---|---|---|---|---|---|
| fort | 1 | 17,7 | 1,00 | 1,00 | 0 % | 0 % |
| fort | 2 | 19,8 | 0,90 | 0,45 | 48 % | 29 % |
| fort | 4 | 26,3 | 0,67 | 0,17 | 69 % | 50 % |
| faible | 1 | 7,5 | | 1,00 | 0 % | 0 % |
| faible | 2 | 17,2 | | 0,43 | 55 % | 30 % |
| faible | 4 | 28,9 | | 0,26 | 71 % | 47 % |

**Lecture.** Dans cette configuration, le parallélisme de données **ne passe pas à l'échelle** : à quatre processus, le pas du régime fort est plus lent qu'à un seul (gain de 0,67).

Rejouée une seconde fois, l'étude donne la même conclusion (gain de 0,72 à p = 4) avec des nombres différents de quelques pour cent à plusieurs dizaines de pour cent : retenez les ordres de grandeur. La cause est un rapport calcul sur communication défavorable : un pas de calcul de 64 exemples dure quelques millisecondes, alors que l'échange de 4,2 Mo de gradients à environ 1 Go/s en demande déjà quatre (p = 2) à six (p = 4), sans compter la latence.

**Décomposition (exécution avec `--decompose`).** En régime fort à p = 2, l'all-reduce mesuré dure 4,4 ms contre 4,6 ms prédites : le modèle est bon, à 4 % près. L'écart de 29 % sur le pas (5,8 ms) vient pour l'essentiel d'**ailleurs** : 2,8 ms d'aplatissement et de recopie des gradients, et 2,1 ms d'attente du rang le plus lent, soit 4,9 ms.

Le reste tient notamment au calcul, qui ne diminue pas comme 1/p quand le lot par processus baisse : le pas à p = 1 dure 7,5 ms pour 64 exemples et 17,7 ms pour 256, un rapport de 2,4 et non de 4. À p = 4, l'all-reduce dure 11,4 ms pour 7,8 ms prédites (rapport de 1,46) : l'hypothèse la plus probable est que les quatre processus se disputent les quatre processeurs (non isolée ici : comparez avec trois processus).
:::

## Extensions {#extensions}

- **Seuil de rentabilité.** Avec le modèle, prédisez le lot par processus à partir duquel le régime faible atteint une efficacité de 0,8, puis vérifiez par une mesure. L'écart entre prédiction et mesure vous dit ce que le modèle ignore.
- **`DistributedDataParallel`.** Remplacez l'entraîneur élémentaire par `torch.nn.parallel.DistributedDataParallel` et mesurez la part de communication cachée derrière la passe arrière. Prédisez-la avant de la mesurer.
- **Un pic mesuré.** Utilisez le lab 2.1 (STREAM et GEMM), lancé avec `OMP_NUM_THREADS=1` pour que le pic soit celui d'un seul cœur, et passez-le à `report.py --peak-gflops` pour obtenir $U_c$ à chaque point. Calculez aussi le même rapport sur le pas complet $t_p$ : l'écart entre les deux mesure le poids de ce qui n'est pas du calcul, communication en tête.
- **Deux machines.** Placez deux VM sur le même réseau et refaites le balayage avec `gloo` entre elles ; comparez α et B à ceux de la boucle locale.
- **Variante GPU.** Même étude avec `nccl` sur deux GPU NVIDIA d'un même nœud (un rang par GPU, p = 1 puis 2), un modèle plus gros et un pic pris sur votre propre micro-benchmark GEMM ; le pic dense de la fiche technique donne en plus le MFU du module 2. Chiffrez-la avec la méthode de la page [Environnement de travail](../../lab-setup/index.html#budget) : durée prévue multipliée par trois, nombre de GPU, tarif du jour.

## Pour le portfolio {#portfolio}

**Structure du dépôt.** Un `README.md` d'un écran : la question posée, la commande qui régénère le rapport, le tableau des résultats avec leurs écarts interquartiles, et un paragraphe « ce que cette étude ne montre pas ».

**Ce qu'il faut montrer.** Les données brutes, le rapport généré, l'ADR et les tests. Un recruteur regarde d'abord si vous donnez des barres d'erreur, si votre modèle est confronté à une mesure, et si vous reconnaissez ses limites.

**Ce qu'un recruteur d'infrastructure de calcul cherche.** Quelqu'un qui ne confond pas la collective et le pas, qui sait qu'un modèle de performance se valide contre des mesures, et qui ose écrire « ça ne passe pas à l'échelle, voici pourquoi ».

::: note
[Mesurer la couverture d'un intervalle de confiance]{.tag} Un intervalle à 95 % devrait contenir la vraie valeur dans 95 % des cas. Sur 40 jeux synthétiques de 9 points (les tailles d'au moins 64 Kio parmi 15) avec 3 % de bruit multiplicatif, l'intervalle bootstrap par percentiles de B contient la vraie valeur 34 fois sur 40 (85 %), et celui de α 36 fois sur 40 (90 %) : avec si peu de points, il est trop optimiste. Le test `test_bootstrap_coverage_is_close_to_but_below_nominal` l'inscrit ; retenez que « intervalle à 95 % » ne veut pas dire « 95 % de chances » sans vérification.
:::

Trois accroches **honnêtes**, à adapter à ce que vous avez réellement mesuré (ne reprenez pas ces chiffres s'ils ne sont pas les vôtres) :

1. « J'ai mesuré qu'un entraînement en parallélisme de données d'un petit réseau ne passait pas à l'échelle sur quatre processeurs virtuels, et j'ai expliqué pourquoi avec un modèle α-β et une décomposition du temps de communication. »
2. « J'ai validé un modèle d'all-reduce contre des mesures avec un intervalle de confiance, et montré qu'il prédit la collective à 4 % près à deux processus, observe un all-reduce 46 % plus lent que prévu à quatre, et ne prédit pas le pas complet. »
3. « Je sais dire ce que cette étude ne permet pas de conclure : le comportement sur GPU, sur un vrai réseau, et à grande échelle. »

### Formules du projet {#formules}

Notations : $t_1$ est le temps d'un pas à un processus, $t_p$ le temps à $p$ processus, $n$ la taille du message en octets, $\alpha$ la latence par saut et $B$ la bande passante. Gain et efficacité du régime fort :

$$S = \frac{t_1}{t_p}, \qquad E = \frac{S}{p}$$

En régime faible, chaque processus garde son lot : le pas idéal ne change pas avec $p$, et l'efficacité vaut $E = t_1/t_p$.

La fraction séquentielle de Karp-Flatt déduite du gain mesuré :

$$e = \frac{1/S - 1/p}{1 - 1/p}$$

Le temps d'un all-reduce en anneau, modèle du lab 2.2 :

$$T(n) = 2(p-1)\,\alpha + \frac{2(p-1)}{p}\,\frac{n}{B}$$

Et l'utilisation du pic mesuré, avec $N$ paramètres, un lot $b$ par processus, un temps de calcul $t_c$ (passes avant et arrière) et un pic mesuré $F_{\text{mesuré}}$ :

$$U_c = \frac{6\,N\,b}{t_c\,F_{\text{mesuré}}}$$

Ce n'est pas le MFU du [module 2, § 7.2](../../courses/perf-models/index.html#ch7). Celui-ci se calcule sur le pas complet, communication comprise, et sur le pic dense de la fiche technique : avec $p\,b/t_p$ exemples par seconde et $6N$ FLOP par exemple sur $p$ processus, il vaut $\mathrm{MFU} = 6\,N\,b/(t_p\,P_{\text{pic}})$. $U_c$ isole la phase de calcul et utilise un pic mesuré, en général plus bas que celui de la fiche : il est plus élevé que le MFU et ne se compare pas aux 38 à 46 % publiés.

### Pour aller plus loin {#lectures}

- A. H. Karp et H. P. Flatt, « Measuring parallel processor performance », *Communications of the ACM* 33(5), 1990.
- P. Patarasuk et X. Yuan, « Bandwidth optimal all-reduce algorithms for clusters of workstations », *Journal of Parallel and Distributed Computing* 69(2), 2009.
- Le [module 2](../../courses/perf-models/index.html), chapitres sur le modèle α-β et l'all-reduce.
