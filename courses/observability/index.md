---
title: "Observabilité et fiabilité d'une flotte GPU"
subtitle: "Module 14 · Phase 4 · 24 h"
description: "Diagnostiquer en minutes un job bloqué, un GPU silencieux ou une courbe cassée : métriques DCGM, Prometheus, journaux, files d'attente Slurm, SLO de plateforme, goodput et détection de pannes silencieuses."
module:
  id: observability
  number: 14
  phase: 4
  hours: 24
  level: 2
prerequisites: [linux-systems, slurm]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs vérifiés dans un bac à sable (sans GPU)", class: verified}
labs:
  - {id: gpu-metrics-exporter, kind: sandbox}
  - {id: alert-rules, kind: sandbox}
  - {id: hang-detector, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** votre job de 512 GPU n'avance plus depuis vingt minutes, et personne ne le sait. Combien de temps faudra-t-il pour s'en apercevoir, pour trouver le rang fautif et pour relancer l'entraînement ? Sans observabilité, la réponse honnête est « jusqu'à ce qu'un chercheur se plaigne ». Avec elle, elle se compte en minutes.

Ce module apprend à instrumenter une flotte GPU, à définir ce qu'on promet à ses utilisateurs (des objectifs de niveau de service, ou *SLO*), à détecter les pannes **silencieuses** et à relier une régression de courbe à sa cause, qu'elle vienne du matériel ou du modèle. Vous connaissez déjà Prometheus, Grafana et Terraform : ce module ne les réexplique pas. Il traite ce qui change quand la charge est un entraînement distribué synchrone sur du matériel qui tombe en panne sans bruit.

Tout ce qui est exécutable l'a été dans un bac à sable sans GPU. Les métriques GPU y sont **simulées** et étiquetées comme telles ; les captures de Slurm, de `promtool`, de `faulthandler` et de MLflow sont réelles et datées.

::: key
[Règle de ce module]{.tag} Une alerte est une promesse faite à une personne endormie : elle doit signaler un problème réel, que cette personne peut traiter, au bon moment. Chaque alerte de ce module est donc écrite avec trois choses : la durée avant laquelle elle se déclenche, le cas qui la fait taire, et le test qui prouve les deux.
:::

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 24 h, dont environ 9 h de lecture, 10 h de labs et 5 h d'exercices |
| Niveau d'entrée | 2 : Linux et Slurm (modules 1 et 5) ; pour Prometheus, les bases de PromQL suffisent, par exemple le guide officiel [*Getting started*](https://prometheus.io/docs/prometheus/latest/getting_started/) de Prometheus |
| Prérequis | [Module 1 — Linux, systèmes et diagnostic de performance](../linux-systems/index.html), [Module 5 — Slurm et exploitation d'un cluster HPC](../slurm/index.html) |
| Pour qui | Cœur : sémantique des métriques GPU, détection des blocages et objectifs de service (SLO) du calcul ; si vous maîtrisez déjà Prometheus, concentrez-vous sur ces trois points. |
| Livrable | un exportateur testé, des règles d'alerte testées par promtool et par mutation, un détecteur de blocage dont vous connaissez les fausses alarmes |
| Environnement | un portable ou une VM Linux, **sans GPU** ; `promtool` (paquet apt `prometheus`), Python avec `prometheus_client`, `torch` CPU, `pytest`, `pyyaml` (et `mlflow-skinny`, `sqlalchemy`, `alembic` pour la partie C du lab 14.3, `opentelemetry-sdk` pour sa partie D) ; Slurm du module 5 pour la branche en direct |
| Projets liés | [Projet 1 — Mini-cluster Slurm instrumenté](../../projects/homelab-slurm/index.html), [Projet 5 — Observabilité GPU et détection de pannes silencieuses](../../projects/gpu-observability/index.html), [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Dire ce qu'une métrique GPU mesure vraiment, en particulier pourquoi `DCGM_FI_DEV_GPU_UTIL` ne dit pas si le GPU travaille (chapitres 1 et 2).
-   Dimensionner un Prometheus pour une flotte (séries, échantillons, disque) et empêcher l'explosion de cardinalité (chapitre 3).
-   Retrouver le rang fautif d'un job bloqué à partir des journaux et d'une trace de piles (chapitre 4).
-   Exporter l'état d'une file Slurm avec des étiquettes bornées et en tirer un délai d'attente honnête (chapitre 5).
-   Calculer un budget d'erreur, écrire une alerte à fenêtres multiples et la tester (chapitre 6).
-   Mesurer le compromis entre fausses alarmes et délai de détection d'un blocage (chapitre 7).
-   Distinguer, avec des métriques jointes dans MLflow, une régression du système d'une régression du modèle (chapitre 8).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 4 — Plateforme cloud-native et multi-fournisseurs** (semaines 33-44) : placer, observer et facturer des charges sur plusieurs fournisseurs.
-   **S'appuie sur** : [module 1 — Linux, systèmes et diagnostic de performance](../linux-systems/index.html), [module 5 — Slurm et exploitation d'un cluster HPC](../slurm/index.html).
-   **Prépare** : [module 16 — Plateforme interne, sécurité, production et leadership](../platform-leadership/index.html).
-   **Projets qui s'en servent** : [Projet 1 — Mini-cluster Slurm instrumenté](../../projects/homelab-slurm/index.html), [Projet 5 — Observabilité GPU et détection de pannes silencieuses](../../projects/gpu-observability/index.html), [Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU](../../projects/capstone-rfc/index.html).
-   **Compétences demandées dans les offres d'emploi et travaillées ici** : Python, Slurm, Prometheus, Grafana, Supervision GPU (DCGM), Suivi d'expériences, Astreinte, fiabilité (SRE), Santé matérielle (burn-in, diagnostics, RMA), Entraînement distribué (PyTorch, Megatron, DeepSpeed…), Collectives (NCCL, RCCL, HCCL), Journaux, traces, Checkpoint, tolérance aux pannes, Expérience d'entraînement ML, Systèmes distribués (voir [l'analyse du marché](../../market/index.html#couverture)).
<!-- /gen:place -->

### Plan de séances {#seances}

Dix séances, soit 24 h. Le niveau ne diminue jamais d'une séance à la suivante.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 2.5 h | 1 | ch. 1 Ce qu'on observe, le piège des moyennes | Questions de positionnement ; Ex. 1 |
| 2 | 2 h | 2 | ch. 2 Métriques GPU : DCGM | Ex. 2 |
| 3 | 2.5 h | 2 | ch. 3 Prometheus et Grafana pour le calcul | Lab 14.1 partie A ; Ex. 3, 11 |
| 4 | 2 h | 2 | ch. 4 Journaux et traces | Lecture des parties B et D du lab 14.3 ; Ex. 4 |
| 5 | 2.5 h | 2 | ch. 5 Observabilité des ordonnanceurs | Lab 14.1 partie B (Slurm) ; Ex. 5 |
| 6 | 2.5 h | 2 | ch. 6 SLO de plateforme et goodput | Lab 14.2 première moitié ; Ex. 6 |
| 7 | 3 h | 3 | ch. 7 Pannes silencieuses | Lab 14.2 mutation ; Ex. 7, 8 |
| 8 | 3 h | 3 | Lab 14.3 parties A et B | Ex. 9 |
| 9 | 2 h | 3 | ch. 8 Suivi d'expériences et reproductibilité | Lab 14.3 partie C ; Ex. 10 |
| 10 | 2 h | 3 | Checkpoint de sortie, démarrage du Projet 5 | Reprise de l'exercice 9 |

<!-- gen:travailler -->
### Comment travailler ce module {#travailler}

Le parcours s'adresse à plusieurs profils d'entrée, décrits dans le [point de départ](../../profile/index.html). Le tableau donne la priorité conseillée pour ce module ; les questions de positionnement (section 0.1) la confirment ou la corrigent.

| Profil d'entrée | Priorité | Ce que cela veut dire ici |
|---|---|---|
| Ingénieur plateforme, SRE ou DevOps | survol guidé | les questions de positionnement, les chapitres signalés ci-dessous, un lab et le checkpoint |
| Administrateur ou ingénieur HPC | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Ingénieur ML ou chercheur | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Développeur logiciel ou systèmes | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Étudiant ou personne en reconversion | à fond | tous les chapitres, tous les labs et les exercices ★★★ |

**À ne pas survoler.** Les pannes silencieuses des GPU et les SLO de calcul sont nouveaux même pour une équipe d'observabilité expérimentée.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le checkpoint de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si elles vous semblent routinières, parcourez les exercices ★★★ et passez au module 15.

1.  **Utilisation.** Un GPU affiche 100 % d'utilisation (`GPU_UTIL`). Que pouvez-vous en conclure sur son travail utile ?

2.  **Moyennes.** Un job de 64 GPU dont un seul GPU est ralenti affiche une fréquence moyenne quasi normale. Pourquoi cette moyenne est-elle le mauvais indicateur, et lequel la remplace ?

3.  **Étiquettes.** Pourquoi ne pas ajouter l'identifiant du job comme étiquette sur chaque métrique GPU ?

::: sol
**Réponses.**

1.  Presque rien. Selon la documentation de `nvidia-smi`, cette valeur est le pourcentage de temps, sur la période d'échantillonnage, pendant lequel **un ou plusieurs noyaux** s'exécutaient sur le GPU. Un seul noyau minuscule suffit à la rendre égale à 100 %. Voir le chapitre 2.

2.  Dans un entraînement synchrone, chaque étape attend le rang le plus lent : c'est le **minimum** (ou le maximum du temps de calcul) qui compte, pas la moyenne. Il faut surveiller les extrêmes et l'écart à la médiane. Voir les chapitres 1 et 7.

3.  Parce que chaque nouvelle valeur d'étiquette crée de nouvelles séries : un identifiant de job change à chaque job et fait grossir l'index. La documentation de Prometheus déconseille les étiquettes à forte cardinalité. On joint le job au moment de la requête. Voir le chapitre 3.
:::

## 1. Ce qu'on observe {#ch1}

Avant de choisir un outil, il faut savoir quelles questions on veut pouvoir poser à la flotte, et à quelle couche chaque réponse se trouve. Ce chapitre pose le cadre et démonte le premier piège du métier : croire une moyenne.

### 1.1. Cinq couches, une clé de corrélation

Une flotte d'entraînement se lit en cinq couches. Chacune a sa source, son rythme et ses pannes typiques.

-   **Le modèle et l'entraîneur** : perte, pas d'optimisation, tokens par seconde, durée des étapes. C'est la seule couche qui sait si le travail avance.
-   **Les GPU** : fréquences, température, puissance, mémoire, erreurs matérielles (codes XID : les messages d'erreur du pilote NVIDIA), activité des unités de calcul (DCGM, chapitre 2).
-   **Le nœud** : processeur, mémoire, disque, noyau, réseau. Les erreurs matérielles apparaissent aussi dans le journal du noyau.
-   **Le réseau et le stockage** : compteurs d'erreurs des cartes, débit de lecture des données, latence d'écriture des *checkpoints* (points de reprise de l'entraînement).
-   **L'ordonnanceur** : files, états des nœuds, jobs en attente ou en échec (chapitre 5).

<figure class="fig">
<svg viewBox="0 0 680 290" role="img" aria-labelledby="f1-t f1-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="f1-t">Cinq sources, deux magasins, un chemin vers l'astreinte</title>
<desc id="f1-d">Les métriques de l'entraîneur, des GPU, des nœuds et de l'ordonnanceur vont dans Prometheus ; les journaux vont dans Loki. Prometheus évalue des règles et envoie les alertes à Alertmanager, qui prévient l'astreinte. Les exécutions sont suivies dans MLflow.</desc>
<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs>
<rect x="8" y="14" width="190" height="42" rx="6" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="18" y="32" font-size="13" font-weight="700" fill="currentColor">Entraîneur</text>
<text x="18" y="48" font-size="11" fill="currentColor">pas, perte, tokens/s</text>
<line x1="198" y1="35" x2="262" y2="70" stroke="currentColor" stroke-opacity=".6" marker-end="url(#ar)"/>
<rect x="8" y="66" width="190" height="42" rx="6" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="18" y="84" font-size="13" font-weight="700" fill="currentColor">GPU</text>
<text x="18" y="100" font-size="11" fill="currentColor">DCGM : util., tensor, XID</text>
<line x1="198" y1="87" x2="262" y2="70" stroke="currentColor" stroke-opacity=".6" marker-end="url(#ar)"/>
<rect x="8" y="118" width="190" height="42" rx="6" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="18" y="136" font-size="13" font-weight="700" fill="currentColor">Nœud</text>
<text x="18" y="152" font-size="11" fill="currentColor">noyau, disque, réseau</text>
<line x1="198" y1="139" x2="262" y2="70" stroke="currentColor" stroke-opacity=".6" marker-end="url(#ar)"/>
<rect x="8" y="170" width="190" height="42" rx="6" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="18" y="188" font-size="13" font-weight="700" fill="currentColor">Ordonnanceur</text>
<text x="18" y="204" font-size="11" fill="currentColor">Slurm, Kubernetes</text>
<line x1="198" y1="191" x2="262" y2="70" stroke="currentColor" stroke-opacity=".6" marker-end="url(#ar)"/>
<rect x="8" y="222" width="190" height="42" rx="6" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="18" y="240" font-size="13" font-weight="700" fill="currentColor">Journaux</text>
<text x="18" y="256" font-size="11" fill="currentColor">rangs, noyau, Slurm</text>
<line x1="198" y1="243" x2="262" y2="205" stroke="currentColor" stroke-opacity=".6" marker-end="url(#ar)"/>
<rect x="264" y="40" width="130" height="64" rx="6" fill="none" stroke="var(--accent)" stroke-width="2.5"/>
<text x="329" y="66" text-anchor="middle" font-size="14" font-weight="700" fill="currentColor">Prometheus</text>
<text x="329" y="84" text-anchor="middle" font-size="11" fill="currentColor">séries, règles</text>
<rect x="264" y="178" width="130" height="54" rx="6" fill="none" stroke="var(--accent)" stroke-width="2.5"/>
<text x="329" y="202" text-anchor="middle" font-size="14" font-weight="700" fill="currentColor">Loki</text>
<text x="329" y="220" text-anchor="middle" font-size="11" fill="currentColor">lignes, flux</text>
<line x1="394" y1="72" x2="458" y2="72" stroke="currentColor" marker-end="url(#ar)"/>
<rect x="460" y="40" width="150" height="64" rx="6" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="535" y="66" text-anchor="middle" font-size="13" font-weight="700" fill="currentColor">Alertmanager</text>
<text x="535" y="84" text-anchor="middle" font-size="11" fill="currentColor">groupes, silences</text>
<line x1="535" y1="104" x2="535" y2="140" stroke="currentColor" marker-end="url(#ar)"/>
<rect x="460" y="142" width="150" height="40" rx="6" fill="none" stroke="currentColor" stroke-width="1.5"/>
<text x="535" y="167" text-anchor="middle" font-size="13" font-weight="700" fill="currentColor">Astreinte</text>
<line x1="394" y1="205" x2="458" y2="205" stroke="currentColor" stroke-opacity=".6" stroke-dasharray="5 4" marker-end="url(#ar)"/>
<rect x="460" y="188" width="150" height="40" rx="6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="5 4"/>
<text x="535" y="213" text-anchor="middle" font-size="12" fill="currentColor">enquête (corrélation)</text>
<text x="340" y="278" text-anchor="middle" font-size="12" fill="currentColor">La clé de corrélation commune : l'identifiant du job et le nom du nœud.</text>
</svg>
<figcaption>Les sources et leurs deux magasins. Les métriques servent à alerter, les journaux à comprendre. La jointure se fait sur le job et le nœud, pas dans les étiquettes de chaque série.</figcaption>
</figure>
La difficulté n'est pas de collecter, c'est de **relier**. Un entraînement ralenti se manifeste dans la couche du modèle (tokens par seconde en baisse), son origine dans une autre (un GPU qui chauffe), et la décision dans une troisième (drainer le nœud dans Slurm). La clé commune est le couple « job, nœud » : tout le module revient sur la façon de la porter sans exploser le nombre de séries.

### 1.2. Métriques, journaux, traces

Les trois formes de données répondent à trois questions différentes.

1.  **Les métriques** sont des séries numériques échantillonnées à intervalle fixe. Elles sont compactes, agrégeables, et servent à **alerter** : « combien, à quelle vitesse, depuis quand ».
2.  **Les journaux** (*logs*) sont des événements textuels horodatés. Ils sont volumineux et coûteux à indexer, et servent à **comprendre** : « que s'est-il passé sur ce rang à cet instant ».
3.  **Les traces** décomposent une opération en étapes imbriquées (des *spans*). Pour un entraînement, une étape se découpe en chargement des données, calcul, communication et écriture ; la trace dit où le temps passe.

Une règle pratique : alertez sur des métriques, enquêtez dans les journaux, optimisez avec des traces. Inverser l'ordre coûte cher : une alerte fondée sur une recherche de texte dans des téraoctets de journaux est lente et fragile.

### 1.3. Le piège de la moyenne

Dans un entraînement synchrone, chaque étape se termine quand le rang le plus lent a fini (un **rang**, *rank*, est l'un des processus parallèles de l'entraînement, en général un par GPU). La fréquence moyenne des GPU, la température moyenne ou l'utilisation moyenne de la flotte sont donc des indicateurs **aveugles à l'unique GPU qui compte**.

::: ex
[Exemple 1.1 — Un GPU sur 64 à 60 % de sa fréquence]{.tag} Un job occupe 64 GPU ; 63 tournent à 1 980 MHz et un seul à 1 188 MHz (60 %), par exemple à cause d'une limitation thermique. Les valeurs sont celles d'un calcul, pas d'une mesure.

La fréquence moyenne est $(63 \times 1980 + 1188)/64 = 1\,967{,}6$ MHz : elle ne baisse que de 0,63 %. Elle donne l'impression que tout va bien.

Supposons que 80 % d'une étape soit du calcul proportionnel à la fréquence et 20 % de la communication. Le rang lent allonge le calcul de $1/0{,}6$, et tous les autres l'attendent :

$$\text{durée relative d'une étape} = 0{,}2 + \frac{0{,}8}{0{,}6} = 1{,}533$$

Le débit tombe à $1/1{,}533 = 65{,}2\ \%$ de la normale : l'équivalent de 22,3 GPU sur 64 est perdu, alors que la moyenne est inchangée. Surveiller le **minimum** de la fréquence (ou le rapport minimum sur médiane) aurait montré 0,60 tout de suite. C'est exactement ce que calcule la métrique `gpu_node_sm_clock_min_over_median_ratio` du lab 14.1.
:::

La même logique vaut pour tout agrégat : une moyenne lisse l'événement rare, qui est précisément ce qu'on cherche. Préférez le minimum, le maximum, un percentile ou le nombre d'éléments hors norme.

### 1.4. La résolution du temps

Un événement plus court que l'intervalle d'échantillonnage peut passer entre deux mesures. Un échantillonnage toutes les 15 s voit un événement de 3 s avec une probabilité de $3/15 = 20\ \%$ (si les instants sont indépendants).

Et l'exportateur de GPU a son propre rythme : la documentation de dcgm-exporter donne un intervalle de collecte par défaut de 30 000 ms. Prometheus qui grattera (*scrape*) toutes les 15 s relira donc chaque valeur deux fois, et la résolution réelle est celle du plus lent des deux. Pour un événement de 3 s, la probabilité d'être vu tombe à 10 %.

::: note
[Compter plutôt qu'échantillonner]{.tag} Pour ne rien rater, on préfère les **compteurs** (erreurs, événements de limitation, énergie) aux jauges : un compteur garde la trace de ce qui s'est passé entre deux scrapes, une jauge non. Cette distinction fonde le choix des métriques au chapitre 2.
:::

::: recap
Points clés — chapitre 1

-   Cinq couches : modèle, GPU, nœud, réseau et stockage, ordonnanceur. La clé de corrélation est le couple job et nœud.
-   Alertez sur des métriques, enquêtez dans les journaux, optimisez avec des traces.
-   En synchrone, le rang le plus lent fixe le rythme : surveillez les extrêmes, pas la moyenne.
-   Un événement plus court que l'intervalle d'échantillonnage peut être manqué ; préférez les compteurs aux jauges.
:::

## 2. Métriques GPU : DCGM et dcgm-exporter {#ch2}

NVIDIA fournit un gestionnaire de GPU de centre de données, DCGM, et un exportateur qui publie ses mesures au format Prometheus. Ce chapitre explique ce qu'ils exposent, avec une attention particulière aux métriques qu'on lit mal.

### 2.1. DCGM et son exportateur

DCGM (*Data Center GPU Manager*) tourne comme un service (`nv-hostengine`) qui interroge les GPU. `dcgm-exporter` l'embarque et publie ses mesures sur HTTP. D'après la documentation de NVIDIA lue le 24 octobre 2026, l'exportateur écoute par défaut sur le port 9400, collecte toutes les 30 000 ms, et active la correspondance entre GPU et pods Kubernetes avec l'option `-k`.

Sa liste de métriques par défaut est le fichier `etc/default-counters.csv` du dépôt : 25 métriques par GPU et une étiquette statique (la version du pilote) dans la version lue ce jour. Les étiquettes de chaque série comprennent `gpu`, `UUID`, `device` et `Hostname`.

Un point qui concerne Slurm : DCGM ne sait rien des jobs. Le code source de dcgm-exporter contient une option `--hpc-job-mapping-dir` (variable `DCGM_HPC_JOB_MAPPING_DIR`), décrite comme le chemin d'un répertoire de fichiers de correspondance entre GPU et jobs. Le format de ces fichiers n'a pas été relu pour ce module (voir « À vérifier »). Sans cette option, il faut produire soi-même la jointure, comme le font le lab 14.1 et le projet 5.

### 2.2. Les familles de métriques

| Famille | Exemples de la liste par défaut | Type | Sert à |
|---|---|---|---|
| Horloges | `DCGM_FI_DEV_SM_CLOCK`, `MEM_CLOCK` | jauge | repérer une limitation de fréquence |
| Température, puissance | `GPU_TEMP`, `MEMORY_TEMP`, `POWER_USAGE` | jauge | chauffe, consommation |
| Énergie | `TOTAL_ENERGY_CONSUMPTION` | compteur (mJ) | coût énergétique d'un job |
| Utilisation | `GPU_UTIL`, `MEM_COPY_UTIL` | jauge | présence de noyaux (voir 2.3) |
| Profil | `PROF_GR_ENGINE_ACTIVE`, `PROF_PIPE_TENSOR_ACTIVE`, `PROF_DRAM_ACTIVE` | jauge | intensité réelle du calcul |
| Mémoire | `FB_USED`, `FB_FREE` | jauge (MiB) | risque de saturation |
| Erreurs | `XID_ERRORS`, `UNCORRECTABLE_REMAPPED_ROWS`, `ROW_REMAP_FAILURE` | jauge ; compteur pour les lignes remappées | santé matérielle |
| Bus | `PCIE_REPLAY_COUNTER`, `PROF_PCIE_TX_BYTES` | compteur, jauge | liaisons dégradées |

Les métriques du groupe « profil » portent un commentaire dans le fichier : elles sont prises en charge sur les GPU de centre de données de génération Volta ou plus récente. Sur d'autres GPU, elles sont absentes : une règle qui en dépend doit gérer ce cas.

::: note
[Une jauge qui ressemble à un compteur]{.tag} `DCGM_FI_DEV_XID_ERRORS` est une **jauge** dont le texte d'aide dit « valeur de la dernière erreur XID rencontrée ». Elle ne compte pas les erreurs : elle garde la dernière valeur rencontrée, et un `rate()` dessus n'a aucun sens. Les sources lues ne disent pas quand elle revient à zéro (à vérifier sur matériel, voir le projet 5). Une règle correcte teste `> 0` et la durée `for` évite les rebonds. Le projet 5 en fait un test.
:::

### 2.3. Ce que l'utilisation GPU ne dit pas

La documentation de `nvidia-smi` définit l'utilisation du GPU ainsi : « pourcentage de temps, sur la période d'échantillonnage écoulée, pendant lequel un ou plusieurs noyaux s'exécutaient sur le GPU », avec une période comprise entre 1 s et 1/6 s selon le produit. Rien n'est dit de la quantité de travail : un noyau qui occupe un seul multiprocesseur compte autant qu'un noyau qui les occupe tous.

La documentation de DCGM décrit les métriques de profil, plus fines, en termes de cycles :

-   `PROF_GR_ENGINE_ACTIVE` : la fraction du temps où une partie du moteur graphique ou de calcul est active.
-   `PROF_SM_ACTIVE` : la fraction du temps où au moins un *warp* (groupe de threads exécutés ensemble) est actif sur un multiprocesseur (*streaming multiprocessor*, SM), moyennée sur tous. Un *warp* en attente de la mémoire compte comme actif. Cette métrique est commentée dans `default-counters.csv` : il faut l'activer soi-même.
-   `PROF_PIPE_TENSOR_ACTIVE` : la fraction des cycles où l'unité de calcul matriciel (HMMA ou IMMA) est active.

::: ex
[Exemple 2.1 — Même SM_ACTIVE, utilisation de 100 % ou de 20 %]{.tag} La documentation de DCGM donne deux cas qui produisent le **même** `SM_ACTIVE` de 0,2 : un noyau qui lance $N/5$ blocs sur un GPU à $N$ multiprocesseurs pendant tout l'intervalle, ou un noyau qui lance $N$ blocs pendant un cinquième de l'intervalle, les multiprocesseurs restant sinon inactifs.

Dans le premier cas, des noyaux s'exécutent tout le temps : `GPU_UTIL` vaut 100 %. Dans le second, un noyau s'exécute un cinquième du temps : `GPU_UTIL` vaut 20 %. Mais dans le premier cas, 80 % des multiprocesseurs sont inactifs en permanence. Un GPU à 100 % d'utilisation peut donc avoir un `SM_ACTIVE` cinq fois plus faible qu'un autre GPU qui affiche lui aussi 100 %.

La même documentation précise qu'une valeur de `SM_ACTIVE` de 0,8 ou plus est « nécessaire mais pas suffisante » pour un usage efficace, et qu'une valeur inférieure à 0,5 indique probablement un usage inefficace. Pour `TENSOR_ACTIVE`, 0,2 peut signifier 20 % des multiprocesseurs à pleine charge, ou tous à 20 %, ou toute combinaison intermédiaire.
:::

Conséquence pour l'exploitation : l'utilisation GPU sert à détecter un GPU **réservé et inactif** (zéro prolongé), jamais à prouver que l'entraînement est sain. Selon une hypothèse plausible mais non sourcée ici, un entraînement bloqué dans une communication collective peut garder des noyaux d'attente en boucle et afficher une utilisation élevée avec une activité tensorielle nulle ; cette signature est une **hypothèse** utilisée par ce cours et par le projet 5, non une mesure faite ici. Elle est à valider sur vos GPU.

### 2.4. Lire un scrape

Voici les lignes de la fixture du lab 14.1 qui correspondent aux trois GPU en difficulté. La fixture est **simulée** (aucun GPU) mais reprend les noms et le format de dcgm-exporter.

~~~text
DCGM_FI_DEV_GPU_TEMP{gpu="3",UUID="GPU-sim-gpu-n01-3",device="nvidia3",modelName="SIM-GPU 80GB",Hostname="gpu-n01"} 88
DCGM_FI_DEV_SM_CLOCK{gpu="3",...} 1190
DCGM_FI_DEV_GPU_UTIL{gpu="5",...} 99
DCGM_FI_PROF_PIPE_TENSOR_ACTIVE{gpu="5",...} 0
DCGM_FI_DEV_POWER_USAGE{gpu="5",...} 255
DCGM_FI_DEV_XID_ERRORS{gpu="6",...} 79
~~~

Le GPU 3 est chaud et ralenti : un traînard thermique. Le GPU 5 a une utilisation de 99 %, une puissance nettement sous la normale (255 W contre environ 620 W, la moyenne des cinq GPU sains du nœud) et un tensor à zéro : la signature du blocage supposée plus haut. Le GPU 6 a rapporté un code XID 79. Le catalogue XID de NVIDIA l'associe à « GPU has fallen off the bus » : le GPU n'est plus joignable sur le bus, ce qui impose en général une intervention sur le nœud.

Les codes 94 et 95 du même catalogue concernent les GPU qui isolent les erreurs mémoire (à partir des A100) : le 94 reste confiné à une application, qu'il faut relancer, le 95 touche plusieurs applications et impose de réinitialiser le GPU.

::: note
[`promtool` refuse le format de dcgm-exporter]{.tag} Sur le bac à sable (promtool 2.45.3, le 24 octobre 2026), `promtool check metrics` appliqué à un scrape au format de dcgm-exporter échoue avec le code de sortie 3 et un message par série du type « label names should be written in 'snake_case' not 'camelCase' », à cause des étiquettes `modelName` et `Hostname`. 

Ce n'est pas une erreur de l'exposition mais une règle de style que les étiquettes d'un fournisseur ne respectent pas. Conséquence : ne mettez pas ce lint en barrière sur la sortie d'un exportateur tiers, et gardez des noms conformes pour vos propres métriques (le lab 14.1 passe le lint). Source : sortie réelle de `promtool`, relevée par l'auteur.
:::

### 2.5. Hors de NVIDIA : mêmes questions, autres noms

Une flotte peut mêler des GPU NVIDIA et AMD, voire des accélérateurs Ascend ([module 4, chapitre 9](../gpu-programming/index.html#ch9)). Chez AMD, l'*AMD Device Metrics Exporter* (documentation de la version 1.5.3, lue le 25 octobre 2026) publie au format Prometheus sur le port 5000. Ses séries sont en minuscules (`gpu_gfx_activity`, `gpu_clock`) et portent les étiquettes `gpu_id` et `hostname`, là où dcgm-exporter écrit `gpu` et `Hostname`.

Les équivalences ne sont pas exactes. `GPU_GFX_ACTIVITY`, le pendant de `GPU_UTIL`, est un pourcentage d'usage du moteur graphique ; en mode partitionné, il n'est rapporté que pour la partition principale. `GPU_PROF_TENSOR_ACTIVE_PERCENT`, le pendant de `PIPE_TENSOR_ACTIVE`, est un **pourcentage** d'utilisation des unités matricielles (MFMA), là où DCGM donne une fraction entre 0 et 1 ; il n'est pas exporté sur les GPU Radeon.

L'intégration de cet exportateur à Slurm ajoute, par un prologue et un épilogue, les étiquettes `job_id` et `job_user` aux métriques : c'est l'étiquette que la section 3.2 déconseille, à mesurer avant de l'activer. Pour Ascend, la santé se lit par `npu-smi info` (module 4, § 9.5) ; son exportateur n'a pas été relu ici. **Non vérifié** : rien de cette section n'a tourné sur un GPU AMD ou un accélérateur Ascend. L'exercice 11 réécrit une alerte pour une flotte mixte.

::: recap
Points clés — chapitre 2

-   dcgm-exporter publie par défaut sur le port 9400, collecte toutes les 30 s ; sa liste par défaut compte 25 métriques par GPU.
-   `GPU_UTIL` mesure la présence de noyaux, pas le travail ; les métriques de profil (`SM_ACTIVE`, `TENSOR_ACTIVE`) sont plus informatives mais ne disent pas tout.
-   `XID_ERRORS` est une jauge du dernier code, non un compteur ; le XID 79 est « GPU has fallen off the bus ».
-   DCGM ne connaît pas les jobs : la jointure avec Slurm est à votre charge.
-   La signature « utilisation haute, tensor nul » d'un blocage est une hypothèse à valider sur votre matériel.
-   Hors de NVIDIA, les questions restent mais les noms, les unités et les étiquettes changent (AMD : pourcentages, `gpu_id`, `hostname`) : normalisez avant de joindre.
:::

## 3. Prometheus et Grafana pour le calcul {#ch3}

Vous connaissez Prometheus. Ce chapitre ne reprend que ce qui change pour une flotte d'entraînement : le dimensionnement chiffré, la cardinalité des jobs, les règles d'enregistrement, et les cas où le modèle « on gratte des services qui vivent longtemps » ne tient pas.

### 3.1. Dimensionner avant de déployer

La documentation de Prometheus donne une formule de planification et un ordre de grandeur : un échantillon occupe en moyenne **1 à 2 octets** sur disque, et

$$\text{disque} = \text{rétention (s)} \times \text{échantillons par seconde} \times \text{octets par échantillon}$$

La rétention par défaut est de 15 jours si aucune durée ni taille n'est donnée. Les échantillons sont regroupés en blocs de deux heures, compactés ensuite. Le disque n'est pas le seul coût : la mémoire dépend du nombre de séries actives, qu'il faut mesurer chez vous plutôt que d'en croire une règle générale.

::: ex
[Exemple 3.1 — 1 024 GPU, 25 métriques, 15 secondes]{.tag} Une flotte de 128 nœuds de 8 GPU, avec la liste par défaut de dcgm-exporter (25 métriques par GPU), donne $1024 \times 25 = 25\,600$ séries. Gratté toutes les 15 s, cela fait $25\,600/15 = 1\,707$ échantillons par seconde.

Sur 15 jours ($1\,296\,000$ s), cela représente $2{,}21 \times 10^9$ échantillons, soit **2,2 à 4,4 Go** à 1–2 octets par échantillon. C'est un plancher : les métriques du nœud, de l'ordonnanceur et de l'entraîneur s'y ajoutent.

Si vous grattez à 30 s, au rythme de collecte de l'exportateur, tout est divisé par deux (1,1 à 2,2 Go) sans perte d'information, puisque la valeur ne change qu'une fois par 30 s.
:::

Le résultat surprend par sa modestie : le coût d'une flotte de GPU n'est pas dans le volume des échantillons mais dans la **cardinalité**, c'est-à-dire le nombre de séries distinctes que l'on crée au fil du temps.

### 3.2. La cardinalité et le piège de l'étiquette `job`

La documentation de Prometheus avertit : chaque combinaison unique de paires clé-valeur d'étiquettes représente une nouvelle série, et il ne faut pas utiliser d'étiquettes pour stocker des dimensions à forte cardinalité (identifiants d'utilisateur, adresses électroniques, ensembles non bornés).

Un identifiant de job est un tel ensemble non borné : il change à chaque job. Dans un cluster, la tentation est grande de l'ajouter à chaque métrique GPU pour pouvoir filtrer par job.

::: ex
[Exemple 3.2 — Le coût de l'étiquette `job`]{.tag} Même flotte (128 nœuds), jobs de 8 GPU qui durent 4 h en moyenne, et 10 métriques GPU portant l'étiquette `job`. Il y a 128 emplacements de job. Chaque jour : $128 \times 24/4 = 768$ jobs, donc $768 \times 8 \times 10 = 61\,440$ nouvelles séries.

La flotte n'a que $1024 \times 10 = 10\,240$ séries de base. L'étiquette fait donc **créer six fois plus de séries par jour** que la flotte n'en compte, alors que le nombre de séries actives à un instant donné reste le même. L'index grossit, les blocs se compactent plus difficilement, et les requêtes sur plusieurs jours parcourent des milliers de séries de quelques heures. (Calcul arithmétique ; l'effet réel sur votre serveur est à mesurer.)
:::

La parade est de **joindre au moment de la requête**. Un exportateur de plateforme (celui du projet 5, pas celui du lab 14.1) publie une métrique d'association qui vaut toujours 1, `slurm_job_gpu_allocated{Hostname, gpu, job}`, et les règles font la jointure :

~~~yaml
expr: avg by (job) (DCGM_FI_PROF_PIPE_TENSOR_ACTIVE
      * on (Hostname, gpu) group_left (job) slurm_job_gpu_allocated) < 0.05
~~~

Le projet 5 vous fera écrire et tester avec `promtool` une règle de ce type (`JobStalled`). Seule la série d'association porte le job : elle apparaît et disparaît avec lui, les 25 séries du GPU restent stables. Deux protections complètent la parade : la limite `sample_limit` d'un travail de scrape, qui fait échouer le scrape entier si l'exportateur dépasse le nombre d'échantillons autorisé (le défaut 0 signifie aucune limite), et un test de budget de séries dans la suite de tests de l'exportateur, comme dans le lab 14.1.

### 3.3. Règles d'enregistrement

Une règle d'enregistrement calcule une expression à intervalle fixe et la stocke comme une nouvelle série. Elle sert à deux choses : rendre rapide une requête coûteuse sur laquelle des tableaux de bord s'appuient, et donner un nom stable à une notion que plusieurs alertes partagent. La documentation recommande la forme `niveau:métrique:opérations`, où le niveau désigne l'agrégation et les étiquettes conservées.

~~~yaml
- record: job:train_compute_seconds:median
  expr: quantile by (job) (0.5, train_compute_seconds)
- record: node:train_compute_seconds:ratio_to_job_median
  expr: train_compute_seconds / on (job) group_left () job:train_compute_seconds:median
~~~

::: ex
[Exemple 3.3 — Un traînard par règle d'enregistrement, testé]{.tag} Ces deux règles viennent du lab 14.2. La métrique `train_compute_seconds` est le temps de calcul local de la dernière étape, **sans l'attente des collectives** (voir le chapitre 7 : en synchrone, le temps d'étape complet est identique pour tous les rangs).

Le test `tests/platform.rules.test.yml` fournit cinq rangs du job `j1` à 1,0 s et le rang 5 à 1,5 s, et un job `j2` dont un rang est à 1,2 s. La règle `NodeSlow` (seuil 1,3, `for: 10m`) ne répond rien à 9 minutes, puis à 12 minutes une seule alerte, `job j1: node n5 rank 5 computes 1.5x slower than the job median`. Le rang à 1,2 reste silencieux. Résultat de `promtool test rules` : `SUCCESS`, et le mutant « seuil 1,3 remplacé par 3 » est tué.
:::

### 3.4. Ce qui change avec des jobs éphémères

Trois particularités du calcul méritent d'être traitées explicitement.

**Les séries de job naissent et meurent.** Quand un job se termine, ses séries ne se mettent plus à jour et deviennent périmées (*stale*). Une alerte « plus de progrès » ne peut donc pas reposer sur l'absence : une série absente ne ressemble pas à une série qui stagne. Il faut deux alertes distinctes, toutes deux dans le lab 14.2 : l'une sur la stagnation d'un compteur présent (`JobNoProgress`), l'autre sur la disparition d'un exportateur attendu (`up == 0`, `GpuTelemetryDown`).

**Les métriques de fin de job.** Pour exposer le code de retour ou la durée d'un job, le collecteur *textfile* de `node_exporter` lit tous les fichiers `*.prom` d'un répertoire. Son README recommande d'écrire dans un fichier temporaire puis de le renommer (`mv`), de façon atomique. Un *epilog* Slurm convient à cet usage. La *Pushgateway*, elle, n'est recommandée par la documentation que pour le résultat d'un traitement par lots **au niveau du service**, sans lien avec une machine ; elle n'oublie jamais une série poussée tant qu'on ne l'efface pas.

**Les intervalles.** Une étude de l'infrastructure LLM Acme (Hu et al., 2024) échantillonne Prometheus, DCGM et l'IPMI toutes les 15 s. C'est un bon point de départ, à condition de régler aussi l'intervalle de collecte de dcgm-exporter (30 s par défaut) : gratter plus vite que l'exportateur ne collecte ne sert à rien ; gratter plus lentement rate les événements courts du chapitre 1.

::: note
[Grafana : la hiérarchie compte plus que les panneaux]{.tag} Un tableau de bord utile suit la hiérarchie que l'enquêteur parcourt : flotte, puis job, puis nœud, puis GPU. Trois niveaux de tableaux, liés par les variables `job` et `node`, valent mieux qu'un grand tableau de cent panneaux. Générez-les par code (le projet 5 produit un JSON de Grafana testé) plutôt que de les modifier à la main : un tableau qui n'est pas versionné dérive.
:::

::: recap
Points clés — chapitre 3

-   Disque ≈ rétention × échantillons par seconde × (1 à 2 octets). 1 024 GPU × 25 métriques à 15 s : 2,2 à 4,4 Go pour 15 jours.
-   Le vrai risque est la cardinalité : un identifiant de job en étiquette crée ici six fois plus de séries par jour que la flotte n'en compte.
-   On joint le job à la requête, avec une métrique d'association qui vaut 1.
-   Règles d'enregistrement : nom `niveau:métrique:opérations`, tests `promtool`.
-   Une série absente n'est pas une série qui stagne : deux alertes distinctes.
:::

## 4. Journaux et traces {#ch4}

Les métriques disent qu'un job ne va pas bien ; les journaux disent pourquoi. Ce chapitre traite de ce qu'on journalise, de la façon d'indexer sans se ruiner, et d'un exemple réel de localisation d'un rang fautif.

### 4.1. Ce qu'on journalise, et comment on l'indexe

Les sources utiles sont les journaux de chaque rang (une ligne JSON par événement : identifiant du job, rang, pas, événement), le journal du noyau (les erreurs XID des GPU y apparaissent), ceux de Slurm (`slurmd`, `slurmctld`) et ceux de NCCL (la bibliothèque de communications collectives de NVIDIA) quand ils sont activés. Écrivez des lignes **structurées** : un champ `job_id` et un champ `rank` dans chaque ligne rendent la corrélation triviale.

Loki indexe des **flux** définis par leurs étiquettes, pas le contenu des lignes. Sa documentation dit que les étiquettes sont destinées à des valeurs de faible cardinalité décrivant la source des journaux, et recommande de n'ajouter une étiquette dynamique qu'avec parcimonie : trop de combinaisons produisent trop de flux, donc un gros index et de petits morceaux. Pour les valeurs à forte cardinalité que l'on cherche souvent, elle propose les métadonnées structurées. Appliqué à notre cas :

-   étiquettes (bornées) : `cluster`, `node`, `source` (rang, noyau, slurm) ;
-   métadonnées structurées ou filtre de texte : `job_id`, `rank`.

~~~text
{cluster="train", node="gpu-n01"} |= "job_id=4412" |= "NCCL WARN"
~~~

La requête ci-dessus est écrite d'après la syntaxe de LogQL et n'a **pas** été exécutée : il n'y a pas de Loki dans le bac à sable. ELK joue le même rôle avec un autre modèle de coût (index plein texte) ; le critère de choix est le volume et la durée de rétention de vos journaux, à mesurer.

::: ex
[Exemple 4.1 — Le volume d'un journal par pas]{.tag} Un job de 1 024 rangs journalise une ligne de 200 octets à chaque pas de 2 s. Débit : $1024 \times 0{,}5 \times 200 = 102\,400$ octets par seconde, soit 8,85 Go par jour pour **un seul job**. Journaliser un pas sur 50, plus chaque événement rare (checkpoint, évaluation, erreur), le ramène à environ 0,18 Go par jour. Ces chiffres sont arithmétiques (taille de ligne et cadence supposées).
:::

### 4.2. Localiser un rang fautif

Le [chapitre 8 du module 9](../distributed-training/index.html#ch8) et son lab 9.3 ont localisé un rang bloqué à la main ; ici, on fait de ces signaux des métriques et des alertes.

Le journal le plus précieux d'un blocage est celui des **entrées dans les collectives**. Quand un rang ne rejoint jamais une opération collective (une opération où tous les rangs doivent entrer, comme la somme des gradients, *all-reduce*), tous les autres l'attendent. Il suffit de comparer, rang par rang, le dernier pas où la collective a été **entrée** et celui où elle s'est **terminée** : le rang qui est resté en arrière est le fautif.

C'est le principe du *flight recorder* de PyTorch (module 9, § 8.3), qui vide ses enregistrements à l'expiration du délai d'une collective : d'après la documentation de PyTorch 2.14, 10 minutes par défaut avec NCCL et 30 minutes avec les autres moteurs.

::: ex
[Exemple 4.2 — Un vrai blocage, localisé par les journaux et par les piles]{.tag} Partie B du lab 14.3, **réelle** mais sur CPU : deux processus `torch.distributed` (moteur `gloo`), le rang 1 s'arrête avant la collective du pas 150 (un `time.sleep` injecté). Un observateur à l'horloge réelle voit le compteur de progression stagner 3 s ; le programme envoie `SIGUSR1` aux deux processus et `faulthandler` écrit leurs piles. Sortie capturée sur la VM du bac à sable, le 24 octobre 2026 :

~~~text
ALARM: no progress for 3 s; last completed step = 149
--- rank 0: innermost frames of the stack dump (faulthandler, SIGUSR1)
    distributed_c10d.py:3913 in all_reduce
    c10d_logger.py:83 in wrapper
    real_hang.py:50 in child   -> dist.all_reduce(t)
--- rank 1: innermost frames of the stack dump (faulthandler, SIGUSR1)
    real_hang.py:47 in child   -> time.sleep(3600)  # the fault: this rank never joins the collective
last collective entered: {0: 150, 1: 149}; last collective completed: {0: 149, 1: 149}
rank(s) that never joined the last collective: [1]
~~~

Le rang 0 est bloqué dans `all_reduce` ; le rang 1 est dans `time.sleep`. Les journaux donnent la même réponse sans les piles : le rang 0 est entré dans la collective du pas 150, pas le rang 1. **Ce qui n'est pas démontré ici** : le cas GPU et NCCL, où la signature de l'utilisation GPU et le comportement du délai d'attente diffèrent.
:::

### 4.3. Les traces

Dans OpenTelemetry, un *span* représente une unité de travail ou une opération, et les spans forment les traces. Pour un entraînement, un pas se découpe naturellement : chargement des données, calcul avant et arrière, communication, mise à jour, parfois écriture d'un checkpoint. La trace dit si l'étape lente est le calcul (un traînard), la communication (le réseau) ou les données (le stockage).

La partie D du lab 14.3 le montre sans collecteur : le SDK OpenTelemetry émet un span par pas et un span enfant par phase, que son exportateur `ConsoleSpanExporter` écrit ligne à ligne dans un fichier. Sur vingt pas aux durées **simulées**, le script retrouve par les liens de parenté que le pas 13 dure 3,25 s au lieu de 1,65 s, dont 1,70 s de chargement des données (médiane : 0,10 s).

L'article MegaScale (Jiang et al., 2024) décrit un outil qui enregistre des événements CUDA à grain fin pour produire une carte de chaleur et une chronologie à l'échelle du système, et des messages de battement de cœur pour la détection d'anomalies en temps réel. Le coût d'une trace systématique est rédhibitoire : 1 024 rangs × 5 spans par pas de 2 s font $2\,560$ spans par seconde, soit 221 millions par jour. **Échantillonnez** : un pas sur cent produit 2,2 millions de spans par jour, et on trace en plus tous les pas plus lents qu'un seuil.

::: recap
Points clés — chapitre 4

-   Journalisez des lignes structurées avec `job_id` et `rank` ; indexez peu d'étiquettes, filtrez le reste.
-   Dans un blocage, comparez par rang le dernier pas entré et le dernier pas terminé d'une collective : le rang en retard est le fautif.
-   Le flight recorder de PyTorch automatise cela ; le délai par défaut est de 10 min avec NCCL.
-   Une trace de pas se découpe en données, calcul, communication, mise à jour : échantillonnez-la.
:::

## 5. Observabilité des ordonnanceurs {#ch5}

L'ordonnanceur est la couche qui sait pourquoi un job attend, quels nœuds sont retirés de la production et combien de capacité reste. Ce chapitre exporte ces réponses sans exploser la cardinalité, et s'appuie sur des captures réelles de Slurm 23.11.4.

### 5.1. Les questions de la file

Quatre questions suffisent à piloter une file : combien de jobs attendent et **pourquoi** ; depuis combien de temps le plus ancien attend ; combien de nœuds sont en panne ou drainés ; combien de CPU ou de GPU sont alloués, libres ou inutilisables. Les deux premières mesurent le service rendu aux utilisateurs, les deux dernières la capacité de la plateforme.

### 5.2. Exporter Slurm

Le lab 14.1 lit `squeue --json`, `sinfo --json` et `sacct`. Deux raisons d'utiliser le format JSON plutôt que d'analyser le texte. La première : un exportateur libre documente, dans son README lu le 24 octobre 2026, que la disposition textuelle de Slurm « n'est pas une API stable et a changé entre les versions », et exige Slurm 23.02 ou plus pour analyser le JSON. La seconde est que les noms de champs JSON sont explicites.

Une précaution de charge : la page de manuel de `squeue` avertit que chaque appel envoie un appel de procédure distante à `slurmctld` et que, si trop de commandes arrivent à la fois, elles peuvent dégrader les performances du démon, jusqu'à un déni de service. Un exportateur doit donc **mettre en cache** et gratter à 30 ou 60 s, jamais à chaque requête de tableau de bord. Le lab interroge `sacct`, plus lourd, séparément toutes les 30 s.

| Métrique du lab 14.1 | Type | Étiquettes (bornées) |
|---|---|---|
| `slurm_jobs` | jauge | `state`, `reason_class` |
| `slurm_pending_oldest_age_seconds` | jauge | `reason_class` |
| `slurm_nodes` | jauge | `partition`, `state` |
| `slurm_node_drain_info` | jauge (1) | `node`, `reason_class` |
| `slurm_cpus` | jauge | `partition`, `state` |
| `slurm_job_wait_seconds` | histogramme | `qos` |

Les exportateurs libres exposent aussi des métriques par compte et par utilisateur. C'est utile pour la facturation interne, mais le nombre d'utilisateurs borne la cardinalité : relisez la liste avant de l'activer sur une grande organisation.

### 5.3. Pourquoi un job attend

La raison d'attente de Slurm (`Priority`, `Resources`, `JobHeldUser`, `Dependency`…) est la meilleure information de la file, mais elle prend des dizaines de valeurs, dont certaines changent de version en version. Exportez-la telle quelle comme étiquette et vous perdez le contrôle du nombre de séries. Le lab regroupe donc les raisons par **responsable de l'action** :

| Classe | Raisons (page de manuel de `squeue`) | Qui agit |
|---|---|---|
| `capacity` | `Priority`, `Resources`, `ReqNodeNotAvail` | la plateforme |
| `user` | `JobHeldUser`, `Dependency`, `BeginTime` | l'utilisateur |
| `admin` | `JobHeldAdmin`, `Reservation`, `PartitionDown` | un administrateur |
| `config` | `InvalidAccount`, `InvalidQOS` | l'administrateur, tout de suite |
| `other` | toute raison inconnue | à examiner |

Le regroupement est un choix de ce cours ; les raisons sont celles de Slurm. Son intérêt est de distinguer ce qui pèse sur le SLO de la plateforme (`capacity`) de ce qui n'y pèse pas (`user`).

Deux classes s'ajoutent hors de ce tableau. Un job en cours n'a pas de raison d'attente : il porte la classe `none`. Pour un nœud drainé ou en panne, `slurm_node_drain_info` classe la raison de drainage d'après le préfixe convenu au module 5 : `health`, `maintenance` ou `other`.

::: ex
[Exemple 5.1 — La file vue par l'exportateur, sur un vrai Slurm]{.tag} Sur le bac à sable (Slurm 23.11.4, 4 CPU), cinq jobs de 3 CPU se disputent le nœud, qui est ensuite drainé avec la raison `health: gpu_xid:79`. Sortie réelle de `exporter.py` en mode direct, le 24 octobre 2026 (la partie GPU, elle, provient de la fixture simulée) :

~~~text
slurm_jobs{reason_class="capacity",state="pending"} 4.0
slurm_jobs{reason_class="none",state="running"} 1.0
slurm_pending_oldest_age_seconds{reason_class="capacity"} 26.97
slurm_nodes{partition="debug",state="draining"} 1.0
slurm_node_drain_info{node="vm",reason_class="health"} 1.0
slurm_cpus{partition="debug",state="allocated"} 3.0
slurm_cpus{partition="debug",state="idle"} 0.0
slurm_cpus{partition="debug",state="other"} 1.0
slurm_scrape_success 1.0
~~~

Lisez la file en trois lignes : quatre jobs attendent à cause de la **plateforme** (classe `capacity`), le plus ancien depuis 27 s ; le nœud est en cours de drainage pour une raison de santé ; il reste un CPU « autre » (inutilisable) et zéro CPU libre.

Dans la capture `squeue_drained.json`, associée à `sinfo_draining.json`, trois jobs en `Priority` ou `Resources` sont classés en `capacity` pendant que le nœud est en drainage. La raison `ReqNodeNotAvail` (nœud requis indisponible, par exemple drainé), absente de ces captures, est classée de la même façon : c'est la plateforme, pas l'utilisateur, qui fait perdre du temps au job.
:::

### 5.4. Le délai d'attente et ses seaux

Le délai d'attente d'un job est la différence entre son démarrage et sa soumission. Exposé comme **histogramme** de Prometheus, chaque job est compté une fois, dans le seau de sa durée. Le lab 14.1 dédoublonne par identifiant de job : un histogramme ne doit que croître, et deux lectures du même `sacct` ne doivent pas compter deux fois.

Pour une file réelle, la soumission est un mauvais départ : un job retenu par son propriétaire ou en attente d'une dépendance semble attendre des heures sans que la plateforme y soit pour rien. Le champ `Eligible` de `sacct` (début de l'éligibilité) est plus juste ; le lab utilise `Submit` pour rester simple, et cette limite est à lever en production.

Pour le quantile $\phi$ de $n$ jobs, `histogram_quantile` vise le rang $r = \phi n$, prend le premier seau $i$ dont le décompte cumulé $c_i$ atteint ce rang, puis interpole linéairement dans ce seau, comme si ses observations y étaient réparties uniformément :

$$q = b_{i-1} + (b_i - b_{i-1})\,\frac{r - c_{i-1}}{c_i - c_{i-1}}$$

Ici $b_i$ est la borne supérieure du seau $i$, avec $b_0 = 0$ et $c_0 = 0$.

::: ex
[Exemple 5.2 — Ce que `histogram_quantile` répond sur six attentes réelles]{.tag} Six jobs ont attendu 1, 2, 5, 8, 12 et 17 s sur le bac à sable (capture réelle de `sacct`). Valeurs exactes : médiane 6,5 s, 90e centile 14,5 s par interpolation linéaire. Avec les seaux 10 et 30 s, Prometheus doit **interpoler à l'intérieur d'un seau** : `histogram_quantile` répond 7,5 s pour la médiane et 24 s pour le 90e centile, soit 65 % de trop. C'est ce qu'établit le test `tests/wait_quantile.test.yml` du lab 14.2, vérifié avec `promtool`.

Avec des seaux plus fins à 5, 10, 15, 20 et 30 s, la même interpolation donne 5,0 s et 17,0 s (calcul de la même formule, non rejoué dans `promtool`). La leçon : mettez des **bornes de seaux autour de vos seuils de SLO**. Le seuil de 600 s du lab est une borne, donc le rapport de jobs sous 600 s est exact quelle que soit l'interpolation.
:::

### 5.5. Kubernetes : mêmes questions, autres métriques

Sur Kubernetes, `kube-state-metrics` expose l'état des objets, par exemple `kube_pod_status_phase` (jauge) et `kube_pod_container_status_restarts_total` (compteur de redémarrages par conteneur, stable dans la documentation). Pour les files, Kueue publie `kueue_pending_workloads` (jauge par file et par statut, `active` ou `inadmissible`) et `kueue_admission_wait_time_seconds` (histogramme du temps entre la création d'une charge et son admission). Le délai d'attente est donc fourni nativement, contrairement à Slurm où il faut le reconstruire depuis `sacct`. Le module [12](../kubernetes-gpu/index.html) traite Kueue ; avec `dcgm-exporter -k`, les métriques GPU sont associées aux pods.

::: recap
Points clés — chapitre 5

-   Quatre questions : combien attendent et pourquoi, depuis quand, quels nœuds sont retirés, quelle capacité reste.
-   Lisez Slurm en JSON, mettez en cache, grattez à 30 ou 60 s : `squeue` charge `slurmctld`.
-   Regroupez les raisons d'attente par responsable (`capacity`, `user`, `admin`, `config`, `other`) pour borner les étiquettes et isoler ce qui pèse sur la plateforme.
-   Le délai d'attente est un histogramme dédoublonné ; placez des bornes de seaux autour de vos seuils.
-   Kueue fournit un histogramme d'admission natif ; Slurm demande de le reconstruire.
:::

## 6. SLO de plateforme et goodput {#ch6}

Un seuil sur une métrique ne dit pas si les utilisateurs sont bien servis. Un SLO le dit, et il permet de décider quand réveiller quelqu'un. Ce chapitre construit trois objectifs pour une plateforme GPU et des alertes qui s'en déduisent.

### 6.1. SLI, SLO et budget d'erreur

::: def
[SLI, SLO, budget d'erreur]{.tag} Un **SLI** (indicateur de niveau de service) est un rapport entre événements bons et événements totaux, par exemple la part des jobs démarrés en moins de 10 minutes. Un **SLO** fixe une cible pour cet indicateur sur une période, par exemple 95 % sur 30 jours. Le **budget d'erreur** est le complément : $1 - \text{SLO}$, soit 5 % des jobs qui ont le droit d'attendre davantage.
:::

Le budget d'erreur change la conversation : tant qu'il en reste, on peut prendre des risques (une maintenance, une mise à jour de pilote) ; quand il est épuisé, on ralentit. Il transforme « le cluster est lent » en un nombre que l'on peut dépenser.

### 6.2. Trois SLI pour une plateforme GPU

1.  **Disponibilité de la capacité** : GPU-heures utilisables sur GPU-heures totales. Un nœud drainé ou en panne retire sa capacité. Source : l'état des nœuds (`slurm_nodes`, chapitre 5), pondéré par leur nombre de GPU, que Slurm déclare comme GRES (module 5) ; le lab 14.1 ne compte que les CPU (`slurm_cpus`). Décidez à l'avance si la maintenance planifiée compte comme une indisponibilité.
2.  **Délai d'attente** : part des jobs dont l'attente imputable à la plateforme (classe `capacity`, depuis l'éligibilité) est sous un seuil, par QOS. Un seuil de 10 minutes pour la QOS normale et de quelques secondes pour une QOS urgente sont des exemples ; ils découlent de vos engagements.
3.  **Goodput** : part du temps alloué qui produit des pas d'entraînement utiles (6.4).

Les cibles chiffrées (95 %, 99 %, 99,5 %) sont des **choix** de ce parcours pour les exemples, pas des normes.

### 6.3. Des alertes qui réveillent pour de bonnes raisons

Le Workbook SRE de Google compare les stratégies d'alerte selon quatre critères : la précision (part des alertes qui correspondent à une vraie menace), le rappel (part des vrais problèmes détectés), le délai de détection et le délai de réinitialisation. Un simple seuil sur le taux d'erreur échoue : avec un SLO de 99,9 %, un taux d'erreur de 0,1 % pendant 10 minutes déclenche l'alerte alors que seuls 0,02 % du budget mensuel ont été consommés.

La stratégie la plus fidèle est l'alerte à **vitesse de consommation** (*burn rate*) sur **fenêtres multiples** : la vitesse de consommation est le rapport entre le taux d'erreur observé et le taux d'erreur permis par le SLO ; 1 consomme exactement le budget sur la période.

L'alerte exige deux fenêtres à la fois, une longue et une courte, la courte valant 1/12 de la longue pour que l'alerte se réinitialise vite. Le Workbook recommande comme points de départ 2 % du budget en 1 h et 5 % en 6 h pour les pages, 10 % en 3 jours pour un ticket. La vitesse de consommation se déduit :

$$\text{vitesse} = \frac{\text{part du budget consommée} \times \text{période}}{\text{fenêtre}}$$

Pour 2 % en 1 h sur 30 jours (720 h) : $0{,}02 \times 720/1 = 14{,}4$. Pour 5 % en 6 h : $0{,}05 \times 720/6 = 6$. Pour 10 % en 3 jours (72 h) : $0{,}10 \times 720/72 = 1$.

::: ex
[Exemple 6.1 — Les trois alertes du SLO d'attente, générées et testées]{.tag} Le lab 14.2 génère les règles du SLO « 95 % des jobs démarrent en moins de 600 s » à partir d'un seul modèle (`gen_rules.py`). Table imprimée par `python3 gen_rules.py --table` :

~~~text
alert                 burn  long  short  error ratio >  budget/long window    time to fire at 100 % errors
JobWaitSLOFastBurn    14.4    1h     5m           0.72               2.0%                      43.2 min
JobWaitSLOSlowBurn     6.0    6h    30m            0.3               5.0%                     108.0 min
JobWaitSLOTicket       1.0    3d     6h           0.05              10.0%                     216.0 min
~~~

Le seuil est $\text{vitesse} \times (1 - 0{,}95)$ : $14{,}4 \times 0{,}05 = 0{,}72$. Quatre scénarios sont **simulés** (compteurs synthétiques, deux minutes d'évaluation calculées par le modèle) et passés à `promtool test rules` :

-   panne totale de 2 h : la page rapide se déclenche à la 44e minute ($44/60 = 0{,}733 > 0{,}72$ ; à la 43e, $0{,}717$ ne suffit pas), puis se réinitialise 2 minutes après la fin de la panne grâce à la fenêtre de 5 min ;
-   incident de 10 minutes : aucune des trois alertes, à aucun moment ;
-   40 % d'erreurs pendant 8 h : la page lente se déclenche à la 270e minute, la rapide jamais ;
-   20 % d'erreurs pendant 30 h : seul le ticket se déclenche, après 18 h ($0{,}2 \times 18/72 = 0{,}05$).

**Limite de ce SLI.** L'histogramme ne compte un job qu'une fois démarré. Dans une vraie panne où plus rien ne démarre, aucune observation n'arrive, le rapport d'erreurs est indéfini et aucune de ces trois alertes ne se déclenche. Les scénarios supposent des jobs qui démarrent tard, pas des jobs qui ne démarrent pas : il faut en plus une alerte sur l'âge du plus ancien job en attente (`slurm_pending_oldest_age_seconds`, voir « Pour aller plus loin » du lab 14.2).

Le lab mesure aussi l'attente totale depuis `Submit`, sans tri par classe de raison : l'attente « imputable à la plateforme » du 6.2 est la cible, pas ce que le lab calcule.

Les alertes n'ont volontairement **pas** de `for` : le Workbook déconseille les durées dans les alertes de SLO, car une série qui oscille autour du seuil remet le minuteur à zéro et n'alerte jamais. Les deux fenêtres jouent ce rôle de filtre.
:::

::: note
[Alertmanager : grouper plutôt que multiplier]{.tag} Quand un rack perd son refroidissement, des dizaines d'alertes `GPUHot` partent en même temps (lab 14.2 : plus de 85 °C pendant 5 minutes, seuil illustratif). Alertmanager déduplique, groupe et route les alertes, et gère les silences et les inhibitions. Groupez par nom d'alerte et par une étiquette de domaine de panne (rack, commutateur). Sa documentation précise que si une alerte est résolue avant la fin de `group_wait`, aucune notification n'est envoyée pour elle, ce qui réduit le bruit des alertes instables. Cette configuration n'est pas exécutée dans le bac à sable.

La règle `GPUHot` porte aussi `keep_firing_for: 10m`. Selon la documentation de Prometheus, l'alerte reste alors active 10 minutes après la dernière évaluation où sa condition tenait, contre les alertes qui oscillent et les fausses résolutions. Le test du lab le vérifie : le GPU refroidit à la 20e minute, l'alerte est encore active à la 25e et résolue à la 32e.
:::

### 6.4. Le goodput

::: def
[Goodput et ETTR]{.tag} Le rapport technique de Llama 3 définit le temps d'entraînement effectif comme le temps passé en entraînement utile sur le temps écoulé, et rapporte plus de 90 % tout en acceptant des maintenances automatisées. Kokolis et al. (2024) définissent l'*Effective Training Time Ratio* (ETTR) comme le rapport entre le temps d'exécution productif et le temps réel disponible d'une exécution, et le goodput comme la quantité de travail productif accompli par unité de temps, à l'échelle d'une grappe. Dans ce module, « goodput » désigne par commodité le rapport par job (proche de l'ETTR).
:::

Pour piloter une plateforme, il faut décomposer ce rapport en pertes que l'on sait nommer. Pour un job qui s'arrête en moyenne toutes les $M$ secondes, qui écrit un checkpoint toutes les $\tau$ secondes pour un coût $\delta$, et dont chaque panne coûte une détection $d$, un redémarrage $R$ et la moitié d'un intervalle de travail refait :

$$G = 1 - \frac{\delta}{\tau} - \frac{d + R + \tau/2}{M}$$

::: ex
[Exemple 6.2 — Un job de sept jours, 256 GPU]{.tag} Paramètres **supposés** pour l'exemple : $M = 12$ h, $\tau = 30$ min, $\delta = 60$ s, $R = 10$ min, 30 % des pannes sont des blocages détectés après $d$ secondes, les autres des plantages vus en 30 s. Avec une détection des blocages par le seul délai NCCL ($d = 600$ s, documenté) :

Le coût des checkpoints est $\delta/\tau = 3{,}33\ \%$. La perte moyenne par panne est :

$$0{,}3 \times (600 + 600 + 900) + 0{,}7 \times (30 + 600 + 900) = 1\,701\ \text{s}$$

soit $1701/43\,200 = 3{,}94\ \%$. Goodput : **92,73 %**.

Avec un détecteur à phase déclarée à 246 s (lab 14.3, valeur **simulée**), la perte tombe à $1\,595$ s par panne, soit 3,69 % : goodput **92,97 %**. Gain : 0,246 point, soit 105,7 GPU-heures par semaine pour 256 GPU. Ce n'est pas énorme : la détection rapide n'est qu'un des leviers, et les 7,3 % de pertes se répartissent comme la figure ci-dessous. La seule valeur sûre est la méthode : décomposez avant d'optimiser.

<figure class="fig">
<svg viewBox="0 0 640 170" role="img" aria-labelledby="f3-t f3-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="f3-t">Où passe le temps d'un job de sept jours</title>
<desc id="f3-d">Barre de 100 pour cent : 92.7 pour cent de pas utiles, 3.3 pour cent de checkpoints, 0.5 pour cent de détection, 1.4 pour cent de redémarrage, 2.1 pour cent de travail refait.</desc>
<rect x="20.0" y="30" width="556.4" height="44" fill="var(--accent)" fill-opacity="0.9" stroke="currentColor" stroke-width="1.2"/>
<rect x="576.4" y="30" width="20.0" height="44" fill="currentColor" fill-opacity="0.5" stroke="currentColor" stroke-width="1.2"/>
<rect x="596.4" y="30" width="2.8" height="44" fill="currentColor" fill-opacity="0.35" stroke="currentColor" stroke-width="1.2"/>
<rect x="599.2" y="30" width="8.3" height="44" fill="currentColor" fill-opacity="0.22" stroke="currentColor" stroke-width="1.2"/>
<rect x="607.5" y="30" width="12.5" height="44" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-width="1.2"/>
<text x="298.2" y="58" text-anchor="middle" font-size="14" font-weight="700" fill="currentColor">92.7 %</text>
<line x1="586.4" y1="74" x2="586.4" y2="84" stroke="currentColor" stroke-opacity=".6"/>
<text x="460.0" y="96" font-size="12" fill="currentColor">checkpoints : 3.33 %</text>
<line x1="597.8" y1="74" x2="597.8" y2="101" stroke="currentColor" stroke-opacity=".6"/>
<text x="460.0" y="113" font-size="12" fill="currentColor">détection : 0.47 %</text>
<line x1="603.3" y1="74" x2="603.3" y2="118" stroke="currentColor" stroke-opacity=".6"/>
<text x="460.0" y="130" font-size="12" fill="currentColor">redémarrage : 1.39 %</text>
<line x1="613.8" y1="74" x2="613.8" y2="135" stroke="currentColor" stroke-opacity=".6"/>
<text x="460.0" y="147" font-size="12" fill="currentColor">travail refait : 2.08 %</text>
<text x="20" y="20" font-size="12" fill="currentColor">100 % du temps alloué</text>
</svg>
<figcaption>Budget de temps d'un job hypothétique (paramètres de l'exemple 6.2, tous supposés sauf le calcul). Le goodput est le grand segment coloré, à gauche.</figcaption>
</figure>
L'intervalle de checkpoint voisin de l'optimum de Young et Daly, $\sqrt{2\delta M} = 2\,277$ s soit 38 minutes, donnerait un résultat très proche : voir le [projet 3](../../projects/resilient-trainer/index.html) et le [module 10](../fault-tolerance/index.html).
:::

::: recap
Points clés — chapitre 6

-   SLI : un rapport bon sur total ; SLO : une cible sur une période ; budget d'erreur : le complément, que l'on dépense.
-   Trois SLI de plateforme : disponibilité de capacité, délai d'attente imputable à la plateforme, goodput.
-   Alerte à vitesses de consommation multiples (14,4 ; 6 ; 1) sur deux fenêtres (rapport 1/12), sans `for`, testée sur des scénarios.
-   Goodput $= 1 - \delta/\tau - (d + R + \tau/2)/M$ : décomposez les pertes avant de les attaquer.
:::

## 7. Détecter les pannes silencieuses {#ch7}

Les pannes bruyantes se détectent toutes seules : un processus qui meurt, un nœud qui tombe. Les pannes **silencieuses** laissent les GPU réservés, facturés et apparemment occupés pendant que rien d'utile ne se passe. Ce chapitre apprend à les chiffrer, à les détecter et à mesurer le prix de la détection.

### 7.1. Une typologie

Le [module 10, chapitre 5](../fault-tolerance/index.html#ch5) a posé les symptômes (crash, blocage, lenteur, silence) et la pulsation placée dans la boucle ; ce chapitre les traduit en métriques, en alertes et en coût de détection.

| Panne | Signature visible | Piège |
|---|---|---|
| Blocage d'une collective | le compteur de pas stagne ; l'utilisation GPU peut rester haute | un seuil sur l'utilisation ne voit rien |
| Traînard (*straggler*) | un rang calcule plus lentement ; tout le job ralentit | le temps d'étape est identique pour tous les rangs |
| Erreur matérielle | code XID, erreur ECC, remappage de lignes mémoire | `XID_ERRORS` est le dernier code, pas un compteur |
| Dérive de débit | tokens/s en baisse de quelques pour cent | invisible sous un seuil fixe, masquée par le bruit |
| Corruption silencieuse | résultat faux sans erreur | indétectable par les métriques d'état |

::: war
[Ce que la production rapporte]{.tag} Sur une période de 54 jours de pré-entraînement de Llama 3 405B, Meta a recensé 466 interruptions de job, dont 47 planifiées et 419 imprévues ; environ 78 % des interruptions imprévues sont attribuées à des problèmes matériels confirmés ou suspectés (pannes de GPU ou de composants, corruption silencieuse de données…), les GPU représentant 268 des 419 interruptions imprévues (64 % recalculé à partir des comptes du tableau 5 ; le texte de l'article dit 58,7 %, voir le [module 10, § 1.3](../fault-tolerance/index.html#ch1)).

Le rapport décrit aussi les traînards : « Sometimes, hardware issues may cause still-functioning but slow stragglers that are hard to detect. Even a single straggler can slow down thousands of other GPUs, often appearing as functioning but slow communications. » Source : [Dubey et al., *The Llama 3 Herd of Models*, section 3.3.4](https://arxiv.org/abs/2407.21783).
:::

### 7.2. Les blocages : progrès, pas activité

La seule preuve qu'un entraînement avance est que son compteur de pas augmente. L'utilisation GPU, la puissance et l'activité tensorielle sont des indices ; le pas est la preuve. Deux détecteurs sont à distinguer :

-   la **vivacité** (*heartbeat*, signal de vie émis par un fil séparé) : le processus répond encore. Elle détecte un plantage, pas un blocage, car le fil d'exécution qui émet le signal continue de tourner pendant qu'une collective est bloquée ;
-   le **progrès** : un compteur de pas, avec une fenêtre de stagnation ; c'est la « pulsation » du [module 10, § 5.3](../fault-tolerance/index.html#les-pulsations), émise dans la boucle principale.

Le progrès a un défaut : l'entraînement s'arrête légitimement. Un checkpoint, une évaluation, un blocage de données mettent le compteur à l'arrêt. Une fenêtre plus courte que la plus longue pause légitime déclenche de fausses alarmes ; plus longue, elle retarde la détection. Toute la difficulté est de choisir cette fenêtre en connaissance des pauses.

L'astuce du lab 14.3 est que l'entraîneur **déclare sa phase** (`train`, `ckpt`, `eval`) : chaque phase reçoit alors sa propre tolérance, et la fenêtre de stagnation ne s'applique qu'à la phase d'entraînement.

::: ex
[Exemple 7.1 — Fausses alarmes contre délai, sur séries simulées]{.tag} Le lab 14.3 simule 150 runs sains, 150 blocages et 100 plantages de 6 h. Les durées de pauses sont **supposées** (checkpoint de 30 à 90 s, avec 10 % de lents de 120 à 420 s ; évaluation de 120 à 300 s ; blocage de données de 20 à 200 s). Sortie de `python3 evaluate.py`, graines fixes :

~~~text
detector                             hangs found %  crashes found %  healthy runs alarmed %  delay median s
UtilLow 300 s                                    0              100                     0.0               -
TensorIdle 300 s                               100              100                    34.7             307
StepStall 300 s                                100                0                    36.0             306
StepStall 600 s                                100                0                     0.0             606
Heartbeat 60 s                                   0              100                     0.0               -
PhaseAware 240 s                               100                0                     0.0             246
PhaseAware 240 s + Heartbeat 60 s              100              100                     0.0             246
~~~

Quatre enseignements, **valables pour ces hypothèses**. Le détecteur sur l'utilisation est aveugle aux blocages, par construction du modèle de blocage (utilisation haute) ; il voit les plantages parce qu'un GPU sans processus tombe à zéro. Le battement de cœur voit les plantages et jamais les blocages.

Parmi les fenêtres testées (30 à 900 s), le compteur de pas seul n'est sans fausse alarme qu'à partir de 480 s ; à 600 s, c'est exactement le délai par défaut de NCCL.

La phase déclarée donne zéro fausse alarme dès 246 s : la détection est environ 2,5 fois plus rapide que les 606 s du compteur seul. Ce zéro découle des hypothèses : la plus longue pause de données simulée dure 200 s et le plus long checkpoint 420 s, tous deux sous les tolérances. Des pauses réelles plus longues feraient apparaître des fausses alarmes. Il faut **deux** alertes, progrès par phase et vivacité, car l'absence d'une série n'est pas une stagnation.
:::

<figure class="fig">
<svg viewBox="0 0 640 340" role="img" aria-labelledby="f2-t f2-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="f2-t">Fausses alarmes et délai de détection selon la fenêtre</title>
<desc id="f2-d">Deux courbes sur des séries simulées. Avec le seul compteur de pas, les fausses alarmes restent élevées jusqu'à une fenêtre de 240 secondes puis tombent à zéro à 480 secondes. Avec la phase déclarée par l'entraîneur, elles tombent à zéro dès 240 secondes. Une ligne verticale marque le délai du chien de garde NCCL par défaut, 600 secondes.</desc>
<line x1="64" y1="290.0" x2="620" y2="290.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="58" y="294.0" text-anchor="end" font-size="12" fill="currentColor">0</text>
<line x1="64" y1="245.0" x2="620" y2="245.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="58" y="249.0" text-anchor="end" font-size="12" fill="currentColor">3</text>
<line x1="64" y1="200.0" x2="620" y2="200.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="58" y="204.0" text-anchor="end" font-size="12" fill="currentColor">6</text>
<line x1="64" y1="155.0" x2="620" y2="155.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="58" y="159.0" text-anchor="end" font-size="12" fill="currentColor">9</text>
<line x1="64" y1="110.0" x2="620" y2="110.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="58" y="114.0" text-anchor="end" font-size="12" fill="currentColor">12</text>
<line x1="64" y1="65.0" x2="620" y2="65.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="58" y="69.0" text-anchor="end" font-size="12" fill="currentColor">15</text>
<line x1="64" y1="20.0" x2="620" y2="20.0" stroke="currentColor" stroke-opacity=".18"/>
<text x="58" y="24.0" text-anchor="end" font-size="12" fill="currentColor">18</text>
<line x1="64.0" y1="20" x2="64.0" y2="290" stroke="currentColor" stroke-opacity=".18"/>
<text x="64.0" y="306" text-anchor="middle" font-size="12" fill="currentColor">0</text>
<line x1="175.2" y1="20" x2="175.2" y2="290" stroke="currentColor" stroke-opacity=".18"/>
<text x="175.2" y="306" text-anchor="middle" font-size="12" fill="currentColor">200</text>
<line x1="286.4" y1="20" x2="286.4" y2="290" stroke="currentColor" stroke-opacity=".18"/>
<text x="286.4" y="306" text-anchor="middle" font-size="12" fill="currentColor">400</text>
<line x1="397.6" y1="20" x2="397.6" y2="290" stroke="currentColor" stroke-opacity=".18"/>
<text x="397.6" y="306" text-anchor="middle" font-size="12" fill="currentColor">600</text>
<line x1="508.8" y1="20" x2="508.8" y2="290" stroke="currentColor" stroke-opacity=".18"/>
<text x="508.8" y="306" text-anchor="middle" font-size="12" fill="currentColor">800</text>
<line x1="620.0" y1="20" x2="620.0" y2="290" stroke="currentColor" stroke-opacity=".18"/>
<text x="620.0" y="306" text-anchor="middle" font-size="12" fill="currentColor">1000</text>
<rect x="64" y="20" width="556" height="270" fill="none" stroke="currentColor" stroke-width="1.5"/>
<line x1="397.6" y1="20" x2="397.6" y2="290" stroke="var(--accent)" stroke-dasharray="5 4" stroke-width="1.5"/>
<text x="402.6" y="34" font-size="12" fill="currentColor">délai NCCL par défaut : 600 s</text>
<polyline points="84.0,40.0 100.6,40.0 134.0,41.7 200.7,81.7 334.2,290.0 567.7,290.0" fill="none" stroke="currentColor" stroke-width="3"/>
<circle cx="84.0" cy="40.0" r="4.5" fill="currentColor"/>
<circle cx="100.6" cy="40.0" r="4.5" fill="currentColor"/>
<circle cx="134.0" cy="41.7" r="4.5" fill="currentColor"/>
<circle cx="200.7" cy="81.7" r="4.5" fill="currentColor"/>
<circle cx="334.2" cy="290.0" r="4.5" fill="currentColor"/>
<circle cx="567.7" cy="290.0" r="4.5" fill="currentColor"/>
<polyline points="84.0,211.7 100.6,228.3 134.0,256.7 200.7,290.0 334.2,290.0 567.7,290.0" fill="none" stroke="var(--accent)" stroke-width="3"/>
<circle cx="84.0" cy="211.7" r="4.5" fill="var(--accent)"/>
<circle cx="100.6" cy="228.3" r="4.5" fill="var(--accent)"/>
<circle cx="134.0" cy="256.7" r="4.5" fill="var(--accent)"/>
<circle cx="200.7" cy="290.0" r="4.5" fill="var(--accent)"/>
<circle cx="334.2" cy="290.0" r="4.5" fill="var(--accent)"/>
<circle cx="567.7" cy="290.0" r="4.5" fill="var(--accent)"/>
<text x="203.0" y="62.0" font-size="12" fill="currentColor">compteur de pas seul</text>
<text x="136.3" y="206.0" font-size="12" fill="currentColor">avec la phase déclarée</text>
<text x="342.0" y="328" text-anchor="middle" font-size="13" fill="currentColor">délai médian de détection d'un blocage (s)</text>
<text x="14" y="155.0" text-anchor="middle" font-size="13" fill="currentColor" transform="rotate(-90 14 155.0)">runs sains alertés pour 100 h</text>
</svg>
<figcaption>Sortie du lab 14.3 (séries simulées, hypothèses dans <code>sim.py</code>). Six fenêtres de 30 à 900 s pour chaque détecteur ; chaque point est une fenêtre.</figcaption>
</figure>
Zéro fausse alarme sur 900 heures de runs sains ne prouve pas que le taux soit nul : la règle des trois donne une borne supérieure d'environ $3/900 = 0{,}0033$ par heure à 95 %. Pour estimer un taux plus bas il faut plus d'heures, donc plus de runs : mesurez sur la production, pas seulement en simulation.

::: ex
[Exemple 7.2 — Ce que coûte le délai]{.tag} Un blocage détecté en 600 s plutôt qu'en 246 s sur un job de 512 GPU gaspille $(600 - 246)/3600 \times 512 = 50{,}3$ GPU-heures de plus par incident. À l'inverse, une fausse alarme qui tue un job de 256 GPU et lui fait perdre en moyenne un quart d'heure de travail coûte $0{,}25 \times 256 = 64$ GPU-heures. La bonne fenêtre minimise la somme des deux, pondérée par la fréquence des blocages réels : voir l'exercice 8.
:::

### 7.3. Les traînards : mesurer le calcul, pas l'étape

En entraînement synchrone, une étape se termine quand le dernier rang a fini : le temps d'étape complet est le même pour tous les rangs, et ne désigne donc pas le traînard. Ce qui le désigne est le **temps de calcul local** avant la collective, hors attente. C'est la raison d'être de `train_compute_seconds` dans le lab 14.2, et de l'alerte `NodeSlow` fondée sur le rapport à la médiane du job.

L'espérance du maximum de $p$ rangs de dispersion $\sigma$ croît comme $\sigma\sqrt{2\ln p}$ (chapitre 5 du [module 2](../perf-models/index.html)) : même sans panne, plus le job est grand, plus il est lent par rapport à la moyenne. Un traînard **persistant** est autre chose : il fixe le rythme.

::: ex
[Exemple 7.3 — Le coût d'un GPU lent dans un grand job]{.tag} Reprenons l'exemple 1.1 : un GPU à 60 % de sa fréquence ramène le débit à 65,2 % si 80 % de l'étape est du calcul. Dans un job de 1 024 GPU, détecté après 6 h, cela représente $1024 \times 6 \times (1 - 0{,}652) = 2\,137$ GPU-heures perdues par un seul composant. Détecter par comparaison à la médiane (`NodeSlow`, 10 minutes) ramène cette perte à environ 60 GPU-heures plus le temps de la décision. Le calcul suppose la fraction de calcul de 80 %, à mesurer sur votre modèle.
:::

### 7.4. Les dérives de débit

Un entraînement dont le débit baisse de 3 % ne dépasse jamais un seuil fixe à −10 %. Une somme cumulée (CUSUM) accumule les écarts à la cible : $s_i = \max(0,\ s_{i-1} + (\mu - x_i) - k)$ ; on alarme quand $s_i > h$, avec $k = 0{,}5\sigma$ et $h$ un multiple de $\sigma$. La cible et $\sigma$ viennent d'une fenêtre d'échauffement.

::: ex
[Exemple 7.4 — CUSUM contre seuil fixe, sur séries simulées]{.tag} Série de 400 échantillons à 1 % de bruit, baisse de 3 % à l'échantillon 200, 1 000 séries saines et 1 000 séries qui dérivent. Sortie de `python3 drift.py` :

~~~text
 h (sigma)  false-alarm series  drops found  delay median  delay p95
         8                  73          973           2.0          4
        12                   9          997           4.0          6
        15                   3          998           5.0          7
fixed threshold at -10 % finds 0 of 1000 drifting series
~~~

Le seuil fixe ne trouve aucune des 1 000 dérives ; le CUSUM en trouve plus de 97 % en 2 à 5 échantillons, soit environ une minute à 15 s par échantillon. Le prix est le taux de fausses alarmes : 0,9 % des séries saines avec $h = 12\sigma$, 7,3 % avec $h = 8\sigma$. **Réglez-le sur votre bruit réel.**
:::

Une précaution : le rapport de Llama 3 note une variation diurne de 1 à 2 % du débit, attribuée à des températures plus élevées à midi qui jouent sur la fréquence dynamique des GPU. Un CUSUM naïf la prend pour une dérive : comparez à la médiane de la flotte au même instant, ou à la même heure la veille.

### 7.5. Tests de santé continus

Les métriques disent l'état passé ; un test de santé **provoque** l'erreur avant le job. DCGM fournit quatre niveaux de diagnostic (`dcgmi diag -r 1` à `-r 4`, chacun incluant les précédents ; la page *Feature Overview* n'en décrit que trois). Sur des systèmes Hopper, la documentation de *DCGM Diagnostics* annonce moins de 2,5 s pour le niveau 1, moins de 2,5 min sur 4 GPU et 10,5 min sur 8 GPU pour le niveau 2, et, sur 8 GPU, moins de 35 min pour le niveau 3 et 2,25 h pour le niveau 4 ([module 6, chapitre 6](../provisioning/index.html#ch6)).

Elle destine le niveau 1 à la vérification avant un job, le niveau 2 à l'épilogue après une panne, les niveaux 3 et 4 à l'analyse par un administrateur. Le niveau 1 tient donc dans un prologue Slurm ; le niveau 2, dans un épilogue déclenché après un échec ([module 5](../slurm/index.html)).

::: war
[Des vérifications de santé périodiques, calibrées]{.tag} Kokolis et al. (2024) décrivent, sur deux grappes de recherche à A100, des vérifications de santé exécutées toutes les cinq minutes sur chaque nœud, avec des codes de retour succès, échec ou avertissement, allant des erreurs XID aux points de montage manquants. Ils les calibrent de sorte que moins de 1 % des jobs terminés avec succès aient vu une vérification échouer, et un nœud qui échoue passe en remédiation et n'est plus ordonnancé. Source : [arXiv:2410.21680](https://arxiv.org/abs/2410.21680), section sur les vérifications de santé.
:::

La conception recommandée est stratifiée : des vérifications **bon marché et fréquentes** (XID, ECC, fréquences, erreurs PCIe et NVLink) toutes les quelques minutes ; un diagnostic de niveau 1 au prologue de chaque job et de niveau 2 à l'épilogue d'un job en échec ; un diagnostic long (niveau 3 ou 4) à la mise en service et après une réparation. Un nœud qui échoue est drainé avec une raison au préfixe convenu (`health:`, module 5) ; seules les raisons que le contrôle sait clore sans ambiguïté sont remises en service automatiquement.

### 7.6. Les compteurs du réseau {#les-compteurs-du-réseau}

Le rapport de Llama 3 cité au § 7.1 note que les traînards apparaissent souvent comme des communications lentes : le réseau a lui aussi ses pannes silencieuses. Le collecteur `infiniband` de `node_exporter`, actif par défaut sous Linux, lit les compteurs des ports dans `/sys/class/infiniband` et les expose avec les étiquettes `device` et `port`.

Trois compteurs servent d'abord, d'après les descriptions du code source du collecteur : `node_infiniband_symbol_error_total` (erreurs mineures sur une voie physique), `node_infiniband_link_downed_total` (lien tombé faute d'avoir récupéré d'une erreur) et `node_infiniband_port_transmit_wait_total` (ticks où le port avait des données à émettre sans rien envoyer).

Ce sont des compteurs : `increase(node_infiniband_link_downed_total[10m]) > 0` signale un lien retombé dans les dix dernières minutes. Ce module ne fixe pas de seuil pour les erreurs de symbole ou l'attente d'émission ; leur sens et leur lecture (`perfquery`, `rdma statistic`) sont au [module 7, chapitre 8](../networking/index.html#ch8). **Non vérifié** : le bac à sable n'a pas de carte InfiniBand.

::: recap
Points clés — chapitre 7

-   Les pannes silencieuses sont celles qui laissent les GPU réservés sans travail utile ; en production, la majorité des interruptions imprévues rapportées pour Llama 3 sont matérielles ou suspectées de l'être.
-   Le progrès (compteur de pas) prouve l'avancement ; la vivacité détecte les plantages ; il faut les deux, avec des phases déclarées pour les pauses légitimes.
-   La fenêtre de stagnation arbitre fausses alarmes et délai : mesurez vos pauses et placez-la au-dessus de leur queue.
-   Un traînard se mesure par le temps de calcul local, rapporté à la médiane du job.
-   Les dérives de quelques pour cent demandent un CUSUM réglé sur votre bruit ; les vérifications de santé se calibrent sur le taux de fausses alarmes.
-   DCGM a quatre niveaux de diagnostic : le 1 au prologue, le 2 à l'épilogue d'un échec, les 3 et 4 pour l'enquête.
-   Le réseau se surveille par l'`increase` de ses compteurs de ports (collecteur `infiniband` de `node_exporter`) ; leur sens est au module 7.
:::

## 8. Suivi d'expériences et reproductibilité {#ch8}

Une régression de courbe est un problème d'observabilité comme un autre, à condition que les métriques du système et celles du modèle se trouvent au même endroit et portent les mêmes clés. Ce chapitre montre comment, avec MLflow, et ce qu'il faut enregistrer pour pouvoir refaire un run.

### 8.1. Ce qu'un run doit enregistrer

Pour qu'un run soit refaisable, il faut pouvoir reconstruire six choses. Un enregistrement qui en manque une est une anecdote.

| Élément | Exemple | Où le mettre |
|---|---|---|
| Code | commit, branche, état « modifié » | étiquettes (MLflow définit `mlflow.source.git.commit`, `.branch`, `.dirty`) |
| Configuration | taux d'apprentissage, taille de lot globale | paramètres |
| Données | version du jeu, empreinte | étiquette ou paramètre |
| Environnement | empreinte de l'image de conteneur, versions de bibliothèques | étiquettes |
| Aléa | graines | paramètres |
| Matériel et placement | identifiant du job Slurm, liste des nœuds, modèle de GPU | étiquettes |

Weights & Biases range la configuration dans la propriété `config` du run et la perte et les mesures de sortie dans le journal `log` ; MLflow sépare de la même façon les paramètres (`log_param`) et les métriques avec un pas (`log_metrics(..., step=)`). L'idée est la même.

### 8.2. MLflow, en pratique

Le suivi de MLflow enregistre pour chaque run des paramètres, des métriques à pas et des étiquettes, dans un magasin de métadonnées (fichiers locaux ou base de données SQL). Ses métriques système (processeur, mémoire, GPU) s'activent par la variable `MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING` ; les métriques GPU demandent `nvidia-ml-py`, ce que le bac à sable ne peut pas exercer.

::: note
[Le magasin de fichiers est abandonné]{.tag} Avec MLflow 3.17.2 installé le 24 octobre 2026 (`mlflow-skinny`), pointer le suivi sur un dossier local échoue avec : « The filesystem tracking backend (e.g., './mlruns') is in maintenance mode and will not receive further updates. Please migrate to a database backend (e.g., 'sqlite:///mlflow.db') ». Il faut soit une base (le lab utilise SQLite, avec `sqlalchemy` et `alembic`), soit la variable `MLFLOW_ALLOW_FILE_STORE=true`. Les tutoriels qui utilisent encore `mlruns` sont donc périmés ; lisez la documentation de votre version.
:::

### 8.3. Système ou modèle ?

Devant un run qui se dégrade, la première question est de savoir à quel étage chercher. Une règle simple, avec un run de référence de même configuration :

1.  le débit (tokens par seconde) change, la perte **à pas égal** ne change pas : le système est en cause (GPU lent, réseau, stockage) ;
2.  la perte à pas égal change, le débit non : le modèle ou les données (taux d'apprentissage, jeu de données) ;
3.  les deux changent : cause mixte, par exemple un redémarrage qui a changé de nœuds et de données ; il faut enquêter.

Il faut pour cela tracer la perte **en fonction du pas** (pas du temps) et enregistrer à chaque pas le minimum de fréquence SM, ce que le lab 14.3 fait.

::: ex
[Exemple 8.1 — Deux régressions, deux verdicts]{.tag} Partie C du lab 14.3 : trois runs **simulés** de 1 200 pas enregistrés par l'API de MLflow 3.17.2 (SQLite), l'un de référence, l'un où la fréquence du GPU le plus lent tombe à 65 % au pas 600 (`thermal`), l'autre où le taux d'apprentissage devient trois fois trop grand au pas 600 (`lrbug`). La physique est supposée (80 % de calcul). Sortie réelle :

~~~text
thermal  tokens/s -30.1%  loss gap at equal step -0.003  slowest clock -35.0%  CUSUM alarm at step 600  -10 % threshold alarm at step 600
         verdict: SYSTEM (throughput moved, loss per step did not; slowest SM clock moved too)
lrbug    tokens/s +0.0%  loss gap at equal step +2.413  slowest clock +0.0%  CUSUM alarm at step None  -10 % threshold alarm at step None
         verdict: MODEL or DATA (loss per step moved, throughput did not)
~~~

Le premier run perd 30,1 % de débit sans changer de courbe de perte à pas égal : la fréquence minimale a baissé de 35 %, la cause est le GPU. Le second garde son débit et sa fréquence, mais sa perte à pas égal s'écarte de la référence : aucune alerte de débit ne l'aurait vu, et c'est la courbe de perte qui l'accuse. Une plateforme qui ne surveille que le débit rate le second cas ; une équipe qui ne regarde que la perte confond le premier avec un problème de modèle.
:::

### 8.4. Reproductibilité : viser la bonne cible

La reproductibilité bit à bit d'un entraînement distribué est rarement atteignable en pratique : l'ordre des réductions et les noyaux non déterministes y mettent obstacle. L'objectif réaliste est la **reproductibilité statistique** : mêmes code, configuration, données et graines doivent donner des courbes qui restent dans le bruit d'un run de référence. C'est précisément ce que le test de l'exemple 8.1 vérifie (écart de perte à pas égal inférieur à 0,05). Enregistrez donc toujours un run de référence pour chaque configuration que vous comptez comparer.

::: recap
Points clés — chapitre 8

-   Un run refaisable enregistre code, configuration, données, environnement, graines et placement.
-   MLflow : paramètres, métriques à pas, étiquettes ; le magasin de fichiers est en mode maintenance en 3.17.2, utilisez une base.
-   Débit qui change et perte à pas égal inchangée : le système ; l'inverse : le modèle ou les données.
-   Visez la reproductibilité statistique, avec un run de référence par configuration.
:::

## Labs {#labs}

Les trois labs s'exécutent sans GPU dans une VM Linux (testés sur 4 vCPU, 16 Go). Prérequis communs : `promtool` (`sudo apt-get install prometheus`, version 2.45.3 testée) et un Python avec `prometheus_client`, `pytest`, `pyyaml`, `torch` (version CPU) ; la partie C du lab 14.3 demande aussi `mlflow-skinny`, `sqlalchemy` et `alembic`, et sa partie D `opentelemetry-sdk` (1.45.1 testée).

Chaque `verify.sh` respecte `${PYTHON:-python3}` et n'affirme rien sur une durée mesurée : la machine peut être partagée. Les labs ont été testés avec `promtool` 2.45.3 (Ubuntu 24.04), alors que la documentation citée est celle de la branche 3.x, dont la page *latest* contient le [guide de migration vers Prometheus 3.0](https://prometheus.io/docs/prometheus/latest/migration/) : vérifiez vos règles avec le `promtool` de la version de votre serveur.

### Lab 14.1 — Un exportateur de métriques de nœud testé {#lab-14-1}

::: lab

**Objectif.** Écrire et tester avec `prometheus_client` un exportateur qui publie un résumé de nœud GPU, l'état d'une file Slurm avec des étiquettes bornées et un histogramme de délai d'attente. **Durée.** 3 h. **Prérequis matériels.** Un portable CPU ; aucun GPU. La branche en direct demande le Slurm du module 5.

**Ce qui est simulé, ce qui est réel.** Le texte DCGM (`fixtures/dcgm_node.prom`) est **simulé** : noms et formats de dcgm-exporter, valeurs inventées, trois pannes plantées. Les fichiers `fixtures/slurm/*` sont des **captures réelles** de Slurm 23.11.4, réduites aux champs lus.

1.  Lisez `labs/observability/gpu-metrics-exporter/exporter.py` : repérez les trois collecteurs, `reason_class`, et le fait qu'une source en échec ne produit **aucune** valeur et `*_scrape_success 0`.
2.  Lancez `python3 exporter.py --fixtures fixtures --once` et retrouvez les trois pannes plantées dans les métriques `gpu_node_*`.
3.  Lancez `bash verify.sh` : 14 tests, 6 mutants à tuer, `promtool check metrics`, un scrape HTTP réel.
4.  Ajoutez un septième mutant à `mutants.py` (par exemple, classer en `other` les raisons de drainage préfixées par `health:`) et vérifiez qu'il est tué ; sinon, écrivez le test qui manque.
5.  Avec le Slurm du module 5 démarré (`labs/slurm/slurm-sandbox/setup.sh`), lancez `LIVE_SLURM=1 bash verify.sh` pour la branche en direct, puis `teardown.sh`.

**Critère de réussite.** `bash verify.sh` affiche `OK mutants: 6/6 killed` puis `OK gpu-metrics-exporter` (sortie de l'auteur : `14 passed`, `slurm_job_wait_seconds_count{qos="normal"} 6.0`). La branche en direct a été exécutée une fois par l'auteur : `slurm_scrape_success 1.0` et `slurm_nodes{partition="debug",state="mixed"} 1.0`. **Non vérifié** : la lecture d'un vrai dcgm-exporter sur GPU.

**Pour aller plus loin.** Calculez le nombre de séries pour 500 nœuds de 8 GPU avec et sans le résumé de nœud. Remplacez la fixture par un `GET` sur un dcgm-exporter réel si vous avez un GPU.
:::

### Lab 14.2 — Règles d'alerte testées avec promtool {#lab-14-2}

::: lab

**Objectif.** Écrire des règles d'alerte et d'enregistrement, générer les alertes de SLO à partir d'un modèle, les tester avec `promtool test rules`, et prouver que les tests protègent les règles par mutation. **Durée.** 3.5 h. **Prérequis matériels.** Un portable CPU ; `promtool`.

**Ce qui est simulé.** Toutes les séries des tests sont synthétiques ; les seuils sont illustratifs.

1.  Lisez `labs/observability/alert-rules/rules/platform.rules.yml` et `runbooks/` : chaque alerte a une sévérité, un résumé et un runbook.
2.  Lancez `python3 gen_rules.py --table` puis `python3 gen_rules.py --check` : les règles et les tests de SLO sont générés par un même modèle.
3.  Lisez `tests/platform.rules.test.yml` : pour chaque alerte, repérez le cas qui se déclenche et le cas silencieux, avec des instants d'évaluation de part et d'autre de `for`.
4.  Lancez `bash verify.sh` (environ une minute) : `promtool check rules`, lint de politique (il doit **rejeter** `tests/bad.rules.yml`), trois suites de tests et le corrigé de l'exercice 11 (`exercises/`), puis 12 mutants.
5.  Changez le SLO de 95 % à 99 % dans `gen_rules.py`, régénérez, et relisez la table : que deviennent les seuils et les minutes de déclenchement ?

**Critère de réussite.** `bash verify.sh` affiche `OK mutants: 12/12 killed` puis `OK alert-rules`. Si un mutant survit, c'est qu'un test manque : écrivez-le.

**Pour aller plus loin.** Écrivez `JobStuckPending` sur `slurm_pending_oldest_age_seconds{reason_class="capacity"}` et testez-la avec ses mutants ; ajoutez au lint une vérification que toute alerte `page` est atteignable depuis un SLO. Écrivez `IBLinkDowned` sur `increase(node_infiniband_link_downed_total[10m]) > 0` (§ 7.6) et testez-la sur des séries synthétiques.
:::

### Lab 14.3 — Détecteur de job bloqué {#lab-14-3}

::: lab

**Objectif.** Mesurer le compromis fausses alarmes et délai de plusieurs détecteurs de blocage sur séries simulées, observer un **vrai** blocage de collective sur CPU, séparer une régression du système d'une régression du modèle, puis tracer un pas avec OpenTelemetry. **Durée.** 3.5 h. **Prérequis matériels.** Un portable CPU avec `torch` ; 2 cœurs libres suffisent.

**Ce qui est simulé, ce qui est réel.** Partie A : séries **simulées**, pauses et signature de blocage **supposées** (`sim.py`). Partie B : processus, `gloo`, collective bloquée et piles **réels**, mais sur CPU et avec un blocage injecté ; ce n'est pas NCCL. Partie C : trois runs **simulés** enregistrés par l'API réelle de MLflow. Partie D : durées de phases **simulées**, spans réels du SDK OpenTelemetry écrits dans un fichier, sans collecteur.

1.  Partie A : lisez `sim.py` (les hypothèses en tête de fichier) puis `detectors.py`, et lancez `python3 evaluate.py`. Retrouvez le tableau de l'exemple 7.1.
2.  Modifiez une hypothèse (par exemple, des checkpoints jusqu'à 900 s) et relancez : quels détecteurs cassent ? Quelle fenêtre faut-il ?
3.  Partie B : lisez `real_hang.py`, puis lancez `python3 real_hang.py`. Identifiez le rang fautif de deux façons : la pile et les journaux.
4.  Partie C : lancez `python3 regress.py` et relisez les deux verdicts de l'exemple 8.1.
5.  Partie D : lancez `python3 trace_steps.py` et retrouvez le pas lent et sa phase (§ 4.3).
6.  Lancez `bash verify.sh` (environ 30 secondes de calcul).

**Critère de réussite.** `bash verify.sh` affiche `OK real-hang: localized rank 1 at step 150`, `OK part C: both regressions classified correctly`, `OK part D: step 13 is slow because of data` puis `OK hang-detector`. Aucune assertion ne porte sur une durée mesurée : seule la présence de l'alarme et la désignation du rang comptent.

Sans MLflow ou sans le SDK OpenTelemetry, la partie concernée est sautée et `verify.sh` affiche `PARTIAL hang-detector` : le lab n'est alors validé qu'en partie (`STRICT=1 bash verify.sh` échoue dans ce cas).

**Pour aller plus loin.** Sur un nœud GPU, activez le flight recorder de PyTorch (`TORCH_NCCL_TRACE_BUFFER_SIZE`, `TORCH_NCCL_DUMP_ON_TIMEOUT`) sur un job de test dont vous bloquez un rang, et comparez son verdict à celui de la partie B. Mesurez l'utilisation GPU pendant ce blocage : c'est la validation que ce module n'a pas pu faire.
:::

## Exercices {#ex}

::: exo
[Exercice 1 · ★ — Un GPU lent dans un job de 128]{.tag} Un job occupe 128 GPU. Un seul tourne à 75 % de la fréquence nominale de 1 980 MHz, les autres à 1 980 MHz. On suppose que 70 % d'une étape est du calcul proportionnel à la fréquence et 30 % de la communication. Calculez la fréquence moyenne et sa baisse en pourcentage, la durée relative d'une étape, le débit relatif et le nombre de GPU équivalents perdus. Que surveilleriez-vous à la place de la moyenne ?
:::

::: sol
La fréquence moyenne est $(127 \times 1980 + 1485)/128 = 1\,976{,}1$ MHz, soit une baisse de **0,20 %**.

La durée relative d'une étape est :

$$0{,}3 + \frac{0{,}7}{0{,}75} = 1{,}233$$

Le débit relatif est $1/1{,}233 = 81{,}1\ \%$, donc $128 \times (1 - 0{,}811) = 24{,}2$ GPU équivalents sont perdus alors que la moyenne n'a bougé que de 0,2 %. On surveille le **minimum** de la fréquence, ou le rapport minimum sur médiane (0,75 ici), et on alerte sur lui avec une durée `for`. Calcul refait en Python.
:::

::: exo
[Exercice 2 · ★ — Trois GPU, trois verdicts]{.tag} Voici trois GPU d'un même nœud, extraits de la fixture **simulée** du lab 14.1. Classez chacun (sain, bloqué, en panne) et justifiez avec les valeurs. Une alerte « utilisation GPU inférieure à 5 % pendant 10 minutes » les aurait-elle tous trouvés ?

| GPU | `GPU_UTIL` | `TENSOR_ACTIVE` | `POWER_USAGE` (W) | `SM_CLOCK` (MHz) | `XID_ERRORS` |
|---|---|---|---|---|---|
| 2 | 97,0 | 0,542 | 636 | 1 968 | 0 |
| 5 | 99 | 0 | 255 | 1 976 | 0 |
| 6 | 0 | 0 | 70 | 345 | 79 |
:::

::: sol
**GPU 2 : sain.** Utilisation, activité tensorielle (0,54), puissance (636 W) et fréquence sont cohérentes avec un entraînement en cours.

**GPU 5 : bloqué (hypothèse du cours).** Utilisation de 99 % mais activité tensorielle nulle et puissance à 255 W, très en dessous de 636 W : des noyaux tournent sans faire de calcul matriciel, comme dans une attente de collective. C'est une signature **supposée**, à valider sur votre matériel.

**GPU 6 : en panne.** Code XID 79 (« GPU has fallen off the bus » dans le catalogue de NVIDIA), utilisation nulle, puissance et fréquence au repos.

L'alerte sur l'utilisation trouverait le GPU 6, déjà signalé par son XID, et **manquerait le GPU 5**, qui est le plus coûteux : il reste réservé et facturé.
:::

::: exo
[Exercice 3 · ★ — Dimensionner un Prometheus]{.tag} Une flotte de 256 GPU expose 12 métriques par GPU, grattées toutes les 15 s, et la rétention est de 30 jours. Combien de séries, d'échantillons par seconde, d'échantillons sur la période, et quel espace disque (à 1 et 2 octets par échantillon, ordre de grandeur de la documentation) ? Que se passe-t-il si l'on ajoute l'étiquette `job` à ces séries ?
:::

::: sol
Séries : $256 \times 12 = 3\,072$. Échantillons par seconde : $3072/15 = 204{,}8$. Sur 30 jours ($2\,592\,000$ s) : $5{,}31 \times 10^8$ échantillons. Disque : **0,53 à 1,06 Go**.

L'étiquette `job` ne change pas le nombre de séries **actives** mais fait créer de nouvelles séries à chaque nouveau job : si la flotte exécute des jobs courts, le nombre de séries distinctes sur 30 jours dépasse largement 3 072 (exemple 3.2 : six fois plus de séries créées par jour dans le cas traité). On joint donc le job à la requête avec une métrique d'association.
:::

::: exo
[Exercice 4 · ★★ — Qui bloque la collective ?]{.tag} Un job de 4 rangs ne progresse plus. Votre script (voir l'exemple 4.2) affiche ces lignes, **fictives**, avec la pile du rang suspect. (a) Quel rang est en cause et que faut-il vérifier ? (b) Que conclure si les quatre rangs avaient un dernier pas **entré** de 8 120 et un dernier pas **terminé** de 8 119 ?

~~~text
last collective entered:   {0: 8120, 1: 8120, 2: 8119, 3: 8120}
last collective completed: {0: 8119, 1: 8119, 2: 8119, 3: 8119}
rank 2 innermost frame: train.py:212 in next_batch   -> batch = next(data_iter)
~~~
:::

::: sol
(a) Les rangs 0, 1 et 3 sont entrés dans la collective du pas 8 120 et attendent. Le rang 2 n'a pas dépassé le pas 8 119 : il n'a pas rejoint la collective, il est **resté en arrière**.

Sa pile le place dans `next_batch`, c'est-à-dire dans la lecture des données, pas dans le calcul GPU ni dans le réseau. Il faut vérifier le chargeur de données de ce rang et le stockage qu'il lit : montage, débit, processus de chargement bloqués. Ce n'est pas la peine de drainer le nœud pour une panne GPU avant d'avoir regardé le stockage.

(b) Si tous les rangs sont entrés dans la collective du pas 8 120 et qu'aucun ne l'a terminée, aucun rang n'est en retard : **la collective elle-même est bloquée**, ce qui oriente vers le réseau ou le moteur de communication (état des liens, erreurs de la carte réseau, journal NCCL), pas vers un rang.
:::

::: exo
[Exercice 5 · ★★ — Choisir les seaux d'un histogramme]{.tag} Vingt jobs ont attendu (en secondes) : 3, 4, 6, 9, 15, 25, 40, 70, 90, 200, 350, 520, 580, 610, 900, 1 500, 2 400, 3 000, 3 300, 5 000 (valeurs **fictives**). Les seaux A sont 10, 60, 300, 600, 1 800, 3 600 et 7 200 s ; les seaux B sont 30, 120, 600, 1 800 et 7 200 s. Pour chaque jeu, calculez l'estimation que donnerait `histogram_quantile` pour la médiane et le 90e centile, et la part des jobs sous 600 s. Comparez aux valeurs exactes et concluez.
:::

::: sol
Valeurs exactes (interpolation linéaire) : médiane 275 s, 90e centile 3 030 s, part sous 600 s : 13 sur 20, soit **65 %**.

Avec les seaux A, les décomptes cumulés sont 4, 7, 10, 13, 16, 19, 20. La médiane est le rang 10 : elle tombe pile sur la borne de 300 s (estimation **300 s**, +9 %). Le 90e centile est au rang 18 : dans le seau (1 800 ; 3 600] qui contient 3 jobs de 16 à 19 ; $1\,800 + 1\,800 \times (18-16)/(19-16) = 3\,000$ s (**−1 %**).

Avec les seaux B, les décomptes sont 6, 9, 13, 16, 20. La médiane est au rang 10 dans (120 ; 600] : $120 + 480 \times (10-9)/(13-9) = 240$ s (−13 %). Le 90e centile est au rang 18 dans (1 800 ; 7 200] : $1\,800 + 5\,400 \times (18-16)/(20-16) = 4\,500$ s (**+49 %**).

Pour les deux jeux, la part sous 600 s est exacte (65 %), car 600 est une borne. Conclusion : placez des bornes sur vos seuils de SLO ; pour les centiles élevés, resserrez les seaux là où la queue de la distribution se trouve. Calculs refaits en Python avec la formule d'interpolation de Prometheus ; elle a été vérifiée par `promtool` sur les données de l'exemple 5.2.
:::

::: exo
[Exercice 6 · ★★ — Un SLO à 99 %]{.tag} Le SLO d'attente passe à « 99 % des jobs démarrent en moins de 600 s sur 30 jours ». (a) Quel budget d'erreur en minutes d'indisponibilité totale équivalente ? (b) Calculez les seuils de taux d'erreur et les délais de déclenchement à 100 % d'erreur des trois alertes (vitesses 14,4 ; 6 ; 1). (c) Une panne totale de 25 minutes : quelles alertes se déclenchent, et quelle part du budget consomme-t-elle ?
:::

::: sol
(a) $1\ \% \times 30 \times 24 \times 60 = 432$ minutes, soit 7,2 h.

(b) Seuil $=$ vitesse $\times\ 0{,}01$ : **0,144** pour la page rapide (fenêtres 1 h et 5 min), **0,06** pour la page lente (6 h et 30 min), **0,01** pour le ticket (3 j et 6 h). À 100 % d'erreur, la fenêtre longue atteint le seuil après seuil × durée de la fenêtre : $0{,}144 \times 60 = 8{,}64$ min, $0{,}06 \times 360 = 21{,}6$ min, $0{,}01 \times 4\,320 = 43{,}2$ min. Ces valeurs sont celles que donne `python3 gen_rules.py --table` avec `SLO_TARGET = 0.99`.

(c) La page rapide se déclenche à la 9e minute, la page lente à la 22e, pas le ticket (il en faudrait 43,2). La panne consomme $25/432 = 5{,}8\ \%$ du budget mensuel.
:::

::: exo
[Exercice 7 · ★★ — Le déluge de 3 h 10]{.tag} Chaque nuit à 3 h 10, l'alerte `JobNoProgress` (compteur de pas immobile sur une fenêtre de 10 minutes, `for: 2m`) page l'astreinte pour quatre jobs, puis se résout seule deux minutes plus tard. Un instantané du système de fichiers est lancé à 3 h 00 ; les checkpoints de ces jobs durent alors 14 minutes. Expliquez le déclenchement par un calcul, proposez deux corrections et leur prix.
:::

::: sol
Quand le pas s'arrête à l'instant $t_0$, la fenêtre de 10 minutes ne contient plus aucun pas à partir de $t_0 + 10$ min ; avec `for: 2m`, l'alerte se déclenche à $t_0 + 12$ min. Les checkpoints durent 14 minutes : l'alerte est active de $t_0 + 12$ à $t_0 + 14$ min, soit environ **deux minutes**, ce que montre le cas « faux positif connu » de `tests/platform.rules.test.yml` (`promtool test rules`, `SUCCESS` : silence à 21 min, alerte à 33 min pour une pause qui commence à 20 min).

**Correction 1 : élargir la fenêtre.** Avec 15 minutes, la même pause de 14 minutes ne déclenche plus rien (vérifié avec `promtool` sur une copie de la règle). Prix : tout vrai blocage est détecté 5 minutes plus tard, soit pour 512 GPU $5/60 \times 512 = 42{,}7$ GPU-heures de plus par incident.

**Correction 2 : déclarer la phase.** L'entraîneur publie `train_phase` ; la règle de stagnation ne s'applique qu'en phase d'entraînement, la phase de checkpoint a sa propre tolérance (lab 14.3). Prix : un contrat de plus avec l'équipe d'entraînement.

Et surtout, un checkpoint de 14 minutes est lui-même un problème (l'instantané qui le ralentit) : l'alerte vient de le révéler.
:::

::: exo
[Exercice 8 · ★★ — Quelle fenêtre choisir ?]{.tag} Vous gérez des jobs de 256 GPU. D'après le lab 14.3, le tableau suivant donne, sur séries simulées, les runs sains alertés pour 100 h de runs et le délai médian de détection. Une fausse alarme tue un job et lui fait perdre en moyenne 0,25 h de travail ; on suppose **2 blocages réels pour 100 h de runs** (hypothèse). Calculez le coût total en GPU-heures pour 100 h de runs et choisissez. À partir de quelle fréquence de blocages la fenêtre 120 s à phase déclarée battrait-elle celle de 240 s ?

| Détecteur | alertés pour 100 h | délai médian (s) |
|---|---|---|
| compteur seul, 120 s | 16,56 | 126 |
| phase déclarée, 120 s | 2,22 | 126 |
| phase déclarée, 240 s | 0,00 | 246 |
| compteur seul, 480 s | 0,00 | 486 |
| compteur seul, 900 s | 0,00 | 906 |
:::

::: sol
Coût $=$ alertés $\times\ 0{,}25 \times 256$ $+$ $2 \times$ délai$/3600 \times 256$.

| Détecteur | fausses alarmes (GPU-h) | blocages (GPU-h) | total |
|---|---|---|---|
| compteur seul, 120 s | 1 059,8 | 17,9 | 1 077,8 |
| phase déclarée, 120 s | 142,1 | 17,9 | 160,0 |
| phase déclarée, 240 s | 0,0 | 35,0 | **35,0** |
| compteur seul, 480 s | 0,0 | 69,1 | 69,1 |
| compteur seul, 900 s | 0,0 | 128,9 | 128,9 |

Le meilleur choix est la **phase déclarée à 240 s**.

Les fausses alarmes dominent tout : avec le compteur seul à 120 s, elles coûtent près de 60 fois plus que les blocages. Chaque blocage détecté coûte $126 \times 256/3600 = 8{,}96$ GPU-h à 120 s et $17{,}49$ GPU-h à 240 s. La fenêtre de 120 s ne gagnerait que si $142{,}1 + 8{,}96\,n < 17{,}49\,n$, soit $n > 16{,}7$ blocages pour 100 h de runs : un toutes les 6 h, ce qui n'est pas un régime de fonctionnement. Les taux de fausses alarmes sont ici une **borne basse** (une seule première alarme par run) et viennent d'hypothèses de pauses simulées : refaites le calcul avec vos mesures.
:::

::: exo
[Exercice 9 · ★★★ — La pile d'observabilité de 2 048 GPU]{.tag} Dimensionnez et décrivez la pile d'un cluster de 256 nœuds de 8 GPU : intervalles de collecte, nombre de séries et volume de disque pour 15 jours, jointure du job, alertes de page (six au plus), SLO. Hypothèses : 25 métriques par GPU, 1 000 séries par nœud pour les métriques du système (**à mesurer** chez vous). Comparez une collecte unique à 15 s et une collecte de 15 s pour les GPU et 60 s pour les nœuds.
:::

::: sol
**Séries.** GPU : $2048 \times 25 = 51\,200$. Nœuds : $256 \times 1000 = 256\,000$. Total : **307 200** (les métriques du nœud dominent).

**Disque, 15 jours.** Collecte unique à 15 s : $307\,200/15 = 20\,480$ échantillons par seconde, soit 26,5 à 53,1 Go. Collecte à deux rythmes (GPU 15 s, nœuds 60 s) : $51\,200/15 + 256\,000/60 = 7\,680$ échantillons par seconde, soit **10,0 à 19,9 Go**, 2,7 fois moins. La conclusion est que le coût se joue sur les métriques du nœud, pas sur celles des GPU.

**Jointure.** Pas d'étiquette `job` sur les 51 200 séries GPU : une série d'association `slurm_job_gpu_allocated` (modèle du projet 5), alimentée par un prolog Slurm ou l'option de correspondance de dcgm-exporter (format à relire).

**Alertes de page (six).** `JobNoProgress` à phase déclarée ; vitesses de consommation rapide et lente du SLO d'attente, comme au lab 14.2 ; vitesse rapide du SLO de capacité ; XID critique (79, 95) sur un GPU alloué ; télémétrie GPU absente sur plus de 5 % des nœuds. Tout le reste en ticket : `GPUHot`, `NodeSlow`, les tickets à 3 jours, et la vitesse lente du SLO de capacité, traitée en heures ouvrées pour tenir la limite de six pages.

**SLO.** Capacité utilisable 99,5 % (budget de 3,6 h sur 720 h) ; attente sous 10 min pour 95 % des jobs de QOS normale (hors classes `user` et `admin`) ; goodput suivi, sans engagement tant que vous ne l'avez pas mesuré.

**Tableaux.** Trois niveaux (flotte, job, nœud) générés par code. Pas de rétention au-delà de 15 jours sans stockage long terme, non traité ici.
:::

::: exo
[Exercice 10 · ★★★ — Une courbe qui casse au pas 6 000]{.tag} Un entraînement de 512 GPU, repris depuis un checkpoint au pas 5 990 après le remplacement d'un nœud, montre à partir du pas 6 000 : débit en baisse de 12 % ; perte à pas égal supérieure de 0,4 à celle d'un run de référence de même configuration ; fréquence SM minimale en baisse de 3 %. Appliquez la règle du chapitre 8, dites ce que la fréquence explique, et proposez une enquête en trois temps avec les preuves attendues.
:::

::: sol
**Classement.** Le débit **et** la perte à pas égal ont changé : cause **mixte** (règle 3 du chapitre 8). Il y a donc probablement deux causes indépendantes, qui coïncident parce que le redémarrage les a introduites ensemble.

**Ce que la fréquence explique.** Avec 80 % de calcul proportionnel à la fréquence (hypothèse à mesurer), une baisse de 3 % donne $1/(0{,}2 + 0{,}8/0{,}97) = 0{,}976$, soit **−2,4 %** de débit. Il reste environ 9,6 points non expliqués : la fréquence n'est pas la cause principale.

**Enquête.**

1.  *Débit* : comparer le placement avant et après le remplacement (le nouveau nœud est-il sur un autre commutateur ?), le temps de calcul local par rang (`train_compute_seconds`, lab 14.2) et le temps de communication. Preuve : un rang ou un groupe de rangs dont le calcul ou la communication diffère.
2.  *Perte* : un redémarrage correct restaure l'optimiseur, l'ordonnanceur de taux d'apprentissage, l'état de l'aléa et la position du chargeur de données. Relire dans MLflow le taux d'apprentissage enregistré avant et après le pas 5 990 et vérifier que les données ne sont pas rejouées. Preuve : une courbe de taux d'apprentissage continue, ou la cause trouvée.
3.  *Contre-épreuve* : relancer depuis le même checkpoint sur le placement d'origine. Si le débit revient, c'est le placement ; si la perte reste décalée, c'est la reprise.

Un enregistrement de run qui contient le job Slurm, la liste des nœuds et le commit permet de faire cette enquête en une heure, pas en une semaine.
:::

::: exo
[Exercice 11 · ★★ — Une alerte pour une flotte mixte]{.tag} Une flotte ajoute des nœuds AMD supervisés par l'AMD Device Metrics Exporter (§ 2.5). Réécrivez la règle du § 3.2 (activité tensorielle moyenne d'un job sous 0,05) pour qu'elle couvre les deux fournisseurs. Le job `j1` occupe un GPU NVIDIA dont l'activité tensorielle vaut 0 et le GPU 0 du nœud AMD `a01`, qui publie `gpu_prof_tensor_active_percent{hostname="a01", gpu_id="0"} 2`. Que donne la règle avec et sans conversion d'unité ? Quels GPU AMD la règle ne couvre-t-elle pas ?
:::

::: sol
Il faut ramener les deux fournisseurs aux mêmes noms, aux mêmes étiquettes et à la même unité avant la jointure. Deux règles d'enregistrement produisent une série commune, `gpu:tensor_active:ratio`. La première recopie `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`. La seconde divise `gpu_prof_tensor_active_percent` par 100, puis renomme `hostname` en `Hostname` et `gpu_id` en `gpu` par deux `label_replace`. Une étiquette `vendor` les distingue. L'alerte reste celle du § 3.2, appliquée à la série commune.

Pour `j1`, la moyenne vaut $(0 + 0{,}02)/2 = 0{,}01 < 0{,}05$ : l'alerte se déclenche après sa durée `for`. Sans la division par 100, le GPU AMD compterait pour 2, la moyenne vaudrait $(0 + 2)/2 = 1$ et le job bloqué passerait inaperçu.

La règle ne couvre pas les GPU Radeon, où la métrique n'est pas exportée : la série manque, et une série absente ne déclenche rien (§ 3.4). Il leur faut une autre alerte, sur `gpu_gfx_activity` par exemple. Corrigé vérifié par `promtool test rules` sur des séries synthétiques, avec et sans la division : `labs/observability/alert-rules/exercises/`, que lance le `verify.sh` du lab 14.2.
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux dire ce qu'une métrique GPU mesure et ce qu'elle ne mesure pas.** Preuve : un tableau commenté de six métriques DCGM avec leur définition citée et, pour chacune, un cas où elle induit en erreur.
-   **Je peux dimensionner un Prometheus et protéger sa cardinalité.** Preuve : les exercices 3 et 9 refaits pour votre flotte, avec la jointure du job décrite.
-   **Je peux écrire un exportateur testé.** Preuve : le lab 14.1 avec un mutant de votre invention tué par un test que vous avez écrit.
-   **Je peux écrire une alerte et prouver que ses tests la protègent.** Preuve : le lab 14.2 avec une alerte de plus et 13 mutants tués.
-   **Je peux définir un SLO et ses alertes à vitesse de consommation.** Preuve : la table de `gen_rules.py` pour un SLO de votre choix et l'exercice 6.
-   **Je peux détecter un blocage et chiffrer fausses alarmes et délai.** Preuve : le tableau du lab 14.3 recalculé avec les durées de pause de **votre** entraîneur.
-   **Je peux dire si une régression vient du système ou du modèle.** Preuve : la partie C du lab 14.3 refaite sur un cas à vous, et l'exercice 10.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Un job de 512 GPU affiche 100 % d'utilisation GPU mais n'avance plus. Que regardez-vous ?* Réponse-type : l'utilisation ne prouve rien, car elle indique la présence de noyaux ; je regarde le compteur de pas de l'entraîneur, l'activité tensorielle et la puissance, puis le dernier pas entré et terminé de chaque rang (ou le flight recorder) pour trouver le rang qui n'a pas rejoint la collective, et sa pile. Je vérifie les erreurs XID et le journal du noyau du nœud concerné.

    Le délai NCCL par défaut est de 10 minutes : mon détecteur doit agir plus tôt, avec une phase déclarée pour ne pas confondre un checkpoint avec un blocage.
2.  *Comment alertez-vous sur la file d'attente sans réveiller l'astreinte pour rien ?* Réponse-type : je définis un SLI d'attente imputable à la plateforme (raisons de capacité, depuis l'éligibilité), un SLO, et des alertes à vitesses de consommation multiples sur deux fenêtres, sans durée `for`, testées par scénarios avec `promtool`. Les attentes dues à l'utilisateur ou à l'administrateur ne comptent pas. Je groupe les alertes par domaine de panne.
3.  *Votre Prometheus manque de mémoire après l'arrivée d'une nouvelle équipe. Que faites-vous ?* Réponse-type : je soupçonne la cardinalité, typiquement une étiquette à valeurs non bornées (job, pod, utilisateur) ; je cherche la métrique qui compte le plus de séries, je retire ou joins l'étiquette à la requête avec une métrique d'association, et je pose une limite `sample_limit` sur le travail de scrape pour qu'un exportateur fautif échoue au lieu d'étouffer le serveur. Je mesure ensuite le nombre de séries actives avant et après.

## Lectures et références {#refs}

-   Dubey et al. [*The Llama 3 Herd of Models*](https://arxiv.org/abs/2407.21783), 2024, section 3.3.4 : 466 interruptions sur 54 jours (tableau 5 : lire les comptes), temps d'entraînement effectif supérieur à 90 %, traînards (chapitres 6 et 7).
-   Kokolis et al. [*Revisiting Reliability in Large-Scale Machine Learning Research Clusters*](https://arxiv.org/abs/2410.21680), 2024 : définition de l'ETTR, vérifications de santé toutes les cinq minutes (chapitres 6 et 7).
-   Jiang et al. [*MegaScale*](https://arxiv.org/abs/2402.15627), 2024 : battements de cœur, événements CUDA et diagnostic à plus de 10 000 GPU (chapitres 4 et 7).
-   Hu et al. [*Characterization of Large Language Model Development in the Datacenter*](https://arxiv.org/abs/2403.07648), 2024 : échantillonnage à 15 s de Prometheus, DCGM et IPMI, utilisation GPU polarisée (chapitre 3).
-   NVIDIA. [*DCGM — Feature Overview*](https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/feature-overview.html) et [*DCGM Diagnostics*](https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/dcgm-diagnostics.html) : métriques de profil (`SM_ACTIVE`, `PIPE_TENSOR_ACTIVE`), quatre niveaux de `dcgmi diag`, leurs durées et leurs usages (chapitres 2 et 7).
-   NVIDIA. [*DCGM Exporter*](https://docs.nvidia.com/datacenter/cloud-native/gpu-telemetry/latest/dcgm-exporter.html) et [`default-counters.csv`](https://raw.githubusercontent.com/NVIDIA/dcgm-exporter/main/etc/default-counters.csv) : port, intervalle, liste des métriques (chapitre 2). AMD, [*Device Metrics Exporter — List of Available Metrics*](https://instinct.docs.amd.com/projects/device-metrics-exporter/en/latest/configuration/metricslist.html) et [*Slurm integration*](https://instinct.docs.amd.com/projects/device-metrics-exporter/en/latest/integrations/slurm-integration.html) : l'équivalent chez AMD (§ 2.5).
-   NVIDIA. [*nvidia-smi*](https://docs.nvidia.com/deploy/nvidia-smi/index.html) et [*Xid Errors*](https://docs.nvidia.com/deploy/xid-errors/index.html) : définition de l'utilisation GPU, catalogue des codes XID (chapitre 2).
-   Prometheus. [*Storage*](https://prometheus.io/docs/prometheus/latest/storage/), [*Metric and label naming*](https://prometheus.io/docs/practices/naming/), [*Recording rules*](https://prometheus.io/docs/practices/rules/), [*When to use the Pushgateway*](https://prometheus.io/docs/practices/pushing/), [*Alerting rules*](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/), [*Unit testing for rules*](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/) et le [collecteur `infiniband`](https://raw.githubusercontent.com/prometheus/node_exporter/master/collector/infiniband_linux.go) de `node_exporter` : dimensionnement, cardinalité, nommage, `for`, `keep_firing_for`, format des tests, compteurs de ports (chapitres 3, 6 et 7, lab 14.2).
-   Beyer et al. [*The Site Reliability Workbook*, « Alerting on SLOs »](https://sre.google/workbook/alerting-on-slos/) : alertes à vitesses de consommation multiples (chapitre 6).
-   OpenTelemetry. [*Traces*](https://opentelemetry.io/docs/concepts/signals/traces/) : définition du span ; le SDK Python fournit `ConsoleSpanExporter` (chapitre 4, partie D du lab 14.3).
-   Grafana Labs. [*Loki — Labels*](https://grafana.com/docs/loki/latest/get-started/labels/) et [*bonnes pratiques*](https://grafana.com/docs/loki/latest/get-started/labels/bp-labels/) : étiquettes à faible cardinalité (chapitre 4).
-   PyTorch. [*Debugging with Flight Recorder*](https://docs.pytorch.org/tutorials/unstable/flight_recorder_tutorial.html) et [*torch.distributed*](https://docs.pytorch.org/docs/2.14/distributed.html) : variables d'environnement et délais par défaut (chapitre 4).
-   SchedMD. [*squeue*](https://slurm.schedmd.com/squeue.html) et [*sinfo*](https://slurm.schedmd.com/sinfo.html) : raisons d'attente, format JSON, avertissement sur la charge de `slurmctld` (chapitre 5).
-   Kueue. [*Metrics reference*](https://kueue.sigs.k8s.io/docs/reference/metrics/) et kube-state-metrics, [*Pod metrics*](https://raw.githubusercontent.com/kubernetes/kube-state-metrics/main/docs/metrics/workload/pod-metrics.md) : métriques de files et de pods (chapitre 5).
-   MLflow. [*Tracking*](https://mlflow.org/docs/latest/ml/tracking/) et [*System metrics*](https://mlflow.org/docs/latest/ml/tracking/system-metrics/) ; W&B, [*Configure experiments*](https://docs.coreweave.com/products/wandb/track/config) : suivi d'expériences (chapitre 8).

## Sources et portée {#sources}

### Documenté {#documente}

Les faits suivants ont été relus sur leurs sources le 24 octobre 2026. DCGM et dcgm-exporter : définition de l'utilisation GPU (`nvidia-smi`), des métriques de profil, quatre niveaux de diagnostic et leurs durées annoncées sur Hopper (page *DCGM Diagnostics*), port 9400, intervalle de collecte de 30 000 ms, option `-k`, liste de 25 métriques par défaut, existence de l'option `--hpc-job-mapping-dir` dans le code source, codes XID 79, 94 et 95. Prometheus : 1 à 2 octets par échantillon et la formule de capacité, rétention de 15 jours par défaut, blocs de deux heures, avertissement sur la cardinalité, nommage des règles d'enregistrement, usage de la Pushgateway, collecteur *textfile*, `keep_firing_for`, `sample_limit`, `group_wait`. Workbook SRE : vitesses de consommation, fenêtre courte au douzième, déconseil des durées, quatre critères. Llama 3 : 54 jours, 466, 47, 419, 78 %, 268 interruptions de GPU dans les comptes du tableau 5 (le texte dit 58,7 %), 90 %, variation diurne de 1 à 2 %. Kokolis et al. : définitions de l'ETTR et du goodput, contrôles toutes les cinq minutes, moins de 1 %. Acme : 15 s. MegaScale : battements de cœur et événements CUDA. PyTorch : délais de 10 et 30 minutes, variables du flight recorder. Loki, OpenTelemetry, Kueue, kube-state-metrics, MLflow (variable des métriques système, étiquettes `mlflow.source.git.*` lues dans le code source), W&B (`config`), README du `prometheus-slurm-exporter` de vpenso (JSON, Slurm 23.02 minimum). Les comportements **observés** viennent d'exécutions du 24 octobre 2026 : Slurm 23.11.4, `promtool` 2.45.3, MLflow 3.17.2, PyTorch 2.14 (CPU, `gloo`), `prometheus_client` 0.26.0 ; les sorties citées en proviennent. Lus le 25 octobre 2026 : AMD Device Metrics Exporter, documentation de la version 1.5.3 (port 5000, noms et étiquettes, unités, limites sur Radeon et en mode partitionné, étiquettes `job_id` et `job_user` de l'intégration Slurm) ; collecteur `infiniband` de `node_exporter` (actif par défaut, chemin `/sys/class/infiniband`, noms et descriptions des compteurs, lus dans le code source) ; page de migration vers Prometheus 3.0 ; définition du span d'OpenTelemetry ; `ConsoleSpanExporter` (arguments `out` et `formatter`), exécuté avec `opentelemetry-sdk` 1.45.1.

### Recommandé {#recommande}

Les cinq couches, le regroupement des raisons d'attente en classes, les trois SLI de plateforme et leurs cibles (95 %, 99 %, 99,5 %), les seuils d'alerte (85 °C, rapport 1,3 à la médiane, 10 minutes sans pas), le contrat de l'entraîneur (`train_steps_total`, `train_compute_seconds`, phase déclarée), la conception de santé en trois strates, les réglages du CUSUM ($k = 0{,}5\sigma$, $h = 12\sigma$) et la cible de reproductibilité statistique sont des choix de ce parcours, pas des règles des outils. Tous les chiffres de pauses, de fractions de calcul (80 %, 70 %), de fréquence de pannes (12 h, 2 blocages pour 100 h) et de tailles de journaux sont des **hypothèses d'exemple**.

### À vérifier {#a-verifier}

(1) La signature d'un blocage « utilisation haute, tensor nul, battement de cœur actif » n'a pas été mesurée sur GPU : le bac à sable n'a pas de GPU. (2) Le format des fichiers de l'option `--hpc-job-mapping-dir` n'a pas été relu. (3) Les étiquettes exactes de dcgm-exporter varient selon les versions (la présence de `modelName` n'a pas été vérifiée dans la documentation). (4) La requête LogQL, la configuration d'Alertmanager et les métriques de Kubernetes et de Kueue n'ont pas été exécutées : il n'y a pas de Loki, d'Alertmanager ni de cluster Kubernetes dans le bac à sable. (5) Les métriques GPU de MLflow demandent `nvidia-ml-py` et n'ont pas été exercées. (6) Le comportement du chien de garde NCCL n'a pas été observé : la partie B du lab 14.3 utilise `gloo`. (7) Le nombre de séries par nœud (1 000) et la mémoire par série sont à mesurer sur votre serveur. (8) Les champs JSON de `squeue` et de `sinfo` évoluent d'une version de Slurm à l'autre ; relisez la documentation de la vôtre. (9) Le tableau de `kube-state-metrics` marque `kube_pod_status_phase` comme expérimentale à la date de lecture. (10) Les sources lues ne disent pas quand `DCGM_FI_DEV_XID_ERRORS` revient à zéro : à vérifier sur matériel (voir aussi le projet 5). (11) Le tableau 5 de Llama 3 est incohérent avec le texte : nous citons les comptes (module 10). (12) Rien des § 2.5 (AMD, Ascend) et 7.6 (InfiniBand) n'a tourné sur du matériel ; le nom de série `gpu_prof_tensor_active_percent` est déduit de la convention de nommage de l'exportateur d'AMD, et l'exportateur d'Ascend n'a pas été relu. (13) Les labs ont été testés avec `promtool` 2.45.3, alors que la documentation citée est celle de Prometheus 3.x.

### Hors périmètre {#hors-perimetre}

La configuration complète d'Alertmanager (routage, inhibitions), le stockage de longue durée de Prometheus (écriture distante, Thanos, Mimir), le dimensionnement d'Elasticsearch, le déploiement de collecteurs OpenTelemetry, la lecture fine des compteurs InfiniBand et des commutateurs (module 7, chapitre 8), la détection de corruption silencieuse de données, le profilage fin de noyaux (module 4), l'énergie et les coûts (module 15) et le déploiement de l'exportateur sur un vrai cluster de GPU.
