---
title: "Ce que demande le marché"
subtitle: "{{N_POST}} offres d'infrastructure de calcul aux États-Unis, en Europe et en Chine, et ce que le parcours en couvre"
description: "Analyse sourcée d'offres d'emploi d'ingénieur d'infrastructure de calcul dans les laboratoires d'IA, les grands groupes, les clouds GPU, les constructeurs et les centres HPC, région par région, comparée au contenu des seize modules."
numbered: true
---

## Résumé {#resume}

-   **Un socle commun.** Python, l'administration Linux, un langage système, l'astreinte, Kubernetes, l'expérience du calcul haute performance et le profilage figurent chacun dans au moins la moitié des offres de l'échantillon.
-   **Kubernetes est plus demandé que Slurm** : {{SHARE:kubernetes}} des offres contre {{SHARE:slurm}}. Slurm reste central dans les centres HPC et dans une partie des laboratoires américains ; en Chine, l'ordonnancement se fait sur Kubernetes ou sur des outils maison.
-   **La santé matérielle est devenue un métier** : détecter, drainer, réparer et remettre en service des nœuds figure dans {{SHARE:hardware-health}} des offres, et presque toujours en exigence.
-   **Chaque région a son accent.** Les États-Unis demandent plus souvent Slurm, Prometheus et l'expérience HPC ; l'Europe, Kubernetes, la sécurité, la conformité et l'automatisation ; la Chine, le savoir-faire d'entraînement de grands modèles, les collectives et les accélérateurs chinois.
-   **Le parcours couvre l'essentiel et assume quelques écarts.** Les manques les plus nets étaient les langages système, les accélérateurs non NVIDIA, la virtualisation, l'inférence et les systèmes distribués ; la section [Écarts et décisions](#ecarts) dit ce qui a été ajouté et ce qui reste hors parcours.

## Méthode et limites {#methode}

Les offres ont été lues entre le 22 et le 25 octobre 2026 sur les pages publiques des employeurs ou de leurs outils de recrutement (Greenhouse, Ashby, Lever, SmartRecruiters), sur les pages d'offres de LinkedIn, sur le portail de Tencent et sur des pages d'offres chinoises rendues côté serveur. Pour chaque offre, chaque compétence relevée porte une citation copiée de la page. **Un contrôle mécanique a retrouvé mot pour mot {{N_QUOTES_OK}} citations sur {{N_QUOTES}}** dans le texte des pages (`tools/verify_quotes.py`).

Les compétences suivent une taxonomie fixe de 44 entrées, définie dans `specs/research-contract.md`. Une compétence est **exigée** quand elle figure dans les qualifications requises, ou qu'elle est manifestement centrale au poste ; elle est **en bonus** quand elle figure parmi les atouts.

Cinq limites à garder en tête.

-   **Échantillon choisi, pas tiré au hasard.** Les employeurs ont été choisis pour couvrir les grands laboratoires, les grands groupes, les clouds GPU, les constructeurs et les centres HPC des trois régions. Les proportions décrivent cet échantillon, pas le marché entier.
-   **Petits effectifs.** Une différence de dix points entre deux régions correspond à quelques offres : lisez les écarts faibles comme du bruit.
-   **Sources inégales.** Plusieurs portails sont rendus en JavaScript ou fermés aux lecteurs automatiques : Hugging Face, Kyutai, Moonshot, Zhipu, MiniMax et les centres nationaux de supercalcul chinois n'ont pas pu être lus. Les offres chinoises viennent surtout de grands groupes, de laboratoires publics et de fabricants de puces.
-   **Postes d'inférence.** Les offres purement orientées inférence ont été limitées volontairement ; elles sont étiquetées pour pouvoir être exclues.
-   **Années d'expérience.** {{YEARS}} Les fourchettes varient beaucoup avec le niveau du poste.

## L'échantillon {#echantillon}

### Régions et employeurs {#regions-employeurs}

La région est celle du lieu de travail. Les deux postes situés hors des trois régions (Singapour et Canada) comptent dans le total mais pas dans les colonnes régionales.

{{SAMPLE_TABLE}}

### Employeurs lus {#employeurs-lus}

{{N_COMPANIES}} employeurs, au plus deux offres par employeur et par relevé :

{{COMPANIES}}

### Familles de postes {#familles}

{{ROLE_TABLE}}

## Les compétences les plus demandées {#demande}

Le graphique donne, pour les compétences les plus citées, le nombre d'offres qui les mentionnent : la partie rouge compte les offres qui les **exigent**, la partie bleue celles qui les citent seulement en bonus.

{{TOP_BARS}}

Trois lectures.

-   **Le cœur du métier est l'exploitation.** Linux, l'astreinte, la santé matérielle, le réseau et le profilage pèsent plus que la programmation de noyaux ou le parallélisme de modèle.
-   **L'expérience compte autant que les outils.** « Expérience HPC » ({{SHARE:hpc-experience}}) et « expérience d'entraînement » ({{SHARE:ml-training-experience}}) ne s'apprennent pas dans un cours ; les projets et l'exposition à de vraies machines les approchent.
-   **Un langage système est attendu.** Go, Rust ou C++ figurent dans {{SHARE:systems-lang}} des offres, et dans la plupart des offres des grands groupes, pour écrire des contrôleurs, des agents de nœud et des outils de flotte.

## Ce qui change d'une région à l'autre {#regions}

{{REGION_TABLE}}

Compétences les plus caractéristiques de chaque région, comparées aux deux autres (au moins trois offres, écart d'au moins dix points) :

{{DISTINCTIVE}}

### États-Unis {#us}

Les laboratoires d'IA et les clouds GPU américains exploitent les plus grandes flottes. Leurs offres insistent sur l'automatisation de la santé des nœuds (détection, drainage, réparation, retour en service), sur les fabrics RoCE et InfiniBand à grande échelle et sur l'astreinte. Les laboratoires nationaux (Los Alamos, Oak Ridge, Berkeley, Argonne) ajoutent Slurm, le stockage parallèle, la sécurité et des contraintes d'habilitation propres au pays. Plusieurs offres citent des accélérateurs non NVIDIA (TPU, Trainium, ROCm).

### Europe {#eu}

L'Europe mêle des laboratoires d'IA, des clouds GPU et souverains et de grands centres de calcul. Kubernetes y est cité dans {{SHARE:kubernetes:eu}} des offres. La sécurité et la conformité ({{SHARE:security-compliance:eu}}) reflètent les qualifications souveraines et les enquêtes administratives des centres publics. La virtualisation et le stockage reviennent souvent chez les clouds. Les centres HPC demandent un master ou un diplôme d'ingénieur, plusieurs années de calcul intensif, et proposent souvent des contrats à durée déterminée.

### Chine {#cn}

Les offres chinoises demandent le savoir-faire d'entraînement de grands modèles bien au-delà des postes de recherche : {{SHARE:ml-training-experience:cn}} citent l'expérience d'entraînement, y compris pour l'exploitation, le réseau et le stockage. Les collectives ({{SHARE:nccl-collectives:cn}}) et RDMA ({{SHARE:infiniband-roce:cn}}) sont fréquentes ; les accélérateurs non NVIDIA ({{SHARE:non-nvidia-accelerators:cn}}) comprennent Ascend et les GPU de fabricants chinois. Slurm n'apparaît presque jamais ({{COUNT:slurm:cn}}) : l'ordonnancement repose sur Kubernetes et sur des systèmes maison. Les offres lues demandent moins d'années d'expérience qu'ailleurs.

## Ce qui change d'un employeur à l'autre {#employeurs}

{{GROUP_TABLE}}

-   **Laboratoires d'IA et start-ups** : astreinte, systèmes distribués, capacité et coûts, cloud hyperscaler et Terraform.
-   **Grands groupes et hyperscalers** : langage système presque toujours, entraînement distribué, accélérateurs maison ou non NVIDIA.
-   **Clouds GPU** : Kubernetes, Linux, provisioning bare-metal, réseau, virtualisation pour le multi-locataire.
-   **Centres HPC** : Linux, stockage parallèle, Slurm ou PBS, sécurité, achats et relation avec les constructeurs.
-   **Constructeurs** : expérience HPC, InfiniBand, entraînement et accélérateurs propres.

## Ce que le parcours couvre {#couverture}

La profondeur est relevée module par module dans le texte des pages : **mentionné** (cité), **enseigné** (une section ou un exemple travaillé l'explique), **pratiqué** (un lab, un exercice noté ou un jalon de projet le fait faire). Le tableau donne la profondeur maximale atteinte dans le parcours et les modules ou projets qui la portent.

{{COVERAGE_TABLE}}

## Écarts et décisions {#ecarts}

L'indice d'écart multiplie la part d'offres qui citent une compétence par ce qui manque au parcours pour la pratiquer (3 moins la profondeur). Les compétences d'expérience (années d'HPC ou d'entraînement) ne s'enseignent pas et sont traitées par les projets.

{{GAPS_TABLE}}

<!-- gen:decisions -->
<!-- /gen:decisions -->

## Sources et portée {#sources}

### Documenté {#documente}

Les offres, leurs URL et les citations qui appuient chaque compétence sont dans `data/jobs/*.json` ; l'analyse est recalculée par `python3 tools/market_analysis.py`, la page par `python3 tools/gen_market.py`. La couverture des modules est dans `data/coverage.json`.

### Recommandé {#recommande}

La taxonomie, le classement des employeurs en groupes, l'attribution des niveaux « exigé » et « bonus » et l'indice d'écart sont des choix de lecture, signalés comme tels.

### À vérifier {#a-verifier}

Les offres changent chaque semaine : une offre lue en octobre 2026 peut être fermée. Refaites le relevé avant de prendre une décision de carrière.

### Hors périmètre {#hors-perimetre}

Les salaires (rarement publiés, et pas en Chine), le volume total d'offres par pays, et les postes de recherche pure.
