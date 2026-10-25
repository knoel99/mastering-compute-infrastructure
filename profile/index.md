---
title: "Point de départ : profils d'entrée et autodiagnostic"
subtitle: "Le métier visé, cinq profils d'entrée typiques, une grille pour situer votre niveau et le parcours qui en découle"
description: "Ce que fait un ingénieur d'infrastructure de calcul, les profils d'entrée les plus fréquents, leurs atouts et leurs écarts, et une grille d'autodiagnostic pour choisir quoi travailler à fond."
numbered: true
---

## Ce que fait cette page {#objet}

Ce parcours s'adresse à toute personne qui veut devenir *compute infrastructure engineer*, quel que soit son point de départ. Cette page décrit le métier, puis cinq profils d'entrée typiques, avec leurs atouts et leurs écarts. Elle vous donne enfin une grille pour situer votre propre niveau et choisir **quoi travailler à fond et quoi survoler**.

Le niveau visé ne vient pas d'une impression : il s'appuie sur l'[analyse des offres d'emploi](../market/index.html), qui porte sur des postes publiés aux États-Unis, en Europe et en Chine.

::: note
[Une estimation, pas un verdict]{.tag} Un profil d'entrée est une moyenne : le vôtre mélange souvent deux colonnes. Les questions de positionnement de chaque module (section 0.1) servent à corriger l'estimation. Faites-les honnêtement avant de décider de survoler un module.
:::

## Le métier visé {#metier}

### Ce que fait un ingénieur d'infrastructure de calcul {#role}

Un *compute infrastructure engineer* possède la plateforme de calcul d'une organisation qui entraîne des modèles ou qui exploite un supercalculateur. Il provisionne la capacité GPU, ordonnance les jobs, relie les machines, nourrit les GPU en données et garde les entraînements en vie malgré les pannes. Il observe aussi la flotte, en suit le coût et négocie avec les fournisseurs.

Le métier se distingue de deux voisins. L'**ingénieur d'entraînement à grande échelle** travaille *dans* le job : parallélisme, MFU, numérique. L'**ingénieur plateforme classique** exploite des services, rarement des machines dont la performance dépend du réseau et de la mémoire. L'ingénieur de calcul fait le pont : il comprend assez le job pour le diagnostiquer, et assez la machine pour la faire tenir.

### Les familles de postes {#familles}

Les offres se rangent en quelques familles, que l'[analyse du marché](../market/index.html#echantillon) compte région par région.

-   **Clusters GPU et flotte** : provisionner, valider, réparer et retirer des milliers de nœuds ; santé matérielle, automatisation, astreinte.
-   **Plateforme d'entraînement** : ordonnanceur, files d'attente, reprise des jobs, outillage des chercheurs.
-   **Exploitation HPC** : centres de calcul nationaux et industriels, Slurm ou PBS, stockage parallèle, InfiniBand, sécurité.
-   **Performance des systèmes ML** : profilage, collectives, MFU, accélérateurs de plusieurs fabricants.
-   **Réseau et stockage pour l'IA** : fabrics RoCE et InfiniBand, systèmes de fichiers parallèles, stockage objet.
-   **Capacité, coûts et direction d'équipe** : prévision de la demande, contrats, fournisseurs, organisation.

### Ce qui change d'une région à l'autre {#regions}

Les compétences de fond sont les mêmes partout, mais leur poids varie. L'[analyse du marché](../market/index.html#regions) le détaille ; retenez-en trois tendances pour orienter votre travail.

-   **États-Unis** : flottes géantes, santé matérielle et automatisation de la réparation, réseaux RoCE à grande échelle, accélérateurs de plusieurs fabricants.
-   **Europe** : centres HPC et clouds souverains, Linux et exploitation bare-metal, conformité et sécurité, virtualisation.
-   **Chine** : savoir-faire d'entraînement de grands modèles demandé jusque dans les postes d'exploitation, collectives et RDMA, accélérateurs chinois (Ascend, GPU nationaux), ordonnancement sur Kubernetes plutôt que Slurm.

## Cinq profils d'entrée {#profils}

Chaque profil a des appuis qui raccourcissent certains modules et des écarts qui en allongent d'autres. Le tableau de la section [« Priorités par module »](#priorites) les résume.

### Ingénieur plateforme, SRE ou DevOps {#p-plateforme}

**Appuis.** Kubernetes en production, cloud, infrastructure as code, observabilité et astreinte : c'est la moitié du métier pour les clouds GPU et les laboratoires d'IA.

**Écarts typiques.** Ordonnanceurs HPC, réseau d'interconnexion et NCCL, entraînement distribué, pannes propres aux GPU, achats de capacité. Les services que vous exploitez tombent rarement à cause de la mémoire ou du réseau ; un entraînement, presque toujours.

**Conseil.** Travaillez à fond les modules 2 à 5, 7 à 9 et 11. Pour les modules 12, 14 et 16, suivez la section « Comment travailler ce module » : elle dit quels chapitres restent nouveaux pour vous.

### Administrateur ou ingénieur HPC {#p-hpc}

**Appuis.** Linux, Slurm ou PBS, stockage parallèle, InfiniBand, MPI : le cœur de l'exploitation d'un supercalculateur.

**Écarts typiques.** Kubernetes et cloud, entraînement distribué et NCCL, multi-fournisseurs, coûts. Les offres des laboratoires d'IA et des clouds GPU demandent Kubernetes plus souvent que Slurm.

**Conseil.** Survolez les modules 1, 3, 5 et 6 avec leurs questions de positionnement. Gardez votre effort pour les modules 9 à 13 et 15, et pour le projet 4.

### Ingénieur ML ou chercheur {#p-ml}

**Appuis.** PyTorch, entraînement, usage des GPU côté utilisateur, suivi d'expériences : vous connaissez la charge que la plateforme doit servir.

**Écarts typiques.** Exploitation de machines, réseau, stockage, ordonnancement, fiabilité de production, coûts. L'infrastructure vous est apparue comme une boîte noire qui marche ou ne marche pas.

**Conseil.** Le module 9 vous sera familier : parcours normal, en gardant ses chapitres de diagnostic et de mémoire. Travaillez à fond les modules 6 et 7 (machines et réseau), puis 10 et 12 à 16 (production).

### Développeur logiciel ou systèmes {#p-logiciel}

**Appuis.** C++, Go ou Rust, systèmes distribués, tests et intégration continue : les clouds GPU recrutent beaucoup d'ingénieurs « logiciel d'abord » pour automatiser leur flotte.

**Écarts typiques.** Matériel GPU, réseau haute performance, ordonnanceurs, entraînement, exploitation en astreinte.

**Conseil.** Suivez le parcours dans l'ordre. Vos appuis rendent les projets plus rapides : visez des extensions qui produisent du code réutilisable (exportateur, contrôleur, simulateur).

### Étudiant ou personne en reconversion {#p-etudiant}

**Appuis.** Bases de Linux, de Python et d'algorithmique ; parfois un master en informatique ou en calcul scientifique.

**Écarts typiques.** Presque tout le métier, et surtout l'expérience de production, que les offres comptent en années.

**Conseil.** Suivez le parcours complet dans l'ordre, sans survol. Cherchez tôt une exposition à de vraies machines : stage dans un centre de calcul, compétition de clusters étudiants, projet de recherche. L'[enquête sur les masters](../masters/index.html) recense ces voies.

## Priorités par module {#priorites}

Le tableau croise les cinq profils et les seize modules. **A** : à fond, tous les chapitres, tous les labs, les exercices ★★★. **B** : parcours normal. **C** : survol guidé par les questions de positionnement et les chapitres signalés dans la section « Comment travailler ce module » du module.

<!-- gen:priorities -->
| Module | Ingénieur plateforme, SRE ou DevOps | Administrateur ou ingénieur HPC | Ingénieur ML ou chercheur | Développeur logiciel ou systèmes | Étudiant ou personne en reconversion |
|---|---|---|---|---|---|
| [1. Linux, systèmes et diagnostic de performance](../courses/linux-systems/index.html) | B | C | B | B | A |
| [2. Architecture matérielle et modèles de performance](../courses/perf-models/index.html) | A | B | B | B | A |
| [3. Programmation parallèle : OpenMP, MPI et études de passage à l'échelle](../courses/parallel-programming/index.html) | A | C | B | B | A |
| [4. Programmation GPU : CUDA, Triton et profilage](../courses/gpu-programming/index.html) | A | B | B | B | A |
| [5. Slurm et exploitation d'un cluster HPC](../courses/slurm/index.html) | A | C | B | A | A |
| [6. Provisioning, images et santé des nœuds GPU](../courses/provisioning/index.html) | B | C | A | A | A |
| [7. Réseaux haute performance : InfiniBand, RoCE et NCCL](../courses/networking/index.html) | A | B | A | A | A |
| [8. Stockage et E/S pour l'entraînement](../courses/storage/index.html) | A | B | B | A | A |
| [9. Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline](../courses/distributed-training/index.html) | A | A | B | A | A |
| [10. Pannes, checkpointing et reprise automatique](../courses/fault-tolerance/index.html) | B | A | A | B | A |
| [11. Ray, infrastructure d'apprentissage par renforcement et boucles en ligne](../courses/ray-rl-infra/index.html) | A | A | B | B | A |
| [12. Kubernetes pour l'IA : GPU, files d'attente et gang scheduling](../courses/kubernetes-gpu/index.html) | B | A | A | B | A |
| [13. Flotte multi-fournisseurs : SkyPilot, GPU clouds, hyperscalers et centres HPC](../courses/multi-cloud/index.html) | B | A | A | B | A |
| [14. Observabilité et fiabilité d'une flotte GPU](../courses/observability/index.html) | C | B | A | B | A |
| [15. FinOps, capacité, énergie et achats de calcul](../courses/finops-capacity/index.html) | B | A | A | A | A |
| [16. Plateforme interne, sécurité, production et leadership](../courses/platform-leadership/index.html) | B | B | A | B | B |
<!-- /gen:priorities -->

## Autodiagnostic {#diagnostic}

### Échelle {#echelle}

| Niveau | Signification |
|---|---|
| 0 | Aucune pratique |
| 1 | Notion : lu, vu, utilisé ponctuellement |
| 2 | Pratique : utilisé en projet, mais dans un autre contexte |
| 3 | Responsabilité : opéré en production, avec astreinte ou comptes à rendre |
| 4 | Référence : sait former, arbitrer et trancher |

### Grille par domaine {#grille}

Le niveau visé est celui d'un ingénieur confirmé d'infrastructure de calcul. Il vaut 3 sur les domaines que la plupart des offres exigent, et 2 sur ceux où une bonne culture suffit souvent. Recopiez la grille, remplissez la colonne « Votre niveau », puis calculez l'écart.

| Domaine | Visé | Votre niveau | Écart | Module |
|---|---|---|---|---|
| Linux et exploitation | 3 | | | [1](../courses/linux-systems/index.html) |
| Modèles de performance | 3 | | | [2](../courses/perf-models/index.html) |
| Programmation parallèle (MPI, OpenMP) | 2 | | | [3](../courses/parallel-programming/index.html) |
| Programmation et profilage GPU | 2 | | | [4](../courses/gpu-programming/index.html) |
| Ordonnanceurs HPC (Slurm) | 3 | | | [5](../courses/slurm/index.html) |
| Provisioning et santé des nœuds | 3 | | | [6](../courses/provisioning/index.html) |
| Réseaux haute performance et NCCL | 3 | | | [7](../courses/networking/index.html) |
| Stockage pour l'entraînement | 3 | | | [8](../courses/storage/index.html) |
| Entraînement distribué | 3 | | | [9](../courses/distributed-training/index.html) |
| Pannes et checkpointing | 3 | | | [10](../courses/fault-tolerance/index.html) |
| Ray et infrastructure d'apprentissage par renforcement | 2 | | | [11](../courses/ray-rl-infra/index.html) |
| Kubernetes pour l'IA | 3 | | | [12](../courses/kubernetes-gpu/index.html) |
| Multi-cloud et fournisseurs GPU | 3 | | | [13](../courses/multi-cloud/index.html) |
| Observabilité et fiabilité | 3 | | | [14](../courses/observability/index.html) |
| FinOps, capacité, achats | 3 | | | [15](../courses/finops-capacity/index.html) |
| Plateforme, sécurité, leadership | 3 | | | [16](../courses/platform-leadership/index.html) |
| Langages de systèmes (Go, Rust, C++) | 2 | | | aucun module dédié : C++ et Python dans les modules 3 et 4, Go dans les ressources |

### Lire le résultat {#lecture}

-   **Écart de 2 ou plus** : travaillez le module à fond, avec tous ses labs. C'est là que le parcours vous apporte le plus.
-   **Écart de 1** : parcours normal, en vous appuyant sur l'existant ; les exemples chiffrés et les labs comblent l'écart.
-   **Écart nul** : survol guidé par les questions de positionnement ; gardez le checkpoint de sortie comme preuve.

Refaites la grille à la fin de chaque phase. L'écart doit diminuer là où vous avez travaillé ; sinon, refaites les labs.

## Ce qu'un parcours peut changer, et ce qu'il ne peut pas changer {#limites}

Les offres de niveau confirmé ou *lead* demandent de l'**expérience prouvée** sur de vraies machines, souvent plusieurs années (l'[analyse du marché](../market/index.html#methode) donne les fourchettes relevées). Un parcours d'apprentissage donne des compétences, des projets publics et un vocabulaire ; il ne crée pas des années d'exploitation de clusters en production.

Trois conséquences pratiques.

-   **Viser une marche réaliste d'abord.** Un poste d'ingénieur de flotte GPU, de plateforme d'IA ou d'exploitation HPC valorise déjà ce que le parcours enseigne. Les postes de *lead* viennent ensuite, avec l'expérience.
-   **Fabriquer des preuves publiques.** Les six projets du parcours, un journal d'apprentissage, des contributions à des outils ouverts (ordonnanceurs, files d'attente, exportateurs) et des post-mortems écrits remplacent en partie ce qu'on ne peut pas citer d'un employeur.
-   **Chercher l'exposition réelle.** Un stage dans un centre de calcul, une compétition de clusters étudiants ou un projet de recherche donnent accès à de vraies machines.

::: key
[Règle d'honnêteté]{.tag} Ne présentez jamais un projet de portfolio comme une expérience de production, et dites toujours ce qui a été exécuté sur quelle machine. Un recruteur compétent vérifie, et la franchise est un signal de fiabilité, qualité centrale du métier.
:::

## Comment utiliser ce diagnostic {#usage}

1.  Choisissez le profil d'entrée le plus proche du vôtre, ou les deux entre lesquels vous hésitez.
2.  Remplissez la grille d'autodiagnostic, puis comparez avec le tableau des priorités.
3.  Pour chaque module, faites les questions de positionnement : elles confirment ou corrigent votre estimation.
4.  Refaites la grille à la fin de chaque phase et gardez-la dans votre journal d'apprentissage : elle documente votre progression de façon vérifiable.

## Sources et portée {#sources}

### Documenté {#documente}

Les familles de postes et les tendances régionales résument l'[analyse des offres d'emploi](../market/index.html), dont chaque compétence relevée est appuyée par une citation vérifiée mot pour mot dans le texte de l'offre.

### Recommandé {#recommande}

Les cinq profils d'entrée, les niveaux visés, les priorités A, B et C et l'ordre de travail sont des choix de ce parcours. Ils ne sont ni mesurés, ni validés par un tiers.

### Hors périmètre {#hors-perimetre}

Les salaires, les aspects contractuels d'un recrutement et toute promesse d'embauche.
