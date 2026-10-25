---
title: "Ce que demande le marché"
subtitle: "96 offres d'infrastructure de calcul aux États-Unis, en Europe et en Chine, et ce que le parcours en couvre"
description: "Analyse sourcée d'offres d'emploi d'ingénieur d'infrastructure de calcul dans les laboratoires d'IA, les grands groupes, les clouds GPU, les constructeurs et les centres HPC, région par région, comparée au contenu des seize modules."
numbered: true
---

## Résumé {#resume}

-   **Un socle commun.** Python, l'administration Linux, un langage système, l'astreinte, Kubernetes, l'expérience du calcul haute performance et le profilage figurent chacun dans au moins la moitié des offres de l'échantillon.
-   **Kubernetes est plus demandé que Slurm** : 52 % des offres contre 22 %. Slurm reste central dans les centres HPC et dans une partie des laboratoires américains ; en Chine, l'ordonnancement se fait sur Kubernetes ou sur des outils maison.
-   **La santé matérielle est devenue un métier** : détecter, drainer, réparer et remettre en service des nœuds figure dans 38 % des offres, et presque toujours en exigence.
-   **Chaque région a son accent.** Les États-Unis demandent plus souvent Slurm, Prometheus et l'expérience HPC ; l'Europe, Kubernetes, la sécurité, la conformité et l'automatisation ; la Chine, le savoir-faire d'entraînement de grands modèles, les collectives et les accélérateurs chinois.
-   **Le parcours couvre l'essentiel et assume quelques écarts.** Les manques les plus nets étaient les langages système, les accélérateurs non NVIDIA, la virtualisation, l'inférence et les systèmes distribués ; la section [Écarts et décisions](#ecarts) dit ce qui a été ajouté et ce qui reste hors parcours.

## Méthode et limites {#methode}

Les offres ont été lues entre le 22 et le 25 octobre 2026 sur les pages publiques des employeurs ou de leurs outils de recrutement (Greenhouse, Ashby, Lever, SmartRecruiters), sur les pages d'offres de LinkedIn, sur le portail de Tencent et sur des pages d'offres chinoises rendues côté serveur. Pour chaque offre, chaque compétence relevée porte une citation copiée de la page. **Un contrôle mécanique a retrouvé mot pour mot 937 citations sur 937** dans le texte des pages (`tools/verify_quotes.py`).

Les compétences suivent une taxonomie fixe de 44 entrées, définie dans `specs/research-contract.md`. Une compétence est **exigée** quand elle figure dans les qualifications requises, ou qu'elle est manifestement centrale au poste ; elle est **en bonus** quand elle figure parmi les atouts.

Cinq limites à garder en tête.

-   **Échantillon choisi, pas tiré au hasard.** Les employeurs ont été choisis pour couvrir les grands laboratoires, les grands groupes, les clouds GPU, les constructeurs et les centres HPC des trois régions. Les proportions décrivent cet échantillon, pas le marché entier.
-   **Petits effectifs.** Une différence de dix points entre deux régions correspond à quelques offres : lisez les écarts faibles comme du bruit.
-   **Sources inégales.** Plusieurs portails sont rendus en JavaScript ou fermés aux lecteurs automatiques : Hugging Face, Kyutai, Moonshot, Zhipu, MiniMax et les centres nationaux de supercalcul chinois n'ont pas pu être lus. Les offres chinoises viennent surtout de grands groupes, de laboratoires publics et de fabricants de puces.
-   **Postes d'inférence.** Les offres purement orientées inférence ont été limitées volontairement ; elles sont étiquetées pour pouvoir être exclues.
-   **Années d'expérience.** toutes zones : médiane 5 ans (1 à 15, sur 57 offres qui le disent) ; États-Unis : médiane 5 ans (2 à 15, sur 25 offres qui le disent) ; Europe : médiane 5 ans (2 à 10, sur 15 offres qui le disent) ; Chine : médiane 3 ans (1 à 8, sur 16 offres qui le disent). Les fourchettes varient beaucoup avec le niveau du poste.

## L'échantillon {#echantillon}

### Régions et employeurs {#regions-employeurs}

La région est celle du lieu de travail. Les deux postes situés hors des trois régions (Singapour et Canada) comptent dans le total mais pas dans les colonnes régionales.

| Zone du poste | Laboratoires d'IA et start-ups | Grands groupes et hyperscalers | Clouds GPU | Centres HPC | Constructeurs | Autres | Total |
|---|---|---|---|---|---|---|---|
| États-Unis | 9 | 5 | 9 | 5 | 4 | 1 | **33** |
| Europe | 17 | 2 | 11 | 7 | 0 | 1 | **38** |
| Chine | 4 | 10 | 0 | 2 | 7 | 0 | **23** |
| Autres | 0 | 2 | 0 | 0 | 0 | 0 | **2** |
| **Total** | 30 | 19 | 20 | 14 | 11 | 2 | **96** |

### Employeurs lus {#employeurs-lus}

62 employeurs, au plus deux offres par employeur et par relevé :

-   **États-Unis** (23) : AMD, Amazon Web Services, Anthropic, Argonne National Laboratory, Cerebras Systems, CoreWeave, Crusoe, Databricks, Google, Lambda, Lawrence Berkeley National Laboratory, Los Alamos National Laboratory, Meta, Microsoft, NVIDIA, Oak Ridge National Laboratory, OpenAI, Perplexity, Thinking Machines Lab, Together AI, UC San Diego, Vultr, xAI.
-   **Europe** (27) : Aleph Alpha, Anthropic, Black Forest Labs, CEA/DAM Île-de-France, CERN, CSCS – Swiss National Supercomputing Centre, Commissariat au Numérique de Défense, DeepL, Deutsche Telekom IT Solutions HU, ElevenLabs, European Spallation Source ERIC, Fluidstack, Google DeepMind, H Company, Helsing, Isomorphic Labs, Leibniz-Rechenzentrum, Microsoft, Mistral AI, Nebius, Nscale, PhysicsX, Scaleway, Synthesia, Together AI, Verda, Wayve.
-   **Chine** (15) : Alibaba Cloud, Baidu, ByteDance, DeepSeek, Enflame, Huawei, JD.com, MetaX, Moore Threads, Peng Cheng Laboratory, SenseTime, Shanghai AI Laboratory, Sugon, Tencent, Xiaomi.

### Familles de postes {#familles}

| Famille de poste | Offres | Part |
|---|---|---|
| Clusters GPU | 34 | 35 % |
| Plateforme d'entraînement | 12 | 12 % |
| Performance des systèmes ML | 11 | 11 % |
| Exploitation HPC | 11 | 11 % |
| Réseau | 9 | 9 % |
| Stockage | 8 | 8 % |
| Autre | 3 | 3 % |
| Plateforme d'inférence | 3 | 3 % |
| Capacité, FinOps | 3 | 3 % |
| Direction d'équipe | 2 | 2 % |

## Les compétences les plus demandées {#demande}

Le graphique donne, pour les compétences les plus citées, le nombre d'offres qui les mentionnent : la partie rouge compte les offres qui les **exigent**, la partie bleue celles qui les citent seulement en bonus.

<div class="bars" role="list">
<div class="bar" role="listitem"><span class="blab">Python</span><span class="track"><span class="fill two" style="width:59%;float:left"></span><span class="fill" style="width:8%;float:left"></span></span><span class="val">65/96</span></div>
<div class="bar" role="listitem"><span class="blab">Administration Linux</span><span class="track"><span class="fill two" style="width:52%;float:left"></span><span class="fill" style="width:4%;float:left"></span></span><span class="val">54/96</span></div>
<div class="bar" role="listitem"><span class="blab">Langage système (Go, Rust, C++)</span><span class="track"><span class="fill two" style="width:50%;float:left"></span><span class="fill" style="width:5%;float:left"></span></span><span class="val">53/96</span></div>
<div class="bar" role="listitem"><span class="blab">Astreinte, fiabilité (SRE)</span><span class="track"><span class="fill two" style="width:51%;float:left"></span><span class="fill" style="width:3%;float:left"></span></span><span class="val">52/96</span></div>
<div class="bar" role="listitem"><span class="blab">Kubernetes</span><span class="track"><span class="fill two" style="width:38%;float:left"></span><span class="fill" style="width:14%;float:left"></span></span><span class="val">50/96</span></div>
<div class="bar" role="listitem"><span class="blab">Profilage, bancs d'essai</span><span class="track"><span class="fill two" style="width:45%;float:left"></span><span class="fill" style="width:6%;float:left"></span></span><span class="val">49/96</span></div>
<div class="bar" role="listitem"><span class="blab">Expérience HPC</span><span class="track"><span class="fill two" style="width:30%;float:left"></span><span class="fill" style="width:21%;float:left"></span></span><span class="val">49/96</span></div>
<div class="bar" role="listitem"><span class="blab">Expérience d'entraînement ML</span><span class="track"><span class="fill two" style="width:28%;float:left"></span><span class="fill" style="width:18%;float:left"></span></span><span class="val">44/96</span></div>
<div class="bar" role="listitem"><span class="blab">Systèmes distribués</span><span class="track"><span class="fill two" style="width:35%;float:left"></span><span class="fill" style="width:9%;float:left"></span></span><span class="val">43/96</span></div>
<div class="bar" role="listitem"><span class="blab">Réseau (général)</span><span class="track"><span class="fill two" style="width:30%;float:left"></span><span class="fill" style="width:14%;float:left"></span></span><span class="val">42/96</span></div>
<div class="bar" role="listitem"><span class="blab">InfiniBand, RoCE</span><span class="track"><span class="fill two" style="width:27%;float:left"></span><span class="fill" style="width:16%;float:left"></span></span><span class="val">41/96</span></div>
<div class="bar" role="listitem"><span class="blab">Santé matérielle (burn-in, diagnostics, RMA)</span><span class="track"><span class="fill two" style="width:34%;float:left"></span><span class="fill" style="width:4%;float:left"></span></span><span class="val">37/96</span></div>
<div class="bar" role="listitem"><span class="blab">CUDA, programmation GPU</span><span class="track"><span class="fill two" style="width:18%;float:left"></span><span class="fill" style="width:21%;float:left"></span></span><span class="val">37/96</span></div>
<div class="bar" role="listitem"><span class="blab">Prometheus, Grafana</span><span class="track"><span class="fill two" style="width:26%;float:left"></span><span class="fill" style="width:10%;float:left"></span></span><span class="val">35/96</span></div>
<div class="bar" role="listitem"><span class="blab">Systèmes de fichiers parallèles</span><span class="track"><span class="fill two" style="width:19%;float:left"></span><span class="fill" style="width:11%;float:left"></span></span><span class="val">29/96</span></div>
<div class="bar" role="listitem"><span class="blab">Provisioning bare-metal</span><span class="track"><span class="fill two" style="width:21%;float:left"></span><span class="fill" style="width:8%;float:left"></span></span><span class="val">28/96</span></div>
<div class="bar" role="listitem"><span class="blab">Planification de capacité</span><span class="track"><span class="fill two" style="width:23%;float:left"></span><span class="fill" style="width:5%;float:left"></span></span><span class="val">27/96</span></div>
<div class="bar" role="listitem"><span class="blab">CI/CD, automatisation</span><span class="track"><span class="fill two" style="width:20%;float:left"></span><span class="fill" style="width:8%;float:left"></span></span><span class="val">27/96</span></div>
<div class="bar" role="listitem"><span class="blab">Cloud hyperscaler (AWS, GCP, Azure…)</span><span class="track"><span class="fill two" style="width:19%;float:left"></span><span class="fill" style="width:8%;float:left"></span></span><span class="val">26/96</span></div>
<div class="bar" role="listitem"><span class="blab">Conteneurs</span><span class="track"><span class="fill two" style="width:18%;float:left"></span><span class="fill" style="width:9%;float:left"></span></span><span class="val">26/96</span></div>
<div class="bar" role="listitem"><span class="blab">Sécurité, conformité</span><span class="track"><span class="fill two" style="width:23%;float:left"></span><span class="fill" style="width:3%;float:left"></span></span><span class="val">25/96</span></div>
<div class="bar" role="listitem"><span class="blab">Terraform, infrastructure as code</span><span class="track"><span class="fill two" style="width:17%;float:left"></span><span class="fill" style="width:9%;float:left"></span></span><span class="val">25/96</span></div>
<div class="bar" role="listitem"><span class="blab">Collectives (NCCL, RCCL, HCCL)</span><span class="track"><span class="fill two" style="width:16%;float:left"></span><span class="fill" style="width:10%;float:left"></span></span><span class="val">25/96</span></div>
<div class="bar" role="listitem"><span class="blab">Ansible, gestion de configuration</span><span class="track"><span class="fill two" style="width:18%;float:left"></span><span class="fill" style="width:6%;float:left"></span></span><span class="val">23/96</span></div>
</div>

Trois lectures.

-   **Le cœur du métier est l'exploitation.** Linux, l'astreinte, la santé matérielle, le réseau et le profilage pèsent plus que la programmation de noyaux ou le parallélisme de modèle.
-   **L'expérience compte autant que les outils.** « Expérience HPC » (51 %) et « expérience d'entraînement » (46 %) ne s'apprennent pas dans un cours ; les projets et l'exposition à de vraies machines les approchent.
-   **Un langage système est attendu.** Go, Rust ou C++ figurent dans 55 % des offres, et dans la plupart des offres des grands groupes, pour écrire des contrôleurs, des agents de nœud et des outils de flotte.

## Ce qui change d'une région à l'autre {#regions}

| Compétence | Toutes (96) | États-Unis (33) | Europe (38) | Chine (23) |
|---|---|---|---|---|
| Python | 68 % | 79 % | 68 % | 52 % |
| Administration Linux | 56 % | 55 % | 60 % | 52 % |
| Langage système (Go, Rust, C++) | 55 % | 58 % | 53 % | 52 % |
| Astreinte, fiabilité (SRE) | 54 % | 58 % | 63 % | 39 % |
| Kubernetes | 52 % | 48 % | 66 % | 35 % |
| Expérience HPC | 51 % | 61 % | 55 % | 35 % |
| Profilage, bancs d'essai | 51 % | 52 % | 47 % | 52 % |
| Expérience d'entraînement ML | 46 % | 39 % | 37 % | 70 % |
| Systèmes distribués | 45 % | 52 % | 45 % | 35 % |
| Réseau (général) | 44 % | 36 % | 50 % | 44 % |
| InfiniBand, RoCE | 43 % | 48 % | 37 % | 48 % |
| CUDA, programmation GPU | 38 % | 30 % | 37 % | 52 % |
| Santé matérielle (burn-in, diagnostics, RMA) | 38 % | 46 % | 37 % | 30 % |
| Prometheus, Grafana | 36 % | 55 % | 29 % | 26 % |
| Systèmes de fichiers parallèles | 30 % | 30 % | 40 % | 17 % |
| Provisioning bare-metal | 29 % | 33 % | 34 % | 13 % |
| Planification de capacité | 28 % | 27 % | 34 % | 22 % |
| CI/CD, automatisation | 28 % | 30 % | 40 % | 4 % |
| Conteneurs | 27 % | 36 % | 21 % | 26 % |
| Cloud hyperscaler (AWS, GCP, Azure…) | 27 % | 39 % | 26 % | 9 % |
| Terraform, infrastructure as code | 26 % | 33 % | 37 % | 0 % |
| Collectives (NCCL, RCCL, HCCL) | 26 % | 21 % | 24 % | 39 % |
| Sécurité, conformité | 26 % | 24 % | 42 % | 0 % |
| Ansible, gestion de configuration | 24 % | 36 % | 26 % | 4 % |
| Journaux, traces | 23 % | 33 % | 24 % | 4 % |
| Leadership, management | 23 % | 36 % | 24 % | 4 % |
| Slurm | 22 % | 36 % | 21 % | 4 % |
| Entraînement distribué (PyTorch, Megatron, DeepSpeed…) | 20 % | 18 % | 10 % | 39 % |
| Checkpoint, tolérance aux pannes | 20 % | 12 % | 26 % | 22 % |
| Conception d'ordonnanceur | 20 % | 18 % | 21 % | 17 % |

Compétences les plus caractéristiques de chaque région, comparées aux deux autres (au moins trois offres, écart d'au moins dix points) :

-   **États-Unis** : Prometheus, Grafana (55 % contre 27 % ailleurs); Slurm (36 % contre 14 % ailleurs); Leadership, management (36 % contre 16 % ailleurs); Ansible, gestion de configuration (36 % contre 18 % ailleurs); Cloud hyperscaler (AWS, GCP, Azure…) (39 % contre 21 % ailleurs); Python (79 % contre 62 % ailleurs).
-   **Europe** : Sécurité, conformité (42 % contre 16 % ailleurs); Kubernetes (66 % contre 43 % ailleurs); CI/CD, automatisation (40 % contre 21 % ailleurs); Terraform, infrastructure as code (37 % contre 19 % ailleurs); Systèmes de fichiers parallèles (40 % contre 24 % ailleurs); Astreinte, fiabilité (SRE) (63 % contre 48 % ailleurs).
-   **Chine** : Expérience d'entraînement ML (70 % contre 38 % ailleurs); Entraînement distribué (PyTorch, Megatron, DeepSpeed…) (39 % contre 14 % ailleurs); CUDA, programmation GPU (52 % contre 34 % ailleurs); Collectives (NCCL, RCCL, HCCL) (39 % contre 22 % ailleurs); Accélérateurs non NVIDIA (TPU, ROCm, Ascend…) (30 % contre 14 % ailleurs); Infrastructure de RL (17 % contre 3 % ailleurs).

### États-Unis {#us}

Les laboratoires d'IA et les clouds GPU américains exploitent les plus grandes flottes. Leurs offres insistent sur l'automatisation de la santé des nœuds (détection, drainage, réparation, retour en service), sur les fabrics RoCE et InfiniBand à grande échelle et sur l'astreinte. Les laboratoires nationaux (Los Alamos, Oak Ridge, Berkeley, Argonne) ajoutent Slurm, le stockage parallèle, la sécurité et des contraintes d'habilitation propres au pays. Plusieurs offres citent des accélérateurs non NVIDIA (TPU, Trainium, ROCm).

### Europe {#eu}

L'Europe mêle des laboratoires d'IA, des clouds GPU et souverains et de grands centres de calcul. Kubernetes y est cité dans 66 % des offres. La sécurité et la conformité (42 %) reflètent les qualifications souveraines et les enquêtes administratives des centres publics. La virtualisation et le stockage reviennent souvent chez les clouds. Les centres HPC demandent un master ou un diplôme d'ingénieur, plusieurs années de calcul intensif, et proposent souvent des contrats à durée déterminée.

### Chine {#cn}

Les offres chinoises demandent le savoir-faire d'entraînement de grands modèles bien au-delà des postes de recherche : 70 % citent l'expérience d'entraînement, y compris pour l'exploitation, le réseau et le stockage. Les collectives (39 %) et RDMA (48 %) sont fréquentes ; les accélérateurs non NVIDIA (30 %) comprennent Ascend et les GPU de fabricants chinois. Slurm n'apparaît presque jamais (1 sur 23) : l'ordonnancement repose sur Kubernetes et sur des systèmes maison. Les offres lues demandent moins d'années d'expérience qu'ailleurs.

## Ce qui change d'un employeur à l'autre {#employeurs}

| Compétence | Laboratoires d'IA et start-ups (30) | Grands groupes et hyperscalers (19) | Clouds GPU (20) | Centres HPC (14) | Constructeurs (11) |
|---|---|---|---|---|---|
| Python | 77 % | 68 % | 65 % | 64 % | 55 % |
| Administration Linux | 47 % | 42 % | 70 % | 86 % | 55 % |
| Langage système (Go, Rust, C++) | 40 % | 84 % | 65 % | 43 % | 55 % |
| Astreinte, fiabilité (SRE) | 70 % | 58 % | 50 % | 57 % | 9 % |
| Kubernetes | 50 % | 42 % | 75 % | 43 % | 46 % |
| Expérience HPC | 43 % | 37 % | 45 % | 86 % | 73 % |
| Profilage, bancs d'essai | 50 % | 53 % | 60 % | 43 % | 55 % |
| Expérience d'entraînement ML | 57 % | 58 % | 30 % | 14 % | 64 % |
| Systèmes distribués | 53 % | 47 % | 50 % | 21 % | 36 % |
| Réseau (général) | 40 % | 53 % | 45 % | 50 % | 27 % |
| InfiniBand, RoCE | 30 % | 37 % | 55 % | 50 % | 64 % |
| CUDA, programmation GPU | 50 % | 42 % | 25 % | 21 % | 46 % |
| Santé matérielle (burn-in, diagnostics, RMA) | 50 % | 37 % | 40 % | 36 % | 18 % |
| Prometheus, Grafana | 33 % | 37 % | 50 % | 29 % | 27 % |
| Systèmes de fichiers parallèles | 23 % | 5 % | 35 % | 79 % | 27 % |
| Provisioning bare-metal | 23 % | 16 % | 50 % | 50 % | 9 % |
| Planification de capacité | 43 % | 21 % | 25 % | 14 % | 18 % |
| CI/CD, automatisation | 27 % | 37 % | 20 % | 43 % | 9 % |
| Conteneurs | 20 % | 32 % | 20 % | 50 % | 27 % |
| Cloud hyperscaler (AWS, GCP, Azure…) | 40 % | 37 % | 10 % | 14 % | 18 % |
| Terraform, infrastructure as code | 43 % | 21 % | 25 % | 14 % | 9 % |
| Collectives (NCCL, RCCL, HCCL) | 27 % | 32 % | 30 % | 14 % | 27 % |

-   **Laboratoires d'IA et start-ups** : astreinte, systèmes distribués, capacité et coûts, cloud hyperscaler et Terraform.
-   **Grands groupes et hyperscalers** : langage système presque toujours, entraînement distribué, accélérateurs maison ou non NVIDIA.
-   **Clouds GPU** : Kubernetes, Linux, provisioning bare-metal, réseau, virtualisation pour le multi-locataire.
-   **Centres HPC** : Linux, stockage parallèle, Slurm ou PBS, sécurité, achats et relation avec les constructeurs.
-   **Constructeurs** : expérience HPC, InfiniBand, entraînement et accélérateurs propres.

## Ce que le parcours couvre {#couverture}

La profondeur est relevée module par module dans le texte des pages : **mentionné** (cité), **enseigné** (une section ou un exemple travaillé l'explique), **pratiqué** (un lab, un exercice noté ou un jalon de projet le fait faire). Le tableau donne la profondeur maximale atteinte dans le parcours et les modules ou projets qui la portent.

| Compétence | Offres qui la citent | dont exigée | Profondeur dans le parcours | Modules et projets |
|---|---|---|---|---|
| Python | 68 % | 59 % | pratiqué | [1](../courses/linux-systems/index.html), [2](../courses/perf-models/index.html), [3](../courses/parallel-programming/index.html), [4](../courses/gpu-programming/index.html) |
| Administration Linux | 56 % | 52 % | pratiqué | [1](../courses/linux-systems/index.html), [6](../courses/provisioning/index.html), [8](../courses/storage/index.html), [P3](../projects/resilient-trainer/index.html) |
| Langage système (Go, Rust, C++) | 55 % | 50 % | enseigné | [3](../courses/parallel-programming/index.html), [4](../courses/gpu-programming/index.html) |
| Astreinte, fiabilité (SRE) | 54 % | 51 % | pratiqué | [1](../courses/linux-systems/index.html), [5](../courses/slurm/index.html), [10](../courses/fault-tolerance/index.html), [14](../courses/observability/index.html) |
| Kubernetes | 52 % | 38 % | pratiqué | [12](../courses/kubernetes-gpu/index.html), [P4](../projects/multi-provider-scheduler/index.html), [10](../courses/fault-tolerance/index.html), [11](../courses/ray-rl-infra/index.html) |
| Expérience HPC | 51 % | 30 % | pratiqué | [3](../courses/parallel-programming/index.html), [5](../courses/slurm/index.html), [P1](../projects/homelab-slurm/index.html), [P2](../projects/scaling-study/index.html) |
| Profilage, bancs d'essai | 51 % | 45 % | pratiqué | [1](../courses/linux-systems/index.html), [2](../courses/perf-models/index.html), [3](../courses/parallel-programming/index.html), [4](../courses/gpu-programming/index.html) |
| Expérience d'entraînement ML | 46 % | 28 % | pratiqué | [9](../courses/distributed-training/index.html), [2](../courses/perf-models/index.html), [4](../courses/gpu-programming/index.html), [8](../courses/storage/index.html) |
| Systèmes distribués | 45 % | 35 % | pratiqué | [10](../courses/fault-tolerance/index.html), [11](../courses/ray-rl-infra/index.html), [16](../courses/platform-leadership/index.html), [2](../courses/perf-models/index.html) |
| Réseau (général) | 44 % | 30 % | pratiqué | [1](../courses/linux-systems/index.html), [6](../courses/provisioning/index.html), [7](../courses/networking/index.html), [2](../courses/perf-models/index.html) |
| InfiniBand, RoCE | 43 % | 27 % | pratiqué | [7](../courses/networking/index.html) |
| CUDA, programmation GPU | 38 % | 18 % | pratiqué | [4](../courses/gpu-programming/index.html), [2](../courses/perf-models/index.html), [6](../courses/provisioning/index.html) |
| Santé matérielle (burn-in, diagnostics, RMA) | 38 % | 34 % | pratiqué | [5](../courses/slurm/index.html), [6](../courses/provisioning/index.html), [7](../courses/networking/index.html), [10](../courses/fault-tolerance/index.html) |
| Prometheus, Grafana | 36 % | 26 % | pratiqué | [14](../courses/observability/index.html), [P1](../projects/homelab-slurm/index.html), [P5](../projects/gpu-observability/index.html), [11](../courses/ray-rl-infra/index.html) |
| Systèmes de fichiers parallèles | 30 % | 19 % | pratiqué | [8](../courses/storage/index.html), [10](../courses/fault-tolerance/index.html), [12](../courses/kubernetes-gpu/index.html) |
| Provisioning bare-metal | 29 % | 21 % | pratiqué | [6](../courses/provisioning/index.html) |
| Planification de capacité | 28 % | 23 % | pratiqué | [6](../courses/provisioning/index.html), [8](../courses/storage/index.html), [10](../courses/fault-tolerance/index.html), [11](../courses/ray-rl-infra/index.html) |
| CI/CD, automatisation | 28 % | 20 % | enseigné | [1](../courses/linux-systems/index.html), [6](../courses/provisioning/index.html), [16](../courses/platform-leadership/index.html), [P5](../projects/gpu-observability/index.html) |
| Conteneurs | 27 % | 18 % | enseigné | [1](../courses/linux-systems/index.html), [5](../courses/slurm/index.html), [6](../courses/provisioning/index.html), [12](../courses/kubernetes-gpu/index.html) |
| Cloud hyperscaler (AWS, GCP, Azure…) | 27 % | 19 % | pratiqué | [13](../courses/multi-cloud/index.html), [15](../courses/finops-capacity/index.html) |
| Terraform, infrastructure as code | 26 % | 17 % | pratiqué | [6](../courses/provisioning/index.html), [13](../courses/multi-cloud/index.html), [P1](../projects/homelab-slurm/index.html) |
| Collectives (NCCL, RCCL, HCCL) | 26 % | 16 % | pratiqué | [2](../courses/perf-models/index.html), [7](../courses/networking/index.html), [9](../courses/distributed-training/index.html), [3](../courses/parallel-programming/index.html) |
| Sécurité, conformité | 26 % | 23 % | pratiqué | [6](../courses/provisioning/index.html), [13](../courses/multi-cloud/index.html), [16](../courses/platform-leadership/index.html), [12](../courses/kubernetes-gpu/index.html) |
| Ansible, gestion de configuration | 24 % | 18 % | pratiqué | [6](../courses/provisioning/index.html) |
| Journaux, traces | 23 % | 20 % | enseigné | [1](../courses/linux-systems/index.html), [7](../courses/networking/index.html), [9](../courses/distributed-training/index.html), [14](../courses/observability/index.html) |
| Leadership, management | 23 % | 19 % | pratiqué | [16](../courses/platform-leadership/index.html), [P6](../projects/capstone-rfc/index.html), [15](../courses/finops-capacity/index.html) |
| Slurm | 22 % | 12 % | pratiqué | [3](../courses/parallel-programming/index.html), [5](../courses/slurm/index.html), [14](../courses/observability/index.html), [15](../courses/finops-capacity/index.html) |
| Entraînement distribué (PyTorch, Megatron, DeepSpeed…) | 20 % | 15 % | pratiqué | [9](../courses/distributed-training/index.html), [12](../courses/kubernetes-gpu/index.html), [P2](../projects/scaling-study/index.html), [2](../courses/perf-models/index.html) |
| Checkpoint, tolérance aux pannes | 20 % | 16 % | pratiqué | [5](../courses/slurm/index.html), [8](../courses/storage/index.html), [10](../courses/fault-tolerance/index.html), [11](../courses/ray-rl-infra/index.html) |
| Conception d'ordonnanceur | 20 % | 17 % | pratiqué | [5](../courses/slurm/index.html), [12](../courses/kubernetes-gpu/index.html), [13](../courses/multi-cloud/index.html), [P4](../projects/multi-provider-scheduler/index.html) |
| Accélérateurs non NVIDIA (TPU, ROCm, Ascend…) | 18 % | 14 % | pratiqué | [4](../courses/gpu-programming/index.html) |
| Virtualisation (KVM, MIG, vGPU) | 18 % | 10 % | pratiqué | [6](../courses/provisioning/index.html), [1](../courses/linux-systems/index.html) |
| Service d'inférence | 17 % | 12 % | pratiqué | [11](../courses/ray-rl-infra/index.html), [2](../courses/perf-models/index.html), [4](../courses/gpu-programming/index.html) |
| FinOps, coûts | 15 % | 14 % | pratiqué | [8](../courses/storage/index.html), [11](../courses/ray-rl-infra/index.html), [13](../courses/multi-cloud/index.html), [15](../courses/finops-capacity/index.html) |
| Supervision GPU (DCGM) | 14 % | 12 % | pratiqué | [6](../courses/provisioning/index.html), [14](../courses/observability/index.html), [P5](../projects/gpu-observability/index.html) |
| Chaînes de données | 14 % | 9 % | pratiqué | [8](../courses/storage/index.html), [11](../courses/ray-rl-infra/index.html) |
| Centre de données (énergie, refroidissement) | 14 % | 7 % | pratiqué | [15](../courses/finops-capacity/index.html) |
| Achats, relation fournisseurs | 12 % | 12 % | pratiqué | [15](../courses/finops-capacity/index.html), [2](../courses/perf-models/index.html), [6](../courses/provisioning/index.html), [8](../courses/storage/index.html) |
| Stockage objet | 8 % | 7 % | pratiqué | [8](../courses/storage/index.html), [13](../courses/multi-cloud/index.html) |
| Multi-cloud (SkyPilot…) | 7 % | 6 % | pratiqué | [13](../courses/multi-cloud/index.html), [P4](../projects/multi-provider-scheduler/index.html) |
| Clouds GPU spécialisés | 7 % | 6 % | pratiqué | [15](../courses/finops-capacity/index.html), [13](../courses/multi-cloud/index.html) |
| Infrastructure de RL | 6 % | 6 % | pratiqué | [11](../courses/ray-rl-infra/index.html) |
| Suivi d'expériences | 5 % | 4 % | pratiqué | [14](../courses/observability/index.html) |
| Ray | 4 % | 1 % | pratiqué | [11](../courses/ray-rl-infra/index.html) |

## Écarts et décisions {#ecarts}

L'indice d'écart multiplie la part d'offres qui citent une compétence par ce qui manque au parcours pour la pratiquer (3 moins la profondeur). Les compétences d'expérience (années d'HPC ou d'entraînement) ne s'enseignent pas et sont traitées par les projets.

| Compétence | Offres qui la citent | Profondeur | Indice d'écart |
|---|---|---|---|
| Langage système (Go, Rust, C++) | 55 % | enseigné | 0.55 |
| CI/CD, automatisation | 28 % | enseigné | 0.28 |
| Conteneurs | 27 % | enseigné | 0.27 |
| Journaux, traces | 23 % | enseigné | 0.23 |

### Ce qui a été ajouté au parcours {#ajouts}

Ce relevé a conduit, le 25 octobre 2026, à quatre chapitres nouveaux et à des compléments, chacun relu contre ses sources primaires.

-   **Accélérateurs non NVIDIA** (18 % des offres, 30 % en Chine) : [module 4, chapitre 9](../courses/gpu-programming/index.html#ch9), AMD ROCm, TPU et XLA, Trainium, Ascend, avec une liste de contrôle de portabilité.
-   **Inférence** (17 %) : [module 11, chapitre 9](../courses/ray-rl-infra/index.html#ch9), moteurs, cache KV, batching continu, objectifs de service, et le lab 11.4.
-   **Virtualisation** (18 %, 26 % en Europe) : [module 6, chapitre 9](../courses/provisioning/index.html#ch9), IOMMU, VFIO, MIG, vGPU et KubeVirt.
-   **Systèmes distribués et livraison continue** (45 % et 28 %) : [module 16, chapitre 9](../courses/platform-leadership/index.html#ch9), quorum, haute disponibilité de Slurm et de Kubernetes, restauration prouvée, GitOps et canaris, et le lab 16.4.
-   **Langages système** : des ressources vérifiées pour Go et Rust dans la page [Ressources](../resources/index.html), et des variantes Go ou Rust proposées dans les projets [1](../projects/homelab-slurm/index.html#extensions), [4](../projects/multi-provider-scheduler/index.html#extensions) et [5](../projects/gpu-observability/index.html#extensions).
-   **Profils d'entrée** : les modules 12 et 14 ne supposent plus une pratique de Kubernetes ou de Prometheus ; chaque module dit quoi travailler selon le [profil d'entrée](../profile/index.html#profils).

### Ce qui reste un écart assumé {#assume}

-   **Un langage système** s'apprend en écrivant du code pendant des mois, pas dans un chapitre : le parcours fait lire et écrire du C et du CUDA C++ (modules 3 et 4) et propose les variantes Go ou Rust des projets, sans module dédié.
-   **La CI/CD, les conteneurs, les journaux et les traces** sont enseignés (modules 1, 5, 6, 12, 14 et 16) mais sans lab qui leur soit consacré ; les projets 1 et 5 en font pratiquer une partie (tests de règles par `promtool`, exportateurs).
-   **L'expérience** (calcul intensif, entraînement à grande échelle) ne s'acquiert que sur de vraies machines : les projets, un stage dans un centre de calcul ou une compétition de clusters en sont les meilleurs substituts.
-   **Les contraintes propres à un pays** (habilitations de sécurité dans les laboratoires nationaux américains, langue de travail, statut des centres publics) sont signalées, pas enseignées.

## Sources et portée {#sources}

### Documenté {#documente}

Les offres, leurs URL et les citations qui appuient chaque compétence sont dans `data/jobs/*.json` ; l'analyse est recalculée par `python3 tools/market_analysis.py`, la page par `python3 tools/gen_market.py`. La couverture des modules est dans `data/coverage.json`.

### Recommandé {#recommande}

La taxonomie, le classement des employeurs en groupes, l'attribution des niveaux « exigé » et « bonus » et l'indice d'écart sont des choix de lecture, signalés comme tels.

### À vérifier {#a-verifier}

Les offres changent chaque semaine : une offre lue en octobre 2026 peut être fermée. Refaites le relevé avant de prendre une décision de carrière.

### Hors périmètre {#hors-perimetre}

Les salaires (rarement publiés, et pas en Chine), le volume total d'offres par pays, et les postes de recherche pure.
