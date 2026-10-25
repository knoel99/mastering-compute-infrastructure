---
title: "Programmation GPU : CUDA, Triton et profilage"
subtitle: "Module 04 · Phase 1 · 30 h"
description: "Comprendre un noyau GPU assez pour juger un profil : hiérarchie mémoire, occupation, coalescence, streams, puis Triton, précision numérique et Nsight."
module:
  id: gpu-programming
  number: 4
  phase: 1
  hours: 30
  level: 2
prerequisites: [perf-models]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs vérifiés dans un bac à sable (sans GPU)", class: verified}
labs:
  - {id: warp-memory-model, kind: sandbox}
  - {id: numba-cuda-sim, kind: sandbox}
  - {id: triton-interpret, kind: sandbox}
  - {id: profile-reading, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** un entraînement tourne sur 64 GPU à 35 % de MFU, et l'équipe de recherche vous demande si « c'est le matériel ». Pour répondre, il faut lire un profil et nommer le goulot : calcul, bande passante mémoire, lancement des noyaux, transferts ou attente du CPU. Cela suppose de comprendre un noyau GPU, sans forcément en écrire en production.

Ce module est le pont entre le modèle roofline du [module 2](../perf-models/index.html) et le diagnostic d'une flotte. Vous écrirez de petits noyaux CUDA avec Numba, vous les ferez tourner dans un simulateur CPU, puis vous apprendrez Triton, la précision numérique, le profilage et les techniques qui font gagner du temps (fusion, FlashAttention, CUDA graphs).

::: key
[Règle de ce module]{.tag} Un noyau est limité par une seule ressource à la fois : le calcul, la mémoire ou le lancement. Avant d'optimiser, on mesure laquelle ; après, on revérifie. Un conseil d'optimisation sans profil est une hypothèse.
:::

Aucun GPU n'a servi à rédiger ce module. Tout ce qui est calculé ou capturé ici vient d'un portable CPU : simulateur CUDA de Numba, interpréteur de Triton, profileur PyTorch sur CPU, modèles analytiques écrits pour le cours. Chaque section dit ce qui a été exécuté et ce qui ne l'a pas été ; les traces « de type GPU » sont des **fixtures fabriquées à la main**, étiquetées comme telles.

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 30 h, dont 9,75 h de lecture, 12,5 h de labs et 7,75 h d'exercices |
| Niveau d'entrée | 2 : Python solide, notions de roofline et de MFU (module 2) |
| Prérequis | [Module 2 — Architecture matérielle et modèles de performance](../perf-models/index.html) |
| Pour qui | Cœur : la grammaire des échanges entre l'infrastructure et la recherche sur la performance ; survol possible si vous écrivez déjà des noyaux CUDA ou Triton. |
| Livrable | quatre labs testés (modèle de warp, noyaux Numba, noyaux Triton, lecteur de trace) et une grille de diagnostic écrite par vous |
| Environnement | un portable CPU suffit pour tous les labs ; `nvcc` 12.0 est optionnel (compilation sans exécution). Un GPU est utile pour les branches « Pour aller plus loin », décrites mais non exécutées ici ; leur coût de location n'est pas chiffré ici faute de tarif relu (voir le [module FinOps et capacité](../finops-capacity/index.html)) |
| Projets liés | [Projet 2 — Étude de passage à l'échelle](../../projects/scaling-study/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Écrire un noyau CUDA avec Numba, utiliser la mémoire partagée et le comparer à une version vectorisée (chapitres 1 et 3, labs 4.1 et 4.2).
-   Expliquer la coalescence, l'occupation et la divergence de warps sur un exemple chiffré (chapitres 1 et 2, lab 4.1).
-   Calculer le gain d'un recouvrement entre transferts et calcul avec des flux (chapitre 4).
-   Lire un noyau Triton, dire ce qu'il fusionne et pourquoi le trafic mémoire baisse (chapitre 5, lab 4.3).
-   Choisir un format numérique pour un calcul et prévoir ses pièges : accumulation, sous-dépassement, ordre des sommes (chapitre 6).
-   Lire une trace de profil et nommer le goulot : calcul, mémoire, lancement ou transferts (chapitre 7, lab 4.4).
-   Dire ce qu'apportent la fusion, FlashAttention, `torch.compile` et les CUDA graphs, et quand ils ne paient pas (chapitre 8).

<!-- gen:place -->
### Place dans le parcours {#place}

-   **Phase 1 — Calcul parallèle et GPU** (semaines 6-11) : écrire, mesurer et expliquer un programme parallèle sur CPU et GPU.
-   **S'appuie sur** : [module 2 — Architecture matérielle et modèles de performance](../perf-models/index.html).
-   **Prépare** : [module 9 — Entraînement distribué : DDP, FSDP, parallélisme tensoriel et pipeline](../distributed-training/index.html).
-   **Projets qui s'en servent** : [Projet 2 — Étude de passage à l'échelle d'un entraînement](../../projects/scaling-study/index.html).
<!-- /gen:place -->

### Plan de séances {#seances}

Dix séances, 30 h au total. Le niveau 1 correspond aux fondations, le niveau 2 aux méthodes de cœur, le niveau 3 à l'avancé ; il ne diminue jamais. Les durées de chaque séance additionnent les lectures, les parties de labs et les exercices indiqués, au quart d'heure près.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 3 h | 1 | ch. 1 Modèle d'exécution (1,5 h) | Questions de positionnement et Ex. 1 (0,5 h) ; lab 4.1 partie A (1 h) |
| 2 | 3 h | 1 | ch. 2 Hiérarchie mémoire (1 h) | Ex. 2 (0,5 h) ; lab 4.1 partie B (1,5 h) |
| 3 | 3 h | 2 | ch. 3 Écrire des noyaux (1,5 h) | Lab 4.2 partie A : réduction, scan, produit par tuiles (1,5 h) |
| 4 | 3 h | 2 | consolidation du chapitre 3 (pas de nouvelle lecture) | Lab 4.2 partie B : compteurs et erreurs classiques (1,25 h) ; Ex. 3 (0,75 h) et Ex. 4 (1 h) |
| 5 | 3 h | 2 | ch. 4 Streams (1 h) et ch. 5 Triton (1,25 h) | Ex. 5 (0,75 h) |
| 6 | 3 h | 2 | consolidation du chapitre 5 (pas de nouvelle lecture) | Lab 4.3 : Triton en interpréteur (3 h) |
| 7 | 3 h | 2 | ch. 6 Précision numérique (1 h) | Lab 4.2 partie C : formats, sommes (1,25 h) ; Ex. 7 (0,75 h) |
| 8 | 3 h | 3 | ch. 7 Profiler (1,5 h) | Lab 4.4 partie A : profil CPU (1,5 h) |
| 9 | 3 h | 3 | consolidation du chapitre 7 (pas de nouvelle lecture) | Lab 4.4 partie B : traces de type GPU (1,5 h) ; Ex. 8 (0,75 h) et Ex. 6 (0,75 h) |
| 10 | 3 h | 3 | ch. 8 Techniques d'accélération (1 h) | Ex. 9 et Ex. 10 (1 h chacun) ; checkpoint de sortie |

<!-- gen:travailler -->
### Comment travailler ce module {#travailler}

Le parcours s'adresse à plusieurs profils d'entrée, décrits dans le [point de départ](../../profile/index.html). Le tableau donne la priorité conseillée pour ce module ; les questions de positionnement (section 0.1) la confirment ou la corrigent.

| Profil d'entrée | Priorité | Ce que cela veut dire ici |
|---|---|---|
| Ingénieur plateforme, SRE ou DevOps | à fond | tous les chapitres, tous les labs et les exercices ★★★ |
| Administrateur ou ingénieur HPC | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Ingénieur ML ou chercheur | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Développeur logiciel ou systèmes | normal | les chapitres dans l'ordre, les labs, les exercices ★ et ★★ |
| Étudiant ou personne en reconversion | à fond | tous les chapitres, tous les labs et les exercices ★★★ |

**À ne pas survoler.** Le profilage et la lecture de traces servent à tous les profils, y compris si vous n'écrirez jamais de noyau.

**Méthode.** Répondez aux questions de positionnement avant de lire. Lisez ensuite un chapitre par séance, en refaisant les exemples chiffrés. Faites chaque lab jusqu'à ce que son `verify.sh` passe, puis les exercices dans l'ordre des étoiles. Terminez par le checkpoint de sortie : une capacité compte quand sa preuve existe.
<!-- /gen:travailler -->

## 0. Avant de commencer {#avant}

### 0.1. Questions de positionnement {#positionnement}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si les trois vous paraissent routinières, lisez les exercices ★★★ et le chapitre 7, puis passez au module suivant.

1.  **Un noyau, un million d'éléments.** Vous lancez l'addition de deux vecteurs de $10^6$ éléments avec des blocs de 256 threads. Combien de blocs faut-il, combien de threads sont lancés, et que doit faire le code des threads en trop ?

2.  **Pourquoi des millions de threads ?** Un GPU de 108 multiprocesseurs peut héberger 2048 threads par multiprocesseur. Combien de threads sont résidents en même temps, et pourquoi lance-t-on pourtant des noyaux de plusieurs millions de threads ?

3.  **Une fonction qui rend la main trop tôt.** Dans un programme CUDA, l'appel qui lance un noyau retourne presque aussitôt, avant la fin du calcul. Quelle conséquence cela a-t-il sur un chronomètre placé autour de l'appel ?

::: sol
**Réponses.**

1.  $\lceil 10^6 / 256 \rceil = 3907$ blocs, soit $3907 \times 256 = 1\,000\,192$ threads : 192 threads (0,0192 %) n'ont pas d'élément. Ils doivent tester `i < n` avant d'accéder à la mémoire ; sans ce garde-fou, ils lisent et écrivent hors du tableau (chapitres 1 et 3).

2.  $108 \times 2048 = 221\,184$ threads résidents (limite de la capacité de calcul 8.0). Un noyau de plusieurs millions de threads est découpé en blocs que le matériel distribue au fil des places libres ; et c'est la quantité de travail en attente qui masque la latence mémoire (chapitre 1).

3.  Le lancement est **asynchrone** : le guide de programmation CUDA précise que l'appel retourne avant la fin de l'opération. Un chronomètre CPU autour de l'appel mesure donc le coût du lancement, pas celui du calcul. Il faut synchroniser ou utiliser des événements CUDA (chapitres 4 et 7).
:::

## 1. Le modèle d'exécution CUDA : grille, blocs, warps, SM {#ch1}

Un GPU se programme en écrivant le travail d'**un seul thread**, puis en demandant au matériel d'en lancer des milliers. Ce chapitre donne le vocabulaire et les trois idées qui expliquent presque tous les profils : le découpage en blocs et en warps, la divergence et l'occupation.

### 1.1. Grille, blocs, threads

Un **noyau** (*kernel*) est une fonction exécutée par un très grand nombre de **threads**. Les threads sont regroupés en **blocs**, et l'ensemble des blocs d'un lancement forme la **grille**. Chaque thread connaît ses coordonnées (`threadIdx`, `blockIdx`, `blockDim`) et s'en sert pour choisir l'élément de données dont il s'occupe.

Le matériel est organisé en **multiprocesseurs de flux** (*streaming multiprocessors*, SM). Selon le guide de programmation CUDA (v13.4.2, lu le 25 octobre 2026), tous les threads d'un bloc s'exécutent sur un même SM, ce qui leur permet de communiquer par la mémoire partagée du SM et de se synchroniser. À l'inverse, le guide précise qu'il n'y a aucune garantie d'ordonnancement entre blocs : un bloc ne doit jamais attendre le résultat d'un autre bloc du même lancement.

<figure class="fig">
<svg viewBox="0 0 560 300" role="img" aria-labelledby="grid-t grid-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="grid-t">De la grille aux multiprocesseurs</title>
<desc id="grid-d">Une grille de blocs est découpée en blocs de 256 threads, eux-mêmes découpés en 8 warps de 32 threads ; chaque bloc est affecté à un multiprocesseur qui en héberge plusieurs à la fois.</desc>
<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs>
<text x="20" y="26" text-anchor="start" font-size="17" font-weight="700" fill="currentColor">Grille</text>
<rect x="20" y="38" width="30" height="30" fill="var(--accent)" fill-opacity="0.25" stroke="currentColor" stroke-width="1.2"/>
<rect x="54" y="38" width="30" height="30" fill="var(--accent)" fill-opacity="0.25" stroke="currentColor" stroke-width="1.2"/>
<rect x="88" y="38" width="30" height="30" fill="var(--accent)" fill-opacity="0.25" stroke="currentColor" stroke-width="1.2"/>
<rect x="122" y="38" width="30" height="30" fill="var(--accent)" fill-opacity="0.25" stroke="currentColor" stroke-width="1.2"/>
<rect x="20" y="72" width="30" height="30" fill="var(--accent)" fill-opacity="0.25" stroke="currentColor" stroke-width="1.2"/>
<rect x="54" y="72" width="30" height="30" fill="var(--accent)" fill-opacity="0.25" stroke="currentColor" stroke-width="1.2"/>
<rect x="88" y="72" width="30" height="30" fill="var(--accent)" fill-opacity="0.25" stroke="currentColor" stroke-width="1.2"/>
<rect x="122" y="72" width="30" height="30" fill="var(--accent)" fill-opacity="0.25" stroke="currentColor" stroke-width="1.2"/>
<text x="20" y="126" text-anchor="start" font-size="17" fill="currentColor">3907 blocs</text>
<path d="M168 72 L204 72" stroke="currentColor" stroke-width="1.5" marker-end="url(#ah)"/>
<text x="214" y="26" text-anchor="start" font-size="17" font-weight="700" fill="currentColor">Un bloc : 256 threads</text>
<rect x="214" y="38" width="72" height="34" fill="var(--key-bar)" fill-opacity="0.35" stroke="currentColor" stroke-width="1.2"/>
<text x="250" y="62" text-anchor="middle" font-size="17" fill="currentColor">0</text>
<rect x="294" y="38" width="72" height="34" fill="var(--key-bar)" fill-opacity="0.35" stroke="currentColor" stroke-width="1.2"/>
<text x="330" y="62" text-anchor="middle" font-size="17" fill="currentColor">1</text>
<rect x="374" y="38" width="72" height="34" fill="var(--key-bar)" fill-opacity="0.35" stroke="currentColor" stroke-width="1.2"/>
<text x="410" y="62" text-anchor="middle" font-size="17" fill="currentColor">2</text>
<rect x="454" y="38" width="72" height="34" fill="var(--key-bar)" fill-opacity="0.35" stroke="currentColor" stroke-width="1.2"/>
<text x="490" y="62" text-anchor="middle" font-size="17" fill="currentColor">3</text>
<rect x="214" y="78" width="72" height="34" fill="var(--key-bar)" fill-opacity="0.35" stroke="currentColor" stroke-width="1.2"/>
<text x="250" y="102" text-anchor="middle" font-size="17" fill="currentColor">4</text>
<rect x="294" y="78" width="72" height="34" fill="var(--key-bar)" fill-opacity="0.35" stroke="currentColor" stroke-width="1.2"/>
<text x="330" y="102" text-anchor="middle" font-size="17" fill="currentColor">5</text>
<rect x="374" y="78" width="72" height="34" fill="var(--key-bar)" fill-opacity="0.35" stroke="currentColor" stroke-width="1.2"/>
<text x="410" y="102" text-anchor="middle" font-size="17" fill="currentColor">6</text>
<rect x="454" y="78" width="72" height="34" fill="var(--key-bar)" fill-opacity="0.35" stroke="currentColor" stroke-width="1.2"/>
<text x="490" y="102" text-anchor="middle" font-size="17" fill="currentColor">7</text>
<text x="214" y="132" text-anchor="start" font-size="17" fill="currentColor">8 warps de 32 threads</text>
<path d="M300 144 L300 176" stroke="currentColor" stroke-width="1.5" marker-end="url(#ah)"/>
<rect x="20" y="184" width="520" height="104" fill="none" stroke="currentColor" stroke-width="1.8"/>
<text x="34" y="212" text-anchor="start" font-size="17" font-weight="700" fill="currentColor">Un SM (capacité de calcul 8.0)</text>
<text x="34" y="240" text-anchor="start" font-size="17" fill="currentColor">2048 threads · 64 warps · 32 blocs</text>
<text x="34" y="268" text-anchor="start" font-size="17" fill="currentColor">65 536 registres · 164 Kio partagés</text>
</svg>
<figcaption>De la grille au multiprocesseur : le programmeur choisit la taille du bloc, le matériel affecte les blocs aux SM tant que les quatre ressources (threads, blocs, registres, mémoire partagée) suffisent. Limites du guide CUDA, annexe Compute Capabilities.</figcaption>
</figure>

### 1.2. Calculer son index, garder ses bornes

Le nombre de threads lancés est un multiple de la taille de bloc, rarement le nombre exact d'éléments. Le noyau doit donc tester son index. Voici l'addition de vecteurs écrite avec Numba (fichier `labs/gpu-programming/numba-cuda-sim/kernels.py`) ; le même source compile pour un GPU ou s'exécute dans le simulateur.

~~~python
@cuda.jit
def vec_add(a, b, c):
    i = cuda.grid(1)  # blockIdx.x * blockDim.x + threadIdx.x
    if i < c.shape[0]:  # guard: the grid is rounded up to whole blocks
        c[i] = a[i] + b[i]
~~~

L'hôte lance ce noyau par `vec_add[blocs, threads_par_bloc](a, b, c)`, par exemple `vec_add[3907, 256](a, b, c)` : le premier nombre est la taille de la grille (en blocs), le second celle d'un bloc (en threads). L'assistant `launch_1d` de `kernels.py` calcule le premier à partir de $n$.

::: ex
[Exemple 1.1 — Combien de threads pour un million d'éléments ?]{.tag} Avec des blocs de 256 threads, il faut $\lceil 10^6/256 \rceil = 3907$ blocs, donc $3907 \times 256 = 1\,000\,192$ threads. Les 192 threads en trop représentent 0,0192 % du lancement : négligeable en coût, mais fatal sans garde-fou. Le lab 4.2 le montre : sans le test `i < n`, le simulateur lève une `IndexError` ; sur un vrai GPU, l'écriture hors tableau corrompt la mémoire ou fait échouer un appel ultérieur.
:::

La taille de bloc se choisit multiple de 32 et au plus égale à 1024 (maximum du guide CUDA pour toutes les capacités de calcul listées). Un bloc de 48 threads occupe deux warps dont le second est à moitié vide : 25 % des emplacements de calcul sont perdus.

### 1.3. Warps, SIMT et divergence

Dans un bloc, les threads sont regroupés par 32 en **warps**. Le guide CUDA le dit ainsi : les threads d'un bloc sont organisés en groupes de 32 threads appelés warps, et un warp s'exécute selon le paradigme **SIMT** (*Single Instruction, Multiple Threads*). Tous les threads d'un warp exécutent la même instruction en même temps, chacun sur ses propres données.

Chaque thread peut cependant suivre sa propre branche. Quand les threads d'un warp divergent, le guide précise que ceux qui ne suivent pas la branche sont **masqués** pendant que les autres l'exécutent : les chemins sont exécutés l'un après l'autre. Le guide des bonnes pratiques ajoute que cela augmente le nombre total d'instructions exécutées par le warp.

::: def
[Divergence de warp]{.tag} Un `if` dont la condition prend des valeurs différentes dans un même warp coûte la **somme** des durées des deux chemins non vides, au lieu de la durée d'un seul. Une condition qui ne dépend que de l'indice du warp (par exemple `threadIdx.x / 32`) ne diverge jamais.
:::

Le fichier `warpmodel.py` du lab 4.1 modélise ce coût. Sortie capturée sur le portable de rédaction (`python3 warpmodel.py report`, section divergence) :

~~~text
== Divergence: if (p) 10 cycles else 10 cycles, for one warp ==
p = lane % 2 (alternating lanes)                  20 cycles
p = (lane // 16) % 2 == 0 (half warps)            20 cycles
p = same value for all 32 lanes                   10 cycles
~~~

Ce modèle a une limite à connaître : depuis les architectures récentes le matériel peut entrelacer les branches (*independent thread scheduling*), et le guide déconseille de s'appuyer sur l'exécution simultanée exacte des 32 threads. Le modèle de coût « somme des chemins » reste le bon ordre de grandeur pour un profil.

### 1.4. L'occupation

Les SM cachent la latence mémoire en changeant de warp : pendant qu'un warp attend une donnée, un autre calcule. Le guide des bonnes pratiques définit l'**occupation** comme le rapport entre le nombre de warps actifs par multiprocesseur et le nombre maximal possible. Elle est limitée par la première ressource qui manque : les threads, les blocs, les registres ou la mémoire partagée.

Pour la capacité de calcul 8.0 (A100), le guide de programmation donne : 2048 threads, 64 warps et 32 blocs résidents par SM, 65 536 registres de 32 bits par SM, au plus 255 registres par thread, et jusqu'à 164 Kio de mémoire partagée par SM. Le résultat est
$$\text{blocs par SM} = \min\Bigl(\Bigl\lfloor \tfrac{2048}{t} \Bigr\rfloor,\; 32,\; \Bigl\lfloor \tfrac{65536}{r \cdot t} \Bigr\rfloor,\; \Bigl\lfloor \tfrac{164\,\text{Kio}}{s} \Bigr\rfloor\Bigr)$$
avec $t$ le nombre de threads du bloc, $r$ les registres par thread et $s$ la mémoire partagée par bloc. C'est un modèle simplifié : les calculateurs réels arrondissent les allocations.

::: ex
[Exemple 1.2 — L'occupation d'un produit matriciel par tuiles]{.tag} Le compilateur donne les ressources du noyau. Commande exécutée le 25 octobre 2026 avec `nvcc` 12.0.140, en **compilation seule** (pas de GPU dans le bac à sable) :

~~~bash
nvcc -O2 -arch=sm_80 cuda/reduce_matmul.cu -o reduce_matmul -Xptxas -v
~~~

~~~text
# sortie abrégée : les lignes « Function properties » (0 bytes spill stores) et le noyau vec_add sont omis
ptxas info    : Compiling entry function '_Z12matmul_tiledPKfS0_Pfiii' for 'sm_80'
ptxas info    : Used 32 registers, 2048 bytes smem, 388 bytes cmem[0]
ptxas info    : Compiling entry function '_Z9block_sumPKfPfi' for 'sm_80'
ptxas info    : Used 9 registers, 1024 bytes smem, 372 bytes cmem[0]
~~~

Pour `matmul_tiled` (blocs de 16 × 16 = 256 threads, 32 registres, 2048 octets de mémoire partagée), les limites sont 8 blocs par les threads, 8 par les registres, 82 par la mémoire partagée : 8 blocs, 64 warps, occupation de 100 %. Si le noyau utilisait 128 registres, la limite des registres tomberait à 2 blocs : 16 warps, soit 25 %.
:::

Vérifiez avec le modèle du lab : `python3 warpmodel.py occupancy --threads 256 --regs 32 --smem 2048`.

::: note
[L'occupation n'est pas la performance]{.tag} La documentation de Nsight Compute est explicite : une occupation plus élevée ne donne pas toujours de meilleures performances, mais une occupation basse réduit toujours la capacité à masquer les latences. Une occupation de 25 % avec beaucoup de calcul indépendant par thread peut être très bonne ; 100 % avec des accès mémoire désordonnés ne l'est pas. L'occupation est un indicateur à lire, pas un objectif.
:::

### 1.5. Synchronisation

Dans un bloc, `__syncthreads()` est une barrière : aucun thread ne la franchit avant que tous les threads du bloc l'aient atteinte, et les écritures en mémoire partagée faites avant sont visibles après. C'est le seul mécanisme simple de coopération. Entre blocs, il n'y a pas de barrière dans un noyau : la fin du noyau tient lieu de barrière globale.

Une barrière doit être atteinte par **tous** les threads du bloc. Placée dans un `if` dont la condition varie d'un thread à l'autre, elle est un bogue. La documentation du simulateur de Numba note que, si des threads divergents entrent dans des appels différents de `syncthreads()`, le lancement n'échoue pas mais le comportement est imprévisible : le chapitre 3 montre ce que cela donne.

::: recap
Points clés — chapitre 1

-   Un noyau est écrit pour un thread ; la grille est arrondie à des blocs entiers, donc chaque noyau garde ses bornes.
-   Un bloc tient sur un seul SM, se découpe en warps de 32 threads, et ne peut pas compter sur d'autres blocs.
-   La divergence coûte la somme des chemins d'un warp ; l'occupation est limitée par threads, blocs, registres ou mémoire partagée.
-   `nvcc -Xptxas -v` donne registres et mémoire partagée sans GPU ; une occupation basse nuit, mais une occupation haute ne garantit rien.
:::

## 2. Hiérarchie mémoire GPU : coalescence et conflits de bancs {#ch2}

Sur la plupart des noyaux d'un entraînement, ce n'est pas le calcul qui limite mais la façon dont les threads accèdent à la mémoire. Ce chapitre décrit les niveaux de mémoire d'un GPU, puis les deux règles d'accès qui font perdre ou gagner un facteur de 4 à 32 : la coalescence en mémoire globale et les conflits de bancs en mémoire partagée.

### 2.1. Les niveaux de mémoire

Le tableau résume les niveaux visibles du programmeur. Les capacités viennent du guide de programmation CUDA (annexe des capacités de calcul, lue le 25 octobre 2026) et du billet d'architecture Hopper de NVIDIA ; elles changent d'une génération à l'autre.

| Niveau | Portée | Capacité | Ce qu'il faut en retenir |
|---|---|---|---|
| Registres | un thread | 64 K registres de 32 bits par SM, au plus 255 par thread | le plus rapide ; les débordements (*spills*) vont en mémoire locale |
| Mémoire locale | un thread | jusqu'à 512 Kio par thread | physiquement en mémoire globale : lente |
| Mémoire partagée | un bloc | jusqu'à 164 Kio par SM (capacité 8.0), 228 Kio (capacité 9.0) | programmable, sur puce, organisée en 32 bancs |
| Cache L1 | un SM | partage sa mémoire sur puce (SRAM, *static RAM*) avec la mémoire partagée (256 Kio combinés sur H100) | géré par le matériel |
| Cache L2 | tout le GPU | 50 Mo sur H100 SXM5 | partagé par tous les SM |
| Mémoire globale (HBM, *high bandwidth memory*) | tout le GPU | quelques dizaines de Gio, plusieurs To/s | ce que le roofline du module 2 appelle « la mémoire » |
| Mémoire constante | tout le GPU, lecture seule | 64 Kio | un cache dédié sert bien les lectures identiques d'un warp |

Le H100 SXM5 compte 132 SM d'après le billet Hopper ; l'A100 en compte 108, d'après l'article FlashAttention (chapitre 8). Retenez la hiérarchie plutôt que les chiffres : plus on est près des unités de calcul, plus c'est rapide et plus c'est petit. La mémoire partagée est la seule mémoire rapide que le programmeur gère lui-même.

### 2.2. La coalescence

::: def
[Coalescence]{.tag} Les lectures ou écritures des 32 threads d'un warp sont **coalescées** quand le matériel les sert avec aussi peu de transactions que possible. Pour les capacités de calcul 6.0 et plus, le guide des bonnes pratiques résume : les accès simultanés d'un warp se regroupent en autant de transactions de **32 octets** (des *secteurs*) qu'il en faut pour couvrir toutes les adresses demandées.
:::

Si les 32 threads lisent 32 `float` adjacents et alignés, ils touchent 128 octets consécutifs, soit 4 secteurs : le guide donne exactement cet exemple. Si chaque thread lit un `float` toutes les 8 positions, les 32 lectures tombent dans 32 secteurs différents : le GPU transfère 1024 octets pour en utiliser 128.

<figure class="fig">
<svg viewBox="0 0 560 300" role="img" aria-labelledby="sect-t sect-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="sect-t">Secteurs de 32 octets touchés par un warp</title>
<desc id="sect-d">Trois bandes de 32 secteurs. Pas unité : 4 secteurs touchés. Pas 2 : 8 secteurs touchés. Pas 8 ou plus : les 32 secteurs sont touchés.</desc>
<text x="20" y="26" text-anchor="start" font-size="17" fill="currentColor">Case = un secteur de 32 octets (8 float32)</text>
<text x="20" y="62" text-anchor="start" font-size="17" font-weight="700" fill="currentColor">Pas 1 : a[k]</text>
<rect x="20.0" y="70" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="36.25" y="70" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="52.5" y="70" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="68.75" y="70" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="85.0" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="101.25" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="117.5" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="133.75" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="150.0" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="166.25" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="182.5" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="198.75" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="215.0" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="231.25" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="247.5" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="263.75" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="280.0" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="296.25" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="312.5" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="328.75" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="345.0" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="361.25" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="377.5" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="393.75" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="410.0" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="426.25" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="442.5" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="458.75" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="475.0" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="491.25" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="507.5" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="523.75" y="70" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<text x="540" y="62" text-anchor="end" font-size="17" fill="currentColor">4 secteurs</text>
<text x="20" y="136" text-anchor="start" font-size="17" font-weight="700" fill="currentColor">Pas 2 : a[2k]</text>
<rect x="20.0" y="144" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="36.25" y="144" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="52.5" y="144" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="68.75" y="144" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="85.0" y="144" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="101.25" y="144" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="117.5" y="144" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="133.75" y="144" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="150.0" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="166.25" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="182.5" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="198.75" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="215.0" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="231.25" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="247.5" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="263.75" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="280.0" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="296.25" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="312.5" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="328.75" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="345.0" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="361.25" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="377.5" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="393.75" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="410.0" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="426.25" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="442.5" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="458.75" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="475.0" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="491.25" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="507.5" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<rect x="523.75" y="144" width="15" height="28" fill="none" stroke="currentColor" stroke-width="1.2"/>
<text x="540" y="136" text-anchor="end" font-size="17" fill="currentColor">8 secteurs</text>
<text x="20" y="210" text-anchor="start" font-size="17" font-weight="700" fill="currentColor">Pas 8 : a[8k]</text>
<rect x="20.0" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="36.25" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="52.5" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="68.75" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="85.0" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="101.25" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="117.5" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="133.75" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="150.0" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="166.25" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="182.5" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="198.75" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="215.0" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="231.25" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="247.5" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="263.75" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="280.0" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="296.25" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="312.5" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="328.75" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="345.0" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="361.25" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="377.5" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="393.75" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="410.0" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="426.25" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="442.5" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="458.75" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="475.0" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="491.25" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="507.5" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<rect x="523.75" y="218" width="15" height="28" fill="var(--accent)" fill-opacity="0.55" stroke="currentColor" stroke-width="1.2"/>
<text x="540" y="210" text-anchor="end" font-size="17" fill="currentColor">32 secteurs</text>
<text x="20" y="280" text-anchor="start" font-size="17" fill="currentColor">Rendement : 100 %, 50 %, 12,5 %</text>
</svg>
<figcaption>Les 32 lanes d'un warp lisent chacune un float32 à l'adresse base + k × pas ; les cases pleines sont les secteurs transférés (adresses croissantes de gauche à droite, 256 float32 affichés). Plus le pas grandit, plus le nombre de secteurs augmente, jusqu'à 32 (calculé par warpmodel.py).</figcaption>
</figure>

Le modèle du lab 4.1 compte les secteurs. Sortie capturée (`python3 warpmodel.py report`, section mémoire globale) :

~~~text
== Global memory: 32 lanes load one float32 each (sector = 32 bytes) ==
pattern                                    sectors  efficiency
unit stride (lane k reads a[k])                  4      100.0%
unit stride, base shifted by 4 bytes             5       80.0%
stride 2                                         8       50.0%
stride 8 (32 bytes)                             32       12.5%
stride 32 (column of 32-wide matrix)            32       12.5%
AoS, field x of a 16-byte struct                16       25.0%
32 random elements (seed 0)                     32       12.5%
~~~

Trois enseignements. Un décalage de 4 octets coûte un secteur de plus (80 %). Le rendement tombe à 1/pas jusqu'au pas 8, puis plafonne à 12,5 %. Un accès aléatoire est au pire des cas.

::: ex
[Exemple 2.1 — Tableau de structures contre structure de tableaux]{.tag} Des particules sont stockées dans un tableau de structures de 16 octets (x, y, z, w en `float`). Un noyau qui lit seulement `x` fait lire à chaque thread un octet sur seize : le warp touche 16 secteurs au lieu de 4 pour un tableau de `x` contigus (rendement de 25 %).

Pour $2^{24}$ particules, le noyau transfère 268 Mo au lieu de 67 Mo. À 3,35 To/s (bande passante de la fiche du H100 SXM, voir le module 2), cela donne au mieux 80 µs au lieu de 20 µs : un facteur 4 sur un noyau limité par la mémoire. Les caches peuvent récupérer une partie des octets perdus si le noyau relit ensuite `y`, `z` et `w` ; c'est une borne, pas une prédiction.
:::

La règle pratique : donnez à des threads voisins des adresses voisines. Rangez les données en structure de tableaux (un tableau par champ) quand les noyaux lisent un champ à la fois, et choisissez la dimension rapide du tenseur comme dimension de l'index de thread le plus rapide (`threadIdx.x`).

### 2.3. Mémoire partagée et conflits de bancs

La mémoire partagée est découpée en **32 bancs** (*banks*) d'une largeur de 32 bits. Le guide des bonnes pratiques précise que, depuis la capacité 5.x, des mots de 32 bits successifs sont affectés à des bancs successifs ; le mot d'indice $w$ est donc dans le banc $w \bmod 32$. Comme un warp compte 32 threads et que la mémoire a 32 bancs, un warp peut servir ses 32 accès en un cycle s'ils tombent dans des bancs différents.

::: def
[Conflit de bancs]{.tag} Quand plusieurs adresses **différentes** d'une même requête de warp tombent dans le même banc, les accès sont sérialisés : le guide indique que la bande passante effective diminue d'un facteur égal au nombre de requêtes séparées nécessaires. Si plusieurs threads lisent la **même** adresse, c'est une diffusion (*broadcast*) et il n'y a pas de conflit.
:::

Le cas classique est la lecture d'une colonne d'une tuile $32 \times 32$ : le thread $k$ lit le mot $32k$, donc tous les threads tapent dans le banc 0. Sortie capturée du modèle :

~~~text
== Shared memory: lane k reads tile[k][0] of float tile[32][W+pad] ==
layout                                     conflict degree
W=32, no padding                                        32
W=32, pad 1                                              1
W=16, no padding                                        16
W=33                                                     1
all lanes read the same word (broadcast)                 1
~~~

::: ex
[Exemple 2.2 — La transposition et sa colonne de remplissage]{.tag} Le fichier `labs/gpu-programming/warp-memory-model/cuda/transpose.cu` contient trois noyaux : naïf (lectures coalescées, écritures avec un pas de $n$ éléments, donc 32 secteurs par requête d'écriture), par tuile `tile[32][32]` et par tuile `tile[32][33]`. Les deux versions à tuile lisent et écrivent la mémoire globale en accès coalescés ; la première lit pourtant la tuile par colonnes avec un pas de 32 mots, donc un conflit d'ordre 32, alors que la seconde a un pas de 33 mots, premier avec 32, donc aucun conflit (modèle ci-dessus).

Compilation seule, `nvcc` 12.0.140, `sm_80`, 25 octobre 2026 : 20 registres pour le noyau naïf, 24 registres et 4096 octets de mémoire partagée pour la tuile simple, 24 registres et 4224 octets pour la tuile avec remplissage ; aucun débordement (*0 bytes spill stores*). Le coût du remplissage est de 128 octets par bloc. Le gain réel se mesure sur un GPU avec le programme du lab (non exécuté ici).
:::

Le remplissage fonctionne parce que 33 est premier avec 32 : pour un pas $p \le 32$, le degré de conflit vaut $\gcd(p, 32)$ (vérifié par le modèle du lab 4.1 pour $p$ de 1 à 128 ; voir l'exercice 9). Un pas impair ne produit jamais de conflit.

### 2.4. Registres et débordements

Un thread qui a besoin de plus de registres que le compilateur ne lui en accorde les **déverse** en mémoire locale, c'est-à-dire en mémoire globale cachée. `-Xptxas -v` l'indique par « spill stores » et « spill loads » ; l'option `-maxrregcount` de `nvcc` plafonne les registres pour augmenter l'occupation, au risque de créer ces débordements. Un noyau dont l'occupation est limitée par les registres demande donc un arbitrage chiffré, pas une consigne générale.

::: recap
Points clés — chapitre 2

-   Registres, mémoire partagée, caches, mémoire globale : plus c'est proche, plus c'est rapide et petit ; seule la mémoire partagée est gérée par le programmeur.
-   Coalescence : un warp qui lit 32 `float` adjacents touche 4 secteurs de 32 octets ; avec un pas de 8 ou plus, 32 secteurs (rendement de 12,5 %).
-   Bancs : 32 bancs de 4 octets ; le degré de conflit d'une colonne de tuile vaut le plus grand diviseur commun entre le pas et 32 ; un pas impair l'évite.
-   Ces modèles donnent des bornes de trafic ; la mesure sur GPU reste l'arbitre.
:::

## 3. Écrire des noyaux : réduction, produit par tuiles, scan {#ch3}

Peu d'ingénieurs d'infrastructure écrivent des noyaux de production ; presque tous doivent en lire. Trois patrons couvrent l'essentiel de ce qu'on rencontre dans un profil : la réduction (somme, maximum, normalisation), le produit de matrices par tuiles et le scan (somme cumulée). Les trois reposent sur la mémoire partagée et les barrières du chapitre 1.

### 3.1. La réduction en arbre

Sommer $n$ nombres en parallèle se fait en arbre : à chaque tour, la moitié des threads ajoute la valeur d'un voisin, et la barrière garantit que tout le monde a fini avant le tour suivant. Un bloc de $t$ threads réduit $t$ valeurs en $\log_2 t$ tours. Voici le noyau du lab 4.2 (`kernels.py`), écrit pour Numba ; son jumeau CUDA C++ est dans `cuda/reduce_matmul.cu`.

~~~python
@cuda.jit
def block_sum(x, partial):
    sm = cuda.shared.array(tpb, dtype)
    t = cuda.threadIdx.x
    i = cuda.grid(1)
    sm[t] = x[i] if i < x.shape[0] else 0
    if sync:
        cuda.syncthreads()
    s = tpb // 2
    while s > 0:
        if t < s:
            sm[t] += sm[t + s]
        if sync:
            cuda.syncthreads()
        s //= 2
    if t == 0:
        partial[cuda.blockIdx.x] = sm[0]
~~~

Le noyau est défini dans une fabrique, `make_block_sum(tpb, dtype, sync)` : la taille de bloc `tpb` et le type `dtype` sont des constantes de compilation, comme l'exige la forme d'un tableau partagé. Avec `sync=False`, les deux barrières disparaissent, ce qui reproduit l'erreur classique du § 3.4.

Chaque bloc écrit une somme partielle ; une seconde étape (ici sur le CPU) additionne les sommes partielles. Le nombre de barrières par bloc est $\log_2 t + 1$, et le code les place hors de tout `if`.

::: ex
[Exemple 3.1 — Réduire 256 nombres avec des blocs de 64 threads]{.tag} Le lancement compte 4 blocs. Chaque bloc fait 6 tours (64 → 32 → 16 → 8 → 4 → 2 → 1), soit $63$ additions, donc $4 \times 63 = 252$ additions sur GPU plus 3 sur le CPU : 255 au total, comme une somme séquentielle, mais avec une profondeur de 6 additions sur le GPU puis 2 sur le CPU (en arbre) au lieu de 255.

Le test `test_reduction_matches_the_numpy_tree_bit_for_bit` vérifie que le noyau et une version NumPy qui fait les mêmes additions dans le même ordre donnent **le même résultat à un bit près** en `float32` : l'ordre des additions détermine les bits du résultat (chapitre 6).
:::

Tant que le nombre de threads actifs $s$ est un multiple de 32, des warps entiers sont actifs ou inactifs : pas de divergence. Aux cinq derniers tours ($s < 32$), un seul warp travaille, avec des lanes inactives. C'est un coût fixe, négligeable devant la lecture de la mémoire globale.

### 3.2. Le produit matriciel par tuiles

Le produit naïf donne à chaque thread un élément de la matrice résultat : il lit une ligne de la première matrice et une colonne de la seconde en mémoire globale, soit $2K$ lectures pour une dimension commune $K$. Les mêmes valeurs sont relues par des centaines de threads. Le produit par tuiles charge à la place une tuile de chaque matrice en mémoire partagée, puis chaque valeur sert à $T$ threads.

~~~python
@cuda.jit
def matmul_tiled(A, B, C, loads):
    sA = cuda.shared.array((tile, tile), float32)
    sB = cuda.shared.array((tile, tile), float32)
    tx = cuda.threadIdx.x
    ty = cuda.threadIdx.y
    col, row = cuda.grid(2)
    M = A.shape[0]
    K = A.shape[1]
    N = B.shape[1]
    acc = float32(0)
    for t0 in range(0, K, tile):
        a_col = t0 + tx
        b_row = t0 + ty
        if row < M and a_col < K:
            sA[ty, tx] = A[row, a_col]
            if count:
                cuda.atomic.add(loads, 0, 1)
        else:
            sA[ty, tx] = 0.0
        if b_row < K and col < N:
            sB[ty, tx] = B[b_row, col]
            if count:
                cuda.atomic.add(loads, 0, 1)
        else:
            sB[ty, tx] = 0.0
        cuda.syncthreads()  # the tile is complete before anyone uses it
        for k in range(tile):
            acc += sA[ty, k] * sB[k, tx]
        cuda.syncthreads()  # everyone is done with the tile before it is overwritten
    if row < M and col < N:
        C[row, col] = acc
~~~

Le même schéma de fabrique fixe la taille de tuile `tile` ; `count=True` ajoute un compteur atomique de lectures.

Le lab ajoute un compteur atomique de lectures globales (`count=True`) : on ne mesure pas un temps, on **compte** les accès, ce qui est déterministe et indépendant de la machine. Sortie capturée (`python3 demo.py loads`, Numba 0.68.0, simulateur) :

~~~text
N = 32: product of two 32x32 float32 matrices, global loads counted by an atomic counter
  tile  8:   8192 loads
  tile 16:   4096 loads
  naive  :  65536 loads  (= 2 N^3 = 65536)
~~~

::: ex
[Exemple 3.2 — Lectures globales et intensité arithmétique]{.tag} Pour $N = 32$ : le noyau naïf lit $2N^3 = 65\,536$ valeurs, le noyau à tuiles de $T$ en lit $2N^3/T$ : 8192 pour $T = 8$, 4096 pour $T = 16$.

Le produit fait $2N^3$ FLOP. En comptant 4 octets par valeur, l'intensité arithmétique du chapitre 4 du module 2 passe de 0,25 FLOP/octet (naïf) à $T/4$ : 2 FLOP/octet pour la tuile de 8, 4 pour la tuile de 16.

C'est un décompte idéalisé, sans caches : sur un vrai GPU les caches L1 et L2 absorbent une partie des relectures du noyau naïf. Même à 4 FLOP/octet, un produit à tuiles de 16 reste très en dessous de l'équilibre machine d'un H100 (environ 295 FLOP/octet en BF16, exemple 2.1 du module 2) : les bibliothèques utilisent des tuiles bien plus grandes, hiérarchiques, et les cœurs tensoriels.
:::

Deux contraintes dimensionnent la tuile. Avec un élément par thread, une tuile $T \times T$ demande $T^2 \le 1024$ threads, donc $T \le 32$. Elle demande aussi $2T^2$ valeurs en mémoire partagée : 2048 octets pour $T = 16$ en `float32`, 8192 pour $T = 32$.

### 3.3. Le scan

Un **scan** inclusif calcule toutes les sommes cumulées : `out[i] = x[0] + ... + x[i]`. En parallèle, la version de Hillis et Steele fait $\log_2 t$ tours, chacun ajoutant la valeur située `offset` places plus tôt. Chaque tour demande **deux** barrières (tout le monde lit, puis tout le monde écrit) sinon un thread lit une valeur déjà modifiée. Les sommes de blocs sont ensuite scannées puis rajoutées à chaque bloc, en trois étapes (`inclusive_scan` dans `kernels.py`).

Pour un bloc de 32 threads, cette version effectue $\sum_{k=0}^{4}(32 - 2^k) = 129$ additions, contre 31 pour un scan séquentiel : elle gagne en profondeur (5 tours) et perd en travail. Les versions industrielles utilisent l'algorithme de Blelloch, qui effectue un travail proportionnel à $n$ ; il n'est pas implémenté ici.

### 3.4. Les erreurs classiques

Le tableau liste les erreurs qui produisent des profils ou des résultats absurdes.

| Erreur | Symptôme | Parade |
|---|---|---|
| Garde-fou `i < n` oublié | écriture hors tableau, corruption silencieuse sur GPU | tester les bornes ; lancer sous `compute-sanitizer` |
| Barrière oubliée entre écriture et lecture partagées | résultat faux, parfois juste | une barrière après chaque phase d'écriture |
| Barrière dans un `if` divergent | blocage ou résultat imprévisible | barrière hors de toute condition |
| Plusieurs blocs écrivent la même sortie | course de données | atomiques, ou une sortie par bloc comme ici |
| Chronométrer sans synchroniser | temps absurdement courts | événements CUDA ou synchronisation explicite (chapitre 4) |
| Comparer des flottants avec `==` après une réduction | échecs aléatoires | tolérance, ou ordre d'addition fixé (chapitre 6) |

Le simulateur attrape la première erreur et rend la seconde visible. Sortie capturée (`python3 demo.py errors`) :

~~~text
unguarded kernel: IndexError -> tid=[44, 0, 0] ctaid=[1, 0, 0]: index 108 is out of bounds for axis 0
reduction without barriers: 5 wrong results out of 5 launches
~~~

Le numéro du premier thread fautif varie d'une exécution à l'autre ; le résultat « 5 sur 5 » aussi peut varier, car le simulateur laisse le système d'exploitation ordonnancer ses threads. Le test du lab accorde donc six essais et exige au moins un résultat faux.

::: war
[Ce que le simulateur ne voit pas]{.tag} La documentation du simulateur CUDA de Numba liste ses limites : « Warps and warp-level operations are not yet implemented. » Il ne modélise donc ni la coalescence, ni les conflits de bancs, ni la divergence : ces comportements se calculent avec le modèle du lab 4.1 ou se mesurent sur un GPU. Il ne réalise pas non plus de contrôle de types, et le temps qu'il mesure n'a aucun rapport avec celui d'un GPU. Source : [Numba, CUDA simulator](https://numba.readthedocs.io/en/stable/cuda/simulator.html).
:::

### 3.5. Noyau écrit à la main ou version vectorisée ?

Dans une vraie base de code, vous appelez `torch.sum` ou `torch.matmul`, qui passent par des bibliothèques optimisées par NVIDIA et par l'équipe PyTorch. Les tests du lab comparent chaque noyau à NumPy, la « version vectorisée » : égalité exacte pour les entiers, tolérance relative de $10^{-4}$ pour les produits `float32`. Le chronométrage de ces comparaisons n'a de sens que sur GPU : `bench_gpu.py` le fait avec des événements CUDA, mais il n'a **pas** été exécuté pour ce cours.

::: recap
Points clés — chapitre 3

-   Réduction : arbre en $\log_2 t$ tours, une barrière par tour, barrières hors de tout `if` ; l'ordre des additions fixe les bits du résultat.
-   Produit par tuiles : chaque valeur lue en mémoire globale sert $T$ fois ; les lectures globales passent de $2N^3$ à $2N^3/T$ (compté dans le simulateur).
-   Scan : $\log_2 t$ tours à deux barrières ; la version simple a peu de tours mais fait plus d'additions qu'un scan séquentiel.
-   Les erreurs classiques sont des bornes et des barrières ; le simulateur en attrape une partie, un outil comme `compute-sanitizer` le reste sur GPU.
:::

## 4. Streams, événements, mémoire épinglée et recouvrement {#ch4}

Un GPU exécute des noyaux et des copies. Si le programme les enchaîne l'un après l'autre, le GPU attend les copies, et les copies attendent le GPU. Ce chapitre montre comment les recouvrir, et comment ne pas se tromper en les chronométrant.

### 4.1. L'asynchronisme

Le guide de programmation CUDA décrit l'interface comme asynchrone : un appel qui lance un noyau ou une copie retourne aussitôt, souvent avant que l'opération ait commencé. Le CPU peut alors préparer la suite pendant que le GPU travaille. La documentation de PyTorch en tire la conséquence pour le chronométrage : les mesures de temps sans synchronisation ne sont pas exactes ; il faut appeler `torch.cuda.synchronize()` avant de mesurer, ou utiliser des `torch.cuda.Event`.

Un **flux** (*stream*) est une file d'attente d'opérations exécutées dans l'ordre. Deux opérations de flux différents peuvent s'exécuter en même temps si les ressources le permettent ; une opération lancée sans flux explicite va dans le flux par défaut. Un **événement** est un repère inséré dans un flux : on l'utilise pour chronométrer sur le GPU (`cudaEventElapsedTime`) et pour faire attendre un flux sur un autre.

### 4.2. La mémoire épinglée

Un tampon de mémoire CPU ordinaire est **paginable** : le système peut déplacer ses pages. Un tampon **épinglé** (*pinned*, ou *page-locked*) garde les siens en place, et c'est la condition pour qu'une copie soit réellement asynchrone. On l'alloue avec `cudaMallocHost` (CUDA C++), comme le fait le fichier du lab.

::: war
[Une copie asynchrone depuis la mémoire paginable est synchrone]{.tag} Le guide de programmation CUDA l'écrit ainsi : pour que les copies impliquant la mémoire du CPU s'exécutent de façon asynchrone, les tampons de l'hôte doivent être épinglés. Avec de la mémoire paginable, `cudaMemcpyAsync()` fonctionne mais retombe sur un comportement synchrone qui ne recouvre rien. Source : [CUDA Programming Guide, § 2.5](https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/asynchronous-execution.html).
:::

Le guide des bonnes pratiques ajoute deux avertissements. Les copies depuis la mémoire épinglée atteignent la bande passante maximale : à titre d'exemple, environ 12 Go/s sur une carte PCIe x16 de génération 3 (le chiffre dépend de votre machine : mesurez-le). Et la mémoire épinglée est une ressource rare : en abuser dégrade les performances du système.

### 4.3. Recouvrir transferts et calcul

Cas typique : traiter un grand tampon en trois étapes, copie vers le GPU, noyau, copie retour. On le découpe en $c$ morceaux, chacun dans son flux. Le noyau du morceau 1 s'exécute pendant la copie du morceau 2. Voici la boucle du fichier `cuda/streams_overlap.cu` (lab 4.2, non exécuté ici faute de GPU).

~~~cuda
for (int c = 0; c < chunks; ++c) {
  cudaStream_t st = s[c % streams];
  float* hp = h + c * per;
  float* dp = d + c * per;
  CHECK(cudaMemcpyAsync(dp, hp, per * sizeof(float), cudaMemcpyHostToDevice, st));
  busy_scale<<<(per + 255) / 256, 256, 0, st>>>(dp, int(per), 2000);
  CHECK(cudaMemcpyAsync(hp, dp, per * sizeof(float), cudaMemcpyDeviceToHost, st));
}
~~~

<figure class="fig">
<svg viewBox="0 0 560 330" role="img" aria-labelledby="strm-t strm-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="strm-t">Un flux contre quatre morceaux</title>
<desc id="strm-d">Chronologie : avec un seul flux les trois étapes se suivent, 110 ms au total ; en quatre morceaux elles se recouvrent, 57,5 ms au total.</desc>
<defs><marker id="ah2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs>
<text x="10" y="20" text-anchor="start" font-size="16" font-weight="700" fill="currentColor">1 flux : 110 ms</text>
<text x="10" y="49" text-anchor="start" font-size="16" fill="currentColor">H→D</text>
<line x1="110" y1="60" x2="550.0" y2="60" stroke="currentColor" stroke-opacity=".2"/>
<rect x="110.0" y="30" width="160.0" height="24" fill="var(--accent)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<text x="10" y="83" text-anchor="start" font-size="16" fill="currentColor">noyau</text>
<line x1="110" y1="94" x2="550.0" y2="94" stroke="currentColor" stroke-opacity=".2"/>
<rect x="270.0" y="64" width="120.0" height="24" fill="var(--key-bar)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<text x="10" y="117" text-anchor="start" font-size="16" fill="currentColor">D→H</text>
<line x1="110" y1="128" x2="550.0" y2="128" stroke="currentColor" stroke-opacity=".2"/>
<rect x="390.0" y="98" width="160.0" height="24" fill="var(--accent)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<text x="10" y="170" text-anchor="start" font-size="16" font-weight="700" fill="currentColor">4 morceaux, 3 flux : 57,5 ms</text>
<text x="10" y="199" text-anchor="start" font-size="16" fill="currentColor">H→D</text>
<line x1="110" y1="210" x2="550.0" y2="210" stroke="currentColor" stroke-opacity=".2"/>
<text x="10" y="233" text-anchor="start" font-size="16" fill="currentColor">noyau</text>
<line x1="110" y1="244" x2="550.0" y2="244" stroke="currentColor" stroke-opacity=".2"/>
<text x="10" y="267" text-anchor="start" font-size="16" fill="currentColor">D→H</text>
<line x1="110" y1="278" x2="550.0" y2="278" stroke="currentColor" stroke-opacity=".2"/>
<rect x="110.0" y="180" width="40.0" height="24" fill="var(--accent)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<rect x="150.0" y="214" width="30.0" height="24" fill="var(--key-bar)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<rect x="180.0" y="248" width="40.0" height="24" fill="var(--accent)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<rect x="150.0" y="180" width="40.0" height="24" fill="var(--accent)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<rect x="190.0" y="214" width="30.0" height="24" fill="var(--key-bar)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<rect x="220.0" y="248" width="40.0" height="24" fill="var(--accent)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<rect x="190.0" y="180" width="40.0" height="24" fill="var(--accent)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<rect x="230.0" y="214" width="30.0" height="24" fill="var(--key-bar)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<rect x="260.0" y="248" width="40.0" height="24" fill="var(--accent)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<rect x="230.0" y="180" width="40.0" height="24" fill="var(--accent)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<rect x="270.0" y="214" width="30.0" height="24" fill="var(--key-bar)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<rect x="300.0" y="248" width="40.0" height="24" fill="var(--accent)" fill-opacity="0.45" stroke="currentColor" stroke-width="1.2"/>
<line x1="110" y1="292" x2="550.0" y2="292" stroke="currentColor"/>
<text x="110.0" y="312" text-anchor="middle" font-size="16" fill="currentColor">0</text>
<text x="190.0" y="312" text-anchor="middle" font-size="16" fill="currentColor">20</text>
<text x="270.0" y="312" text-anchor="middle" font-size="16" fill="currentColor">40</text>
<text x="350.0" y="312" text-anchor="middle" font-size="16" fill="currentColor">60</text>
<text x="430.0" y="312" text-anchor="middle" font-size="16" fill="currentColor">80</text>
<text x="510.0" y="312" text-anchor="middle" font-size="16" fill="currentColor">100</text>
<text x="550.0" y="330" text-anchor="end" font-size="16" fill="currentColor">ms</text>
</svg>
<figcaption>Même travail, mêmes durées par étape (40, 30 et 40 ms pour le tampon entier) ; le découpage en 4 morceaux sur 3 flux masque presque tout sauf la plus longue étape. Modèle de l'exemple 4.1.</figcaption>
</figure>

Modélisons le gain. Soit $t_{in}$, $t_k$ et $t_{out}$ les durées des trois étapes pour le tampon entier, supposées proportionnelles à la taille, avec un moteur de copie par direction. Découpées en $c$ morceaux, les étapes forment un pipeline dont l'étape la plus lente impose le rythme :

$$T(c) = \frac{t_{in} + t_k + t_{out}}{c} + \frac{c-1}{c}\,\max(t_{in}, t_k, t_{out})$$

Quand $c$ croît, $T$ tend vers le maximum des trois durées : le recouvrement masque tout sauf l'étape la plus longue.

::: ex
[Exemple 4.1 — Quatre morceaux au lieu d'un]{.tag} Avec des étapes de 40, 30 et 40 ms (valeurs choisies pour l'exemple), un seul morceau prend 110 ms. Avec quatre morceaux : $110/4 + 3 \times 40/4 = 57{,}5$ ms, soit un gain de 1,91.

Pour 1, 2, 4, 8 et 16 morceaux, la formule donne 110, 75, 57,5, 48,75 et 44,4 ms ; la borne est 40 ms. La figure ci-dessus trace les deux premiers cas.
:::

Le modèle suppose des copies et un noyau indépendants, des morceaux assez grands pour que chaque noyau occupe le GPU, et ignore le coût fixe de chaque lancement. Il faut aussi que les copies partent de mémoire épinglée. Il ne dit pas si votre GPU a un moteur de copie par direction : cela se vérifie dans la documentation du modèle et par la mesure.

### 4.4. Ce que fait PyTorch pour vous

Dans PyTorch, les opérations sur GPU sont asynchrones et le framework synchronise automatiquement quand il copie des données entre CPU et GPU ; les fonctions de copie acceptent un argument `non_blocking` qui permet de contourner cette synchronisation quand elle est inutile (notes CUDA de PyTorch 2.14). 

Deux conséquences pour un profil : une opération qui ramène une valeur sur le CPU (par exemple lire un scalaire pour l'afficher) force l'attente de toutes les opérations précédentes ; et un chargeur de données qui n'épingle pas ses tampons prive l'entraînement du recouvrement. Les noms exacts des options de chargement sont à vérifier dans la documentation de votre version.

::: recap
Points clés — chapitre 4

-   Lancements et copies asynchrones : un chronomètre CPU sans synchronisation mesure le lancement, pas l'exécution.
-   Un flux est une file ordonnée ; des flux distincts permettent le recouvrement ; les événements chronomètrent sur le GPU.
-   Sans mémoire épinglée, `cudaMemcpyAsync` devient synchrone.
-   Pipeline en $c$ morceaux : $T(c)$ tend vers l'étape la plus lente ; avec 40, 30 et 40 ms, quatre morceaux ramènent 110 ms à 57,5 ms.
:::

## 5. Triton : programmer par blocs {#ch5}

CUDA demande d'écrire ce que fait **un thread** et de gérer à la main mémoire partagée, barrières et coalescence. Triton propose de décrire ce que fait **un bloc de données**, et laisse le compilateur choisir la répartition sur les threads. Il s'exécute sans GPU dans un interpréteur, ce qui le rend idéal pour apprendre.

### 5.1. Un programme par bloc

Le dépôt de Triton le présente comme un langage et un compilateur pour écrire des primitives d'apprentissage profond très efficaces, avec l'ambition d'une productivité supérieure à CUDA et d'une flexibilité supérieure à d'autres langages dédiés. Ses fondations sont décrites dans l'article de Tillet, Kung et Cox (MAPL 2019), qui introduit un langage de blocs (« tuiles »), une représentation intermédiaire et un auto-réglage. Le langage actuel est intégré à Python et diffère de la syntaxe de cet article.

Dans un noyau Triton, une **instance de programme** traite un bloc d'éléments. `tl.program_id(axis=0)` donne son numéro, `tl.arange(0, BLOCK_SIZE)` crée un vecteur d'indices, et `tl.load`/`tl.store` lisent et écrivent des blocs entiers. Le tutoriel officiel appelle la grille de lancement « SPMD » (*single program, multiple data* : un même programme, des données différentes) et la compare à une grille CUDA.

~~~python
@triton.jit
def add_kernel(x_ptr, y_ptr, out_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
    pid = tl.program_id(axis=0)
    offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements  # the last program may run past the end
    x = tl.load(x_ptr + offsets, mask=mask)
    y = tl.load(y_ptr + offsets, mask=mask)
    tl.store(out_ptr + offsets, x + y, mask=mask)
~~~

Le masque `offsets < n_elements` joue le rôle du garde-fou du chapitre 1 : la dernière instance dépasse la fin du tableau. L'hôte lance autant d'instances que de blocs avec `add_kernel[(triton.cdiv(n, block),)](x, y, out, n, BLOCK_SIZE=block)`. `BLOCK_SIZE` est une constante de compilation (`tl.constexpr`), comme la taille de tuile du chapitre 3.

### 5.2. La fusion : le softmax

Le softmax de chaque ligne d'une matrice $M \times N$ s'écrit en cinq opérations PyTorch : maximum de la ligne, soustraction, exponentielle, somme, division. Chacune lit et écrit la mémoire globale. Le noyau Triton ci-dessous garde la ligne entière en mémoire rapide et ne lit qu'une fois, n'écrit qu'une fois.

~~~python
@triton.jit
def softmax_kernel(x_ptr, out_ptr, n_cols, row_stride, BLOCK_SIZE: tl.constexpr):
    """One program per row; the whole row lives in registers/SRAM: read once, write once."""
    row = tl.program_id(axis=0)
    cols = tl.arange(0, BLOCK_SIZE)
    mask = cols < n_cols
    x = tl.load(x_ptr + row * row_stride + cols, mask=mask, other=-float("inf"))
    x = x - tl.max(x, axis=0)  # numerical stability: subtract the row maximum
    num = tl.exp(x)
    den = tl.sum(num, axis=0)
    tl.store(out_ptr + row * row_stride + cols, num / den, mask=mask)
~~~

Le lab 4.3 ne recopie pas la formule du tutoriel : le registre `traffic.py` exécute les cinq opérations et additionne les éléments des tenseurs d'entrée et de sortie de chacune (comptage idéalisé : chaque opération relit tous ses opérandes en DRAM, sans cache). Sortie capturée (`python3 traffic.py 4096 2048`, PyTorch 2.14.1 CPU, 25 octobre 2026) :

~~~text
softmax of a 4096 x 2048 float32 matrix as 5 separate operations:
  reads      41951232 elements  (5MN + 2M = 41951232)
  writes     25174016 elements  (3MN + 2M = 25174016)
  traffic 256.1 MiB unfused versus 64.0 MiB fused -> x4.001
~~~

Les totaux $5MN + 2M$ lus et $3MN + 2M$ écrits sont ceux que le tutoriel officiel de softmax fusionné annonce en commentaire ; il en déduit une accélération théorique d'environ 4.

::: ex
[Exemple 5.1 — Ce que vaut la fusion sur un H100]{.tag} Le softmax non fusionné transfère $268{,}5 \cdot 10^6$ octets et le noyau fusionné $67{,}1 \cdot 10^6$. Si les deux sont limités par la bande passante de 3,35 To/s (fiche du H100 SXM, module 2), les bornes inférieures de durée sont $80{,}1$ µs et $20{,}0$ µs. Ce sont des **bornes** : un noyau réel atteint une fraction de la bande passante, et les caches modifient le trafic.

Le rapport 4 est l'ordre de grandeur qu'une mesure sur GPU devrait approcher si les deux versions sont limitées par la bande passante et si la ligne tient en mémoire rapide : c'est une hypothèse à tester, pas un résultat.
:::

La condition « la ligne tient » est une vraie limite : `BLOCK_SIZE` est la plus petite puissance de 2 au moins égale au nombre de colonnes, et tout le bloc vit dans les registres et la mémoire partagée. Pour des lignes très longues, il faut un algorithme en plusieurs passes, comme celui de FlashAttention (chapitre 8).

### 5.3. L'auto-réglage

Les bonnes valeurs de `BLOCK_SIZE`, du nombre de warps ou d'étages de pipeline dépendent du GPU. `@triton.autotune(configs=[...], key=[...])` essaie une liste de configurations et retient la meilleure : la documentation précise que `key` liste les arguments dont un changement de valeur déclenche une nouvelle évaluation de toutes les configurations. Le coût est une compilation et un chronométrage à chaque nouvelle forme.

::: note
[Observé dans le bac à sable]{.tag} Dans l'interpréteur, `@triton.autotune` **ne fonctionne pas** : l'appel a levé `RuntimeError: 0 active drivers ([]). There should only be one.` (Triton 3.8.0, 25 octobre 2026, Linux sans GPU). L'auto-réglage chronomètre de vrais noyaux, ce qu'un interpréteur ne fait pas. Il vit donc dans `bench_gpu.py`, qui est octet-compilé mais jamais exécuté ici.
:::

### 5.4. L'interpréteur

Avec `TRITON_INTERPRET=1`, d'après la documentation de débogage de Triton, tous les noyaux contournent la compilation et sont simulés par l'interpréteur avec des équivalents NumPy ; il traite les instances de programme une par une, en séquence. Cela permet de poser un point d'arrêt (`pdb`) dans un noyau, d'afficher les valeurs intermédiaires et de tester les masques, ce que le lab 4.3 fait avec 13 tests.

::: war
[Limites documentées de l'interpréteur]{.tag} La documentation de débogage de Triton liste des limites connues : l'interpréteur « does not support operations on bfloat16 numeric types » (il faut convertir en `float32`) et ne gère pas les accès mémoire indirects (charger un pointeur depuis la mémoire, puis charger à cette adresse). Source : [Triton, débogage](https://triton-lang.org/main/programming-guide/chapter-3/debugging.html).
:::

::: note
[Observé dans le bac à sable : `bfloat16`]{.tag} Dans notre essai (Triton 3.8.0, 25 octobre 2026), l'addition de deux tenseurs `bfloat16` dans l'interpréteur ne lève **aucune exception**, mais le résultat est faux : `add` de deux tenseurs de uns a rendu des valeurs de l'ordre de $1{,}7 \cdot 10^{38}$ au lieu de 2. La documentation a donc raison, et l'absence d'erreur est le piège : convertissez en `float32` avant de calculer. Relisez la documentation de **votre** version ; `python3 probe_observations.py` (lab 4.3) refait cette observation et les deux suivantes sur votre installation.
:::

::: note
[Un masque oublié ne se voit pas toujours]{.tag} En supprimant le masque de `add_kernel` pour une longueur qui n'est pas un multiple du bloc, nous n'avons pas obtenu d'exception : l'interpréteur a lu et écrit hors du tableau et le processus Python s'est arrêté brutalement (erreur de segmentation à un essai, `Aborted` à un autre, Triton 3.8.0 ; `probe_observations.py` l'observe dans un processus fils). L'interpréteur valide la logique, il ne remplace pas la discipline des masques.
:::

### 5.5. Triton ou CUDA ?

| Situation | Choix raisonnable | Pourquoi |
|---|---|---|
| Fusionner des opérations élémentaires et des réductions | Triton | on décrit des blocs ; le compilateur gère la coalescence |
| Variante d'attention ou de normalisation absente des bibliothèques | Triton | itération rapide en Python |
| Produit matriciel standard au pic | bibliothèque (cuBLAS, CUTLASS) | réglé par le constructeur pour chaque génération |
| Contrôle fin des warps, de la mémoire partagée, des copies asynchrones | CUDA C++ | Triton cache ces choix |
| Portabilité entre constructeurs de GPU | Triton | un seul source pour plusieurs cibles (selon la prise en charge) |
| Debug sur un portable sans GPU | Triton (interpréteur) ou Numba (simulateur) | valident la logique, pas la vitesse |

Cette grille est une recommandation de ce parcours, pas une règle de NVIDIA ni de Triton. Elle se fonde sur un critère : qui sait lire et maintenir le code dans deux ans ?

::: recap
Points clés — chapitre 5

-   Triton programme des blocs : une instance traite un bloc d'éléments, le compilateur répartit sur les threads.
-   La fusion supprime les allers-retours en mémoire : le softmax en cinq opérations lit $5MN + 2M$ éléments et en écrit $3MN + 2M$, contre une lecture et une écriture de $MN$ pour le noyau fusionné (rapport proche de 4).
-   `TRITON_INTERPRET=1` valide la logique sur CPU ; il ne valide ni la vitesse, ni l'auto-réglage.
-   Triton pour les noyaux fusionnés ou sur mesure, bibliothèques pour les GEMM standard, CUDA C++ pour le contrôle fin.
:::

## 6. Précision numérique : formats, sommes, mise à l'échelle {#ch6}

Un entraînement choisit un compromis entre la vitesse, la mémoire et la fidélité des nombres. Pour un ingénieur d'infrastructure, trois situations reviennent : une perte qui devient `NaN`, des gradients qui disparaissent, et deux exécutions « identiques » qui donnent des résultats différents. Ce chapitre donne les outils pour les expliquer, avec des expériences exécutables sur un CPU.

### 6.1. Les formats

Un nombre flottant a un bit de signe, un exposant (qui fixe la plage) et une mantisse (qui fixe la précision). La précision relative d'un format vaut environ $2^{-m}$ pour $m$ bits de mantisse explicites. Le tableau vient de `torch.finfo` (PyTorch 2.14.1, 25 octobre 2026) ; les nombres de bits sont ceux des formats, vérifiés par le test `test_format_table_matches_the_bit_layouts` du lab 4.2.

~~~text
format     exp mant         eps         max   smallest normal
float32      8   23    1.19e-07   3.403e+38          1.18e-38
float16      5   10    0.000977    6.55e+04           6.1e-05
bfloat16     8    7     0.00781    3.39e+38          1.18e-38
fp8 e4m3     4    3       0.125         448            0.0156
fp8 e5m2     5    2        0.25   5.734e+04           6.1e-05
~~~

Deux conclusions. `float16` est précis (10 bits) mais étroit : maximum 65 504, plus petit normal $6{,}1 \cdot 10^{-5}$. `bfloat16` a le même exposant que `float32` (même plus petit normal) mais seulement 7 bits de mantisse. Le billet Hopper de NVIDIA décrit les deux formats FP8 : E4M3 apporte plus de précision pour moins de plage, E5M2 plus de plage pour moins de précision ; FP8 divise par deux le stockage et double le débit par rapport à FP16 ou BF16.

TF32 est un format de calcul des cœurs tensoriels : la documentation PyTorch de `set_float32_matmul_precision` indique qu'avec le réglage `"high"` les produits `float32` utilisent TensorFloat32 (10 bits de mantisse explicites) ou la somme de deux `bfloat16`, quand les algorithmes rapides existent ; `"highest"` garde `float32` (24 bits de mantisse dont 23 stockés) et `"medium"` utilise `bfloat16` (7 bits stockés).

### 6.2. L'accumulation

Le piège le plus simple : additionner beaucoup de petits nombres dans un accumulateur étroit. En `float16`, l'écart entre deux nombres représentables vaut 2 entre 2048 et 4096, donc $2048 + 1$ s'arrondit à 2048 (arrondi au pair le plus proche) et la somme ne bouge plus.

::: ex
[Exemple 6.1 — Un accumulateur FP16 qui se bloque]{.tag} Sortie capturée (`precision.py`, NumPy, `cumsum` en `float16`) : la somme de $n$ uns en `float16` vaut 1000 pour $n = 1000$, 2048 pour $n = 2048$, puis **2048 pour $n = 4096$ et pour $n = 100\,000$**. Il n'y a aucune erreur, aucun `NaN` : le résultat est faux sans le dire. C'est pourquoi les produits matriciels en précision réduite accumulent en `float32` (l'article de Micikevicius et al. recommande une arithmétique qui accumule dans des sorties en simple précision), et pourquoi les réductions d'un noyau (chapitre 3) utilisent un accumulateur `float32` même pour des entrées `float16`.
:::

### 6.3. La mise à l'échelle de la perte

Les gradients sont souvent minuscules. Micikevicius et al. (2017) notent que toute valeur de module inférieur à $2^{-24}$ devient zéro en FP16, et observent, pour les gradients des poids d'un réseau de reconnaissance vocale (figure 2b de l'article), qu'environ 5 % des valeurs ont un exposant inférieur à $-24$. Remède : multiplier la perte par un facteur $S$ avant la passe arrière, ce qui multiplie tous les gradients par $S$, puis diviser les gradients par $S$ en `float32` avant la mise à jour des poids.

Ce facteur est borné des deux côtés : trop petit, les petits gradients disparaissent ; trop grand, les grands gradients dépassent 65 504 et deviennent `inf`. Le tableau vient de gradients **synthétiques** de modules répartis uniformément en échelle logarithmique entre $2^{-30}$ et $2^0$ (ce n'est pas la distribution d'un réseau réel). Sortie capturée (`precision.py`, graine fixée) :

~~~text
== loss scaling: gradients with magnitudes in [2^-30, 2^0] cast to float16 ==
scale       zeros      inf
2^0         16.5%     0.0%
2^8          0.0%     0.0%
2^16         0.0%     0.0%
2^24         0.0%    26.8%
~~~

Sans échelle, 16,5 % des gradients synthétiques deviennent nuls. Avec $2^{24}$, plus aucun ne s'annule mais 26,8 % débordent. Comme la bonne valeur change pendant l'entraînement, PyTorch fournit [`torch.amp.GradScaler`](https://docs.pytorch.org/docs/2.14/amp.html), qui ajuste l'échelle dynamiquement ; la documentation précise que l'entraînement en précision mixte avec `float16` utilise ordinairement `autocast` et `GradScaler` ensemble. Avec `bfloat16`, dont la plage est celle de `float32`, on n'utilise en général pas de mise à l'échelle (à vérifier pour votre modèle).

### 6.4. Le coût en précision des entrées réduites

Que perd-on à arrondir les **entrées** d'un produit matriciel ? Le lab émule l'arrondi à $m$ bits de mantisse (`round_mantissa`) et calcule le produit avec une accumulation exacte. L'émulation à 7 bits reproduit exactement `bfloat16` (testé). L'émulation à 10 bits imite l'arrondi des entrées de TF32 ; ce n'est pas la sortie d'un cœur tensoriel, dont le mode d'arrondi peut différer.

~~~text
== relative error of C = round(A) @ round(B), n = 256, exact accumulation ==
tf32 (emulated, 10 bits)            2.94e-04
bfloat16 (7 bits)                   2.36e-03
2 mantissa bits (e5m2 precision)    7.50e-02
~~~

L'erreur relative suit la précision du format : environ $10^{-4}$ pour 10 bits, $2 \cdot 10^{-3}$ pour 7 bits, $7 \cdot 10^{-2}$ pour 2 bits. Elle ne dit rien de la qualité d'un entraînement, qui dépend aussi des accumulations et des normalisations : c'est la raison pour laquelle on valide un changement de précision par une courbe de perte, pas par cette erreur.

### 6.5. L'ordre des sommes et le déterminisme

L'addition flottante n'est pas associative : $(a + b) + c$ peut différer de $a + (b + c)$. Une réduction parallèle dont l'ordre varie d'une exécution à l'autre (par exemple des additions atomiques) donne donc des résultats qui varient aussi.

::: ex
[Exemple 6.2 — Vingt ordres, dix-sept résultats]{.tag} Sortie capturée (`precision.py`) : les mêmes 4096 nombres `float32`, sommés dans 20 ordres aléatoires (graine fixée), donnent **17 résultats distincts**, étalés sur 0,047 pour une somme voisine de 6534,17 ; le pire écart à la somme en `float64` est 0,033. Sur 16 384 nombres voisins de 1, la somme séquentielle en `float32` s'écarte de $3{,}1 \cdot 10^{-3}$ de la somme exacte, la somme en arbre (celle du chapitre 3) de $7{,}8 \cdot 10^{-4}$ : dans cet essai l'arbre est environ quatre fois plus précis.

Sur 20 graines essayées en relecture, l'arbre a toujours été plus précis, avec des facteurs très variables : retenez le sens de l'écart, pas le 4. Avec un ordre fixé, sa somme est de plus reproductible bit à bit.
:::

L'ordre d'addition d'un vrai GPU peut dépendre de l'ordonnancement (additions atomiques). Le simulateur de Numba ne l'a pas montré : sur 30 lancements d'une somme par `cuda.atomic.add`, nous avons obtenu un seul résultat (`python3 demo.py atomics` du lab 4.2 ; observation, pas une garantie). Il ne montre donc pas cette non-reproductibilité, et le lab la remplace par des ordres aléatoires explicites.

::: war
[Pas de reproductibilité garantie entre plateformes]{.tag} La documentation de PyTorch est claire : « Completely reproducible results are not guaranteed across PyTorch releases, individual commits, or different platforms. » Elle propose `torch.use_deterministic_algorithms()` pour préférer des algorithmes déterministes et signaler les autres par une erreur, au prix de performances. Source : [PyTorch, Reproducibility](https://docs.pytorch.org/docs/2.14/notes/randomness.html).
:::

Conséquence pour l'exploitation : une perte qui diffère légèrement après un changement de nœud, de version de bibliothèque ou de nombre de GPU n'est pas un bogue en soi. On compare des courbes avec une tolérance, et on réserve les comparaisons bit à bit à un même matériel, une même version et une graine fixée.

::: recap
Points clés — chapitre 6

-   `float16` : précis mais étroit (max 65 504) ; `bfloat16` : plage de `float32`, précision de 7 bits ; FP8 : E4M3 plus précis, E5M2 plus large.
-   Accumulez en `float32` : un accumulateur `float16` se bloque à 2048 sans erreur.
-   La mise à l'échelle de la perte déplace les gradients dans la plage de FP16 ; trop forte, elle débordera : l'échelle doit être dynamique.
-   L'addition flottante n'est pas associative : l'ordre de réduction change les bits du résultat ; un arbre fixé est reproductible et plus précis qu'une boucle.
:::

## 7. Profiler : Nsight, PyTorch Profiler et lecture d'une trace {#ch7}

Un profil répond à une seule question : où va le temps ? Ce chapitre présente les trois outils, la structure d'une trace, puis une méthode de lecture en quatre verdicts. Les verdicts sont appliqués dans le lab 4.4 à un vrai profil CPU et à des traces de type GPU **fabriquées à la main**.

### 7.1. Trois outils, trois échelles

| Outil | Échelle | Ce qu'on y lit |
|---|---|---|
| PyTorch Profiler | opérateurs PyTorch | quel opérateur, combien d'appels, quelles formes, quels FLOP, trace exportable |
| Nsight Systems (`nsys`) | tout le programme | chronologie : CPU, appels à l'API CUDA, noyaux, copies, plages NVTX (annotations posées par le programme avec la bibliothèque *NVIDIA Tools Extension*) |
| Nsight Compute (`ncu`) | un noyau | débit atteint, occupation, trafic mémoire, états des warps |

Le profileur PyTorch se pilote avec `torch.profiler.profile` ; la recette et la référence de l'API (`torch.profiler`) indiquent les activités `ProfilerActivity.CPU` et `ProfilerActivity.CUDA`, les options `record_shapes`, `with_flops` et `profile_memory`, la méthode `export_chrome_trace` et le tableau `key_averages().table(sort_by=...)`. `record_function("nom")` ajoute une annotation qui apparaît dans la trace.

Nsight Systems se lance par `nsys profile -o rapport commande` et se résume par `nsys stats rapport.nsys-rep` (guide utilisateur de Nsight Systems). Nsight Compute se lance par `ncu` ; ses options de filtrage `-k` (nom du noyau) et `-c` (nombre de lancements) limitent le profilage aux noyaux voulus (guide en ligne de commande). Ces commandes sont documentées, mais **non exécutées ici** faute de GPU.

### 7.2. Anatomie d'une trace

Une trace Chrome (`export_chrome_trace`) est un fichier JSON dont chaque événement complet porte un nom, une date de début `ts`, une durée `dur`, un processus, un fil et une catégorie `cat`. D'après le code de Kineto, la bibliothèque qui alimente le profileur PyTorch, les catégories incluent `cpu_op` (opérateur du CPU), `user_annotation`, `cuda_runtime` (appel à l'API CUDA, comme le lancement d'un noyau), `kernel` (noyau sur le GPU), `gpu_memcpy` et `gpu_memset`.

On y lit deux voies. La voie CPU montre ce que fait le programme : opérateurs, puis lancements. La voie GPU, par flux, montre ce que fait le matériel : noyaux et copies. Les **trous** de la voie GPU sont du temps perdu ; la question est ce que le CPU faisait pendant ce temps.

### 7.3. Quatre verdicts

Le script `trace_report.py` du lab calcule, pour une trace avec activité GPU : l'utilisation du GPU (durée de l'union des intervalles occupés sur la durée totale), la durée médiane des noyaux et la part des copies. Il en tire un verdict selon des seuils qui sont des **heuristiques de ce cours**.

| Signal | Verdict | Premières actions |
|---|---|---|
| copies $> 50$ % du temps GPU | **transferts** | mémoire épinglée, moins d'octets, recouvrement (chapitre 4) |
| utilisation $< 60$ % et noyau médian $< 50$ µs | **lancement** | fusion, CUDA graphs, `torch.compile`, lot plus grand |
| utilisation $\ge 85$ % | **GPU saturé** | Nsight Compute : calcul ou mémoire ? fusion, précision, FlashAttention |
| utilisation $< 85$ % sans être dans le cas « lancement » (noyaux longs, ou utilisation entre 60 et 85 %) | **mixte** | chercher les attentes du CPU : chargement, synchronisations, Python |

Quand le GPU est saturé, la trace ne suffit pas : il faut ouvrir un noyau avec Nsight Compute. Sa section « GPU Speed Of Light Throughput » donne l'utilisation du calcul et de la mémoire, avec un graphique roofline ; « Occupancy » et « Warp State Statistics » expliquent ce que font les warps. C'est le roofline du module 2, appliqué à un noyau précis.

### 7.4. Un vrai profil CPU (lab 4.4, partie A)

Le lab profile une étape (passe avant et arrière) d'un petit transformeur à 2 couches (largeur 128, séquence 64, lot 8) avec 2 threads CPU. Sortie capturée (`python3 profile_cpu.py --out trace.json`, une exécution) :

~~~text
operator                           calls  self CPU us     MFLOP
aten::mm                              16         5975     805.3
aten::addmm                            8         4142     402.7
aten::copy_                           33         2641       0.0
train_step                             1         2247       0.0
aten::bmm                             12         1776     100.7
aten::gelu                             2         1128       0.0
aten::gelu_backward                    2          970       0.0
aten::_softmax                         2          934       0.0
profiler FLOPs of mm+addmm+bmm: 1308622848 = 3.000 x analytic forward FLOPs
~~~

::: ex
[Exemple 7.1 — Vérifier un profil avec un modèle]{.tag} Les nombres d'appels découlent de l'architecture : 8 `addmm` (4 couches linéaires par bloc, 2 blocs), 16 `mm` (la passe arrière en fait deux par couche linéaire : gradient de l'entrée et des poids) et 12 `bmm` (2 produits d'attention en passe avant, 4 en passe arrière, par bloc). Les FLOP s'accordent aussi. Par bloc, $24\,BTD^2 + 4\,BT^2D$ avec $B=8$, $T=64$, $D=128$ donne 218 103 808 FLOP, soit 436 207 616 pour deux blocs ; la passe arrière en ajoute le double, d'où $3 \times 436\,207\,616 = 1\,308\,622\,848$ : exactement la valeur du profileur.

Un profil qui s'accorde avec le modèle de FLOP du module 2 est un profil auquel on peut se fier ; un écart serait le signal à explorer. Sur six exécutions de relecture, les trois opérateurs de produit matriciel ont représenté de 40 à 51 % du temps propre du CPU : la moitié environ va ailleurs, aux copies, à GELU, au softmax, à l'annotation et à de plus petits opérateurs. Ce sont les candidats à la fusion du chapitre 8.
:::

Ne retenez pas les microsecondes : elles varient d'une exécution à l'autre sur une machine partagée. Le test du lab n'affirme donc aucune durée, seulement les compteurs, les FLOP et la cohérence de l'imbrication (la somme des temps propres égale la durée de l'étape annotée).

### 7.5. Des traces de type GPU, fabriquées (lab 4.4, partie B)

Le bac à sable n'a pas de GPU. Le lab fournit donc trois fichiers `fixtures/*.json` générés par `make_fixture.py` : ils imitent la structure d'une trace de Kineto, avec des durées **choisies** pour illustrer un goulot. Ils portent `otherData.synthetic = true`. Ils servent à s'exercer à lire ; ils ne disent rien sur un GPU réel. Sortie capturée de `trace_report.py` :

| Trace (fabriquée) | Utilisation | Noyaux | Noyau médian | Copies | Verdict |
|---|---|---|---|---|---|
| `launch_bound` | 27,7 % | 200 | 5,0 µs | 0 % | lancement |
| `gpu_bound` | 99,8 % | 12 | 910,6 µs | 0 % | GPU saturé |
| `transfer_bound` | 99,1 % | 10 | 306,3 µs | 92,9 % | transferts |

::: ex
[Exemple 7.2 — Ce que le verdict permet de prévoir]{.tag} La trace `launch_bound` dure 3587 µs pour 994 µs de noyaux : si l'on supprimait tous les trous (CUDA graphs, fusion), le temps tomberait au mieux à 994 µs, un gain maximal de $3587/994 = 3{,}6$. La trace `gpu_bound` n'a presque aucun trou ($10\,877/10\,855 = 1{,}002$) : les CUDA graphs n'y apportent rien, seul l'intérieur des noyaux compte. La trace `transfer_bound` surprend : avec 40 000 µs de copies pour 3076 µs de noyaux, un recouvrement parfait ne gagnerait que $43\,076/40\,000 = 1{,}08$ ; il faut réduire la durée des copies (mémoire épinglée, moins d'octets), pas les masquer.
:::

Ces gains sont des **bornes** déduites de traces fabriquées. Leur intérêt est la méthode : transformer un verdict en un plafond de gain avant d'engager du travail.

::: recap
Points clés — chapitre 7

-   PyTorch Profiler voit les opérateurs, Nsight Systems la chronologie complète, Nsight Compute un noyau ; on descend d'un niveau seulement quand le précédent a désigné le suspect.
-   Une trace est une liste d'événements `cpu_op`, `cuda_runtime`, `kernel`, `gpu_memcpy` ; les trous de la voie GPU sont le premier indice.
-   Quatre verdicts : transferts, lancement, GPU saturé, mixte ; les seuils sont des heuristiques à ajuster.
-   Confrontez un profil à un modèle (FLOP, nombre d'appels) avant de le croire, et transformez chaque verdict en plafond de gain.
:::

## 8. Techniques d'accélération : fusion, FlashAttention, compilation, CUDA graphs {#ch8}

Le chapitre 7 a donné des verdicts ; celui-ci donne les leviers. Chaque technique traite un goulot précis. L'erreur la plus coûteuse est d'appliquer un levier sans verdict : fusionner des noyaux déjà saturés en calcul, ou capturer un graphe quand le GPU n'attend pas.

### 8.1. Quel levier pour quel verdict

| Levier | Goulot traité | Ne sert à rien si… |
|---|---|---|
| Fusion de noyaux | mémoire (trafic entre opérations) | le noyau est limité par le calcul |
| FlashAttention | mémoire (matrice d'attention en HBM) | séquences courtes, matrice petite |
| `torch.compile` | mémoire et lancement (fusion automatique, moins de Python) | graphes trop dynamiques, ruptures de graphe fréquentes |
| CUDA graphs | lancement | les noyaux sont longs, les formes changent |
| Précision réduite | calcul et mémoire | le calcul est ailleurs (E/S, communication) |
| Lot plus grand | lancement, faible utilisation | la mémoire manque, la qualité de l'entraînement dépend du lot |

### 8.2. La fusion

Le chapitre 5 a chiffré la fusion : cinq opérations de softmax deviennent un noyau, et le trafic est divisé par un facteur proche de 4. Le principe général : une chaîne d'opérations élémentaires et de réductions, toutes limitées par la mémoire, gagne à rester en registres ou en mémoire partagée. Une opération limitée par le calcul (un gros produit matriciel) ne gagne rien à être fusionnée avec ses voisines, sauf à y absorber l'activation ou le biais en sortie.

### 8.3. FlashAttention

L'attention standard calcule trois étapes, où $Q$, $K$ et $V$ sont des matrices $N \times d$ ($N$ la longueur de séquence, $d$ la dimension d'une tête) :

$$S = QK^\top, \qquad P = \mathrm{softmax}(S), \qquad O = PV$$

La matrice $S$ est de taille $N \times N$ : elle est écrite en mémoire HBM, relue par le softmax, réécrite, relue par le produit. L'article de Dao et al. (2022) la décrit comme un algorithme d'attention **exacte**, conscient des entrées-sorties (*IO-aware*), qui utilise des tuiles pour réduire les lectures et écritures entre la HBM et la SRAM sur puce, et qui recalcule les valeurs en passe arrière au lieu de les stocker.

Son analyse donne, pour une SRAM de taille $M$ avec $d \le M \le Nd$, un nombre d'accès à la HBM de $\Theta(Nd + N^2)$ pour l'attention standard et de $\Theta(N^2 d^2 M^{-1})$ pour FlashAttention, avec une mémoire supplémentaire linéaire en $N$. Les FLOP augmentent à cause du recalcul, mais le temps baisse parce que l'accès à la HBM domine. Résultats annoncés : 15 % de gain de temps total sur BERT-large (séquence 512) par rapport au record MLPerf 1.1, 3 fois sur GPT-2 (séquence 1K) et 2,4 fois sur Long Range Arena (séquences 1K à 4K).

::: ex
[Exemple 8.1 — Combien de HBM pour la matrice d'attention ?]{.tag} Prenons $N = 4096$, 32 têtes, `bfloat16` (2 octets), une couche, une séquence. La matrice $S$ pèse $4096^2 \times 32 \times 2 = 1{,}07 \cdot 10^9$ octets, soit 1 Gio. Écrite puis relue pour le softmax, puis la matrice $P$ écrite et relue pour le produit : au moins 4 passes, soit 4 Gio de trafic HBM pour la seule passe avant d'une couche. À 3,35 To/s, cela représente au moins 1,28 ms par couche, borne idéalisée.

Avec $d = 64$ et une SRAM de $M = 98\,304$ éléments (les 192 Kio par SM de l'A100 cités par l'article, comptés en nombres de 2 octets), le rapport des ordres de grandeur $(Nd + N^2) / (N^2 d^2 / M)$ vaut environ 24 ; il reste compris entre 24 et 26 pour $N$ de 1024 à 16 384.

Le $\Theta$ cache des constantes : lisez ce 24 comme un ordre de grandeur, pas comme une prédiction. L'article lui-même annonce, pour des valeurs typiques de $d$ et $M$, jusqu'à 9 fois moins d'accès à la HBM (sa figure 2), soit un facteur très inférieur à 24.
:::

Dans PyTorch, `scaled_dot_product_attention` est l'opérateur qui permet de choisir une implémentation fusionnée selon la plateforme. Le lab 4.4 montre ce que la substitution change dans un profil : avec l'attention explicite, le profil contient les appels `aten::softmax` et plus de `aten::bmm` ; avec l'opérateur fusionné, l'appel `aten::softmax` disparaît (testé sur CPU). Sur GPU, le noyau choisi dépend de votre version et de votre matériel : vérifiez-le dans votre propre trace.

### 8.4. `torch.compile`

`torch.compile` optimise une fonction ou un modèle avec TorchDynamo et un moteur de génération de code ; le moteur par défaut est `inductor`, décrit comme un bon équilibre entre performance et surcoût (documentation PyTorch 2.14). Quand une portion du code ne peut pas être capturée, la compilation retombe sur l'exécution normale : une « rupture de graphe » fait perdre une partie du bénéfice. Le paramètre `mode` propose `"default"`, `"reduce-overhead"`, `"max-autotune"` et `"max-autotune-no-cudagraphs"`.

::: war
[`reduce-overhead` n'est pas garanti]{.tag} La documentation de `torch.compile` décrit le mode `"reduce-overhead"` comme une réduction du surcoût de Python avec des CUDA graphs, utile pour les petits lots, avec une consommation mémoire accrue. Elle précise : « Reduction of overhead is not guaranteed to work; today, we only reduce overhead for CUDA only graphs which do not mutate inputs. » Source : [PyTorch, torch.compile](https://docs.pytorch.org/docs/2.14/generated/torch.compile.html).
:::

### 8.5. Les CUDA graphs

Dans un flux, chaque lancement de noyau impose au pilote du CPU une séquence d'opérations préparatoires. Le guide de programmation CUDA note que, pour un noyau de courte durée, ce surcoût peut représenter une fraction significative du temps total. Un **graphe** CUDA définit une fois un ensemble d'opérations et de dépendances, puis le lance plusieurs fois ; les coûts de lancement baissent car une grande partie de la préparation est faite à l'avance. L'article de blog de PyTorch sur le sujet présente l'effet : les trous entre noyaux courts disparaissent.

Les conditions d'emploi ne sont pas anodines : le graphe est défini une fois puis relancé, donc les formes et les adresses mémoire doivent en principe rester stables entre les lancements (à vérifier dans la documentation de votre version). Un décodage de modèle de langage dont la longueur de contexte varie à chaque pas y est mal adapté sans précautions ; l'exercice 10 chiffre l'arbitrage.

### 8.6. Quand cela ne paie pas

Une technique ne paie pas dans cinq cas : le goulot est ailleurs (vérifié par le verdict du chapitre 7), le gain maximal calculé est inférieur au coût de maintenance, les formes sont trop dynamiques, la précision réduite dégrade la convergence, ou le surcoût de compilation n'est jamais amorti sur la durée du job. Une règle d'équipe simple : toute proposition d'optimisation arrive avec un profil avant, un plafond de gain calculé, et un profil après.

::: recap
Points clés — chapitre 8

-   Chaque levier traite un goulot : fusion et FlashAttention la mémoire, CUDA graphs et lot le lancement, précision réduite le calcul et la mémoire.
-   FlashAttention est exact, conscient des IO : $\Theta(N^2 d^2 / M)$ accès HBM contre $\Theta(Nd + N^2)$, avec un recalcul en passe arrière.
-   `torch.compile` fusionne et réduit le Python, mais ses ruptures de graphe et le mode `reduce-overhead` ne sont pas garantis.
-   Les CUDA graphs exigent des formes et adresses stables ; sans verdict « lancement », ils ne servent à rien.
:::

## Labs {#labs}

Les quatre labs s'exécutent sur un portable Linux **sans GPU**. Prérequis communs : Python 3 récent (testé avec 3.13) avec `numpy`, `torch` (version CPU), `numba`, `triton` et `pytest` ; ils ont été exécutés le 25 octobre 2026 avec PyTorch 2.14.1, Numba 0.68.0 et Triton 3.8.0. `nvcc` est facultatif : s'il est installé (`apt install nvidia-cuda-toolkit`, version 12.0.140 testée), `verify.sh` compile les programmes CUDA C++, sans jamais les lancer. Chaque lab dit ce qui est **vérifié** ici et ce qui ne l'est pas.

~~~bash
python3 -m pip install numpy torch numba triton pytest
~~~

### Lab 4.1 — Le warp et la mémoire, en modèle {#lab-4-1}

::: lab

**Objectif.** Écrire vous-même le modèle de coût d'un warp (secteurs de la mémoire globale, conflits de bancs, divergence, occupation) et le valider par des tests dont vous connaissez les valeurs. **Durée.** 2,5 h (partie A : 1 h, partie B : 1,5 h). **Prérequis matériels.** Portable CPU ; `nvcc` optionnel. **Vérifié ici :** le modèle, ses 25 tests, l'échec de l'ébauche. **Non exécuté ici :** les programmes `cuda/access_patterns.cu` et `cuda/transpose.cu`, compilés seulement.

1.  Lisez `labs/gpu-programming/warp-memory-model/README.md`, puis lancez `python3 warpmodel.py report` et retrouvez les tables des chapitres 1 et 2.
2.  Lancez `WARPMODEL_MODULE=starter.warpmodel python3 -m pytest -q test_warpmodel.py` : les 25 tests échouent, c'est voulu.
3.  Partie A : dans `starter/warpmodel.py`, écrivez `divergence_cost` et `occupancy` jusqu'à faire passer leurs tests.
4.  Partie B : écrivez `sectors_touched` et `bank_conflict_degree`. Prédisez à la main le nombre de secteurs d'un pas de 4 et le degré de conflit d'un pas de 6 avant de lancer les tests.
5.  Calculez l'occupation d'un bloc de 256 threads, 128 registres et 2048 octets (`python3 warpmodel.py occupancy --threads 256 --regs 128 --smem 2048`) et comparez à l'exemple 1.2.
6.  Si `nvcc` est présent, lancez `./verify.sh` et relevez les registres de chaque noyau dans la sortie `ptxas`.

**Critère de réussite.** Sur la référence, `./verify.sh` affiche la ligne `25 passed` puis `OK warp-memory-model: reference passes, starter fails, report values as derived in the course`. Avec votre ébauche complétée, `WARPMODEL_MODULE=starter.warpmodel python3 -m pytest -q test_warpmodel.py` passe aussi : `25 passed`. Les valeurs sont exactes parce que le code est déterministe. Durée de `verify.sh` : quelques secondes.

**Pour aller plus loin.** Sur un GPU NVIDIA, lancez `access_patterns` : le programme affiche le rapport de trafic prédit par le modèle ($(4 + 4\min(p, 8))/8$ pour le pas $p$) à côté de la bande passante mesurée. Si votre GPU contredit la prédiction, c'est un résultat : cherchez le rôle du cache L2. Ce programme n'a pas été exécuté pour ce cours.
:::

### Lab 4.2 — Noyaux CUDA dans le simulateur Numba {#lab-4-2}

::: lab

**Objectif.** Écrire et tester des noyaux CUDA (réduction, scan, produit par tuiles) avec Numba dans son simulateur CPU, compter les lectures globales, provoquer les erreurs classiques et refaire les expériences de précision. **Durée.** 4 h (partie A : 1,5 h, partie B : 1,25 h, partie C : 1,25 h). **Prérequis matériels.** Portable CPU, 4 Go de mémoire ; GPU optionnel pour `bench_gpu.py`. **Vérifié ici :** noyaux, tests, compteurs, expériences de précision, compilation CUDA C++. **Non exécuté ici :** `bench_gpu.py` (octet-compilé) et les binaires CUDA.

1.  Partie A. Lisez `kernels.py`. Lancez `NUMBA_ENABLE_CUDASIM=1 python3 -m pytest -q test_kernels.py`. Ajoutez un noyau `block_max` (maximum par bloc) sur le modèle de `block_sum` et testez-le contre `np.max` par bloc.
2.  Partie B. Lancez `python3 demo.py loads` et vérifiez les trois valeurs de l'exemple 3.2. Puis `python3 demo.py errors` : relevez l'`IndexError` et le résultat de la réduction sans barrières.
3.  Partie B. Supprimez la seconde `cuda.syncthreads()` du produit à tuiles (`matmul_tiled`) et relancez `test_tiled_matmul_matches_numpy_and_naive` et `test_tiled_matmul_with_edges_not_multiple_of_the_tile` : sur la machine de rédaction, ces deux tests ont échoué à chacun de quatre essais. Expliquez quelle tuile est écrasée avant d'avoir été lue, puis restaurez le fichier.
4.  Partie C. Lancez `python3 precision.py`. Retrouvez le blocage à 2048 de l'accumulateur FP16, le tableau d'échelles et les 17 résultats distincts sur 20 ordres de somme.
5.  Partie C. Changez la graine de `order_dependence` : le nombre de résultats distincts change-t-il ? Expliquez pourquoi l'arbre reste plus précis (`tree_vs_sequential`).

**Critère de réussite.** `./verify.sh` affiche `19 passed`, puis les compteurs exacts `tile  8: 8192 loads`, `tile 16: 4096 loads` et `naive  : 65536 loads`, puis `OK numba-cuda-sim: kernels correct in the simulator, tiled loads = naive / tile`. Les compteurs sont déterministes ; le test des barrières manquantes accorde 6 essais et exige au moins un résultat faux (nous avons observé 5 sur 5). Durée : environ 30 secondes sur 4 vCPU.

**Pour aller plus loin.** Sur un GPU NVIDIA, lancez `NUMBA_ENABLE_CUDASIM=0 python3 bench_gpu.py` et placez les trois points (naïf, tuilé, `torch.matmul`) sur le roofline du module 2. Compilez et lancez `cuda/streams_overlap.cu` et comparez les quatre configurations à l'exemple 4.1. Ces deux programmes n'ont pas été exécutés pour ce cours.
:::

### Lab 4.3 — Triton en mode interpréteur {#lab-4-3}

::: lab

**Objectif.** Écrire et déboguer des noyaux Triton (addition fusionnée, softmax, produit par tuiles) avec `TRITON_INTERPRET=1`, et chiffrer le trafic mémoire que la fusion évite. **Durée.** 3 h. **Prérequis matériels.** Portable CPU ; GPU optionnel. **Vérifié ici :** correction des noyaux et décompte du trafic (Triton 3.8.0, 25 octobre 2026). **Non exécuté ici :** vitesse et auto-réglage (`bench_gpu.py`, octet-compilé seulement).

1.  Lisez `labs/gpu-programming/triton-interpret/triton_kernels.py` ; repérez le masque de chaque noyau et la constante `BLOCK_SIZE`.
2.  Lancez `TRITON_INTERPRET=1 python3 -m pytest -q test_triton_kernels.py`.
3.  Ajoutez un `print(x)` dans `softmax_kernel` (autorisé dans l'interpréteur) et relevez les valeurs d'une ligne de 7 colonnes.
4.  Supprimez le masque de `add_kernel` et lancez `TRITON_INTERPRET=1 python3 -m pytest -q -k add_is_exact test_triton_kernels.py`. Sur la machine de rédaction (Triton 3.8.0), le processus s'est arrêté brutalement (`Fatal Python error: Segmentation fault` à un essai, `Fatal Python error: Aborted` à l'autre) au lieu de lever une exception, car l'interpréteur accède réellement à la mémoire hors du tableau. Expliquez pourquoi un masque est indispensable, puis restaurez le fichier.
5.  Lancez `python3 traffic.py 4096 2048` et retrouvez $5MN + 2M$ et $3MN + 2M$ ; lancez-le pour $M = N = 1024$.
6.  Décorez `add_kernel` avec `@triton.autotune` et notez l'erreur. Lancez ensuite `python3 probe_observations.py` : il refait les observations sur `bfloat16`, l'auto-réglage et le masque absent, sans rien affirmer.

**Critère de réussite.** `./verify.sh` affiche `13 passed`, puis `reads 41951232 elements` et `writes 25174016 elements` (déterministes), un rapport de trafic compris entre 3,9 et 4,1 (la sortie du bac à sable : `x4.001`), puis `OK triton-interpret: kernels correct under TRITON_INTERPRET=1, unfused/fused traffic ratio = 4.00`. Durée : environ 10 secondes.

**Pour aller plus loin.** Sur un GPU, lancez `bench_gpu.py` : si le softmax est limité par la bande passante, le rapport des temps du noyau fusionné et des cinq opérations devrait s'approcher du rapport de trafic (environ 4), moins le coût fixe des lancements : c'est l'hypothèse du modèle, à confronter à la mesure. Ce programme n'a pas été exécuté pour ce cours.
:::

### Lab 4.4 — Lire une trace de profil {#lab-4-4}

::: lab

**Objectif.** Profiler un petit transformeur sur CPU avec PyTorch Profiler, vérifier le profil avec un modèle de FLOP, puis lire des traces de type GPU et en tirer un verdict. **Durée.** 3 h (partie A : 1,5 h, partie B : 1,5 h). **Prérequis matériels.** Portable CPU, 2 cœurs libres. **Vérifié ici :** le profil CPU, l'analyseur de trace et ses verdicts. **Fabriqué à la main, non mesuré :** les trois traces `fixtures/*.json`, qui n'apportent aucune information sur un vrai GPU.

1.  Partie A. Lisez `tiny_model.py`, puis lancez `python3 profile_cpu.py --out trace.json` et ouvrez `trace.json` dans un visualiseur de traces Chrome (par exemple Perfetto ou `chrome://tracing`).
2.  Partie A. Lancez `python3 trace_report.py trace.json` et comparez le temps propre à la durée de l'étape annotée `train_step`.
3.  Partie A. Relancez avec `--attention sdpa` et listez les opérateurs qui disparaissent (exemple 7.1 et § 8.3).
4.  Partie B. Lancez `python3 trace_report.py` sur chaque fichier de `fixtures/` et reconstituez le tableau du § 7.5.
5.  Partie B. Modifiez `make_fixture.py` pour fabriquer un quatrième scénario « mixte » (noyaux longs, trous causés par un chargement de données) et vérifiez que le verdict est `MIXED`.
6.  Rédigez en cinq lignes, pour chaque trace, le plafond de gain et la première action.

**Critère de réussite.** `./verify.sh` affiche `13 passed`, la ligne `profiler FLOPs of mm+addmm+bmm: 1308622848 = 3.000 x analytic forward FLOPs` (exacte), les trois verdicts `LAUNCH-BOUND`, `GPU-BOUND` et `TRANSFER-BOUND`, puis `OK profile-reading: profiler FLOPs = 3 x forward, verdicts launch/gpu/transfer-bound on the synthetic traces`. Aucun temps n'est testé. Durée : environ 10 secondes.

**Pour aller plus loin.** Sur un nœud GPU, remplacez `ProfilerActivity.CPU` par `[CPU, CUDA]`, ou lancez `nsys profile -o rapport python train.py`, puis `nsys stats rapport.nsys-rep` ; ouvrez ensuite le noyau dominant avec `ncu -k regex:gemm -c 1 -o noyau python train.py`. Ces commandes sont documentées dans les guides NVIDIA mais n'ont pas été exécutées pour ce cours.
:::

## Exercices {#ex}

::: exo
[Exercice 1 · ★ — L'occupation d'un noyau]{.tag} Un noyau utilise des blocs de 192 threads, 40 registres par thread et 20 Kio de mémoire partagée par bloc. Les limites par SM sont celles de la capacité de calcul 8.0 : 2048 threads, 64 warps, 32 blocs, 65 536 registres et 164 Kio de mémoire partagée. Avec le modèle simplifié du chapitre 1 (sans granularité d'allocation), calculez le nombre de blocs résidents permis par chaque ressource, l'occupation et la ressource limitante. Gagneriez-vous quelque chose en ramenant les registres à 32 ?
:::

::: sol
Par les threads : $\lfloor 2048/192 \rfloor = 10$. Par les blocs : 32. Par les registres :

$$\Bigl\lfloor \frac{65\,536}{40 \times 192} \Bigr\rfloor = \lfloor 8{,}53 \rfloor = 8$$

Par la mémoire partagée : $\lfloor 164/20 \rfloor = \lfloor 8{,}2 \rfloor = 8$. Le minimum est 8 blocs, soit $8 \times 6 = 48$ warps sur 64 : **75 %**. Les registres et la mémoire partagée limitent **ex æquo**.

Vérification : `python3 warpmodel.py occupancy --threads 192 --regs 40 --smem 20480` affiche `blocks/SM=8 warps/SM=48 occupancy=75.0%`.

Ramener les registres à 32 porterait la limite des registres à $\lfloor 65\,536/(32 \times 192) \rfloor = 10$ blocs, mais la mémoire partagée reste à 8 : aucun gain. Il faudrait réduire les deux ressources à la fois.
:::

::: exo
[Exercice 2 · ★ — Tableau de structures ou structure de tableaux]{.tag} Un noyau lit uniquement le champ `x` de $2^{22}$ particules rangées en tableau de structures de 32 octets (8 `float`). (a) Combien de secteurs de 32 octets un warp touche-t-il, et pour un tableau de `x` contigus ? (b) Quel trafic mémoire cela représente-t-il dans chaque cas ? (c) Quelle durée minimale à 3,35 To/s ? Précisez ce que cette borne néglige.
:::

::: sol
(a) Les 32 lanes lisent des adresses espacées de 32 octets, soit un secteur chacune : 32 secteurs pour le tableau de structures (rendement de 12,5 %) contre 4 secteurs pour des `x` contigus (100 %). Le modèle le confirme avec `sectors_touched(aos_field_addresses(32))`.

(b) Pour $2^{22} = 4\,194\,304$ particules : $4\,194\,304 \times 32 = 134\,217\,728$ octets (134 Mo) contre $4\,194\,304 \times 4 = 16\,777\,216$ octets (16,8 Mo).

(c) $134{,}2 \cdot 10^{6}/3{,}35 \cdot 10^{12} = 40{,}1$ µs contre $5{,}0$ µs : un facteur 8. La borne néglige les caches (qui peuvent réutiliser les secteurs si les autres champs sont lus ensuite), la latence et le coût de lancement.
:::

::: exo
[Exercice 3 · ★★ — Le produit à tuiles de grande taille]{.tag} On multiplie deux matrices carrées de côté $N = 4096$ en `float32`. Rappel du chapitre 3 : un noyau naïf lit $2N^3$ valeurs en mémoire globale, un noyau à tuiles de côté $T$ en lit $2N^3/T$, et le produit fait $2N^3$ FLOP.

(a) Donnez le nombre de FLOP. (b) Donnez les octets lus par le noyau naïf, puis par un noyau à tuiles de 16 et de 32. (c) Donnez l'intensité arithmétique de chaque cas. (d) Donnez le temps minimal imposé par la mémoire à 3,35 To/s. (e) Pourquoi une tuile de 64 est-elle impossible avec un élément du résultat par thread ?
:::

::: sol
(a) $2N^3 = 2 \times 4096^3 = 1{,}374 \cdot 10^{11}$ FLOP, soit 137,4 GFLOP.

(b) Naïf : $1{,}374 \cdot 10^{11}$ valeurs $\times$ 4 octets = 549,8 Go. $T = 16$ : $8{,}59 \cdot 10^{9}$ valeurs, 34,4 Go. $T = 32$ : $4{,}29 \cdot 10^{9}$ valeurs, 17,2 Go.

(c) Intensité $= 2N^3/(4 \times 2N^3/T) = T/4$ pour les tuiles : 4 FLOP/octet pour $T = 16$, 8 pour $T = 32$, contre 0,25 pour le naïf.

(d) $549{,}8/3350 = 164$ ms, $34{,}4/3350 = 10{,}3$ ms et $17{,}2/3350 = 5{,}1$ ms. Ce sont des bornes idéalisées, sans caches.

(e) Avec $T = 64$ il faudrait $64^2 = 4096$ threads par bloc, or un bloc en compte au plus 1024. La mémoire partagée ($2 \times 64^2 \times 4 = 32$ Kio) ne serait pas le problème.
:::

::: exo
[Exercice 4 · ★★★ — Diagnostiquer un noyau qui se trompe]{.tag} Un collègue lance les deux noyaux du lab 4.2 dans le simulateur et vous envoie ce résultat de `python3 demo.py errors` :

~~~text
unguarded kernel: IndexError -> tid=[44, 0, 0] ctaid=[1, 0, 0]: index 108 is out of bounds for axis 0
reduction without barriers: 5 wrong results out of 5 launches
~~~

(a) Dites la cause de chaque ligne et corrigez-la en citant la ligne de `kernels.py` concernée. (b) Pour $n = 1000$ et des blocs de 256 threads, combien de threads sont en trop et combien d'octets le noyau sans garde-fou écrit-il après la fin du tableau de sortie `float32` ? (c) Que se passerait-il sur un vrai GPU, et quel outil utiliseriez-vous ? (d) Pourquoi ne peut-on pas conclure qu'un noyau est correct parce que le simulateur ne se plaint pas ?
:::

::: sol
(a) Ligne 1 : le noyau `vec_add_unguarded` ne teste pas `i < c.shape[0]` ; le thread 44 du bloc 1 (index global $64 + 44 = 108$ avec des blocs de 64) dépasse un tableau de 100 éléments. Correction : le test de `vec_add` (`if i < c.shape[0]:`). Ligne 2 : `block_sum(sync=False)` lit la mémoire partagée avant que les autres threads l'aient écrite et entre les tours de l'arbre. Correction : les deux `cuda.syncthreads()` de `block_sum`, placées **hors** de tout `if`.

(b) $\lceil 1000/256 \rceil = 4$ blocs, 1024 threads : 24 en trop. Chacun écrit un `float32` : 96 octets après la fin de la sortie (et lit 96 octets après la fin de chaque entrée).

(c) Sur un vrai GPU, il n'y a pas d'exception : l'écriture hors tableau corrompt silencieusement la mémoire voisine, ou provoque une erreur d'accès illégal signalée plus tard (les erreurs sont asynchrones : § 4.1, lu à la séance suivante). La documentation de Triton recommande `compute-sanitizer` pour contrôler les courses de données et les accès mémoire sur GPU NVIDIA.

(d) Le simulateur ne modélise pas les warps et ordonne ses threads comme le système ; il attrape les accès hors bornes sur des tableaux NumPy, pas toutes les courses. Une absence de plainte prouve peu : il faut des tests sur plusieurs tailles et un outil de contrôle sur GPU.
:::

::: exo
[Exercice 5 · ★★ — Découper un transfert en morceaux]{.tag} Un traitement a pour durées, sur le tampon entier, $t_{in} = 24$ ms (copie vers le GPU), $t_k = 18$ ms (noyau) et $t_{out} = 12$ ms (copie retour). On le découpe en $c$ morceaux sur trois flux, depuis de la mémoire épinglée. Rappel du chapitre 4 :

$$T(c) = \frac{t_{in} + t_k + t_{out}}{c} + \frac{c-1}{c}\max(t_{in}, t_k, t_{out})$$

(a) Calculez $T(c)$ pour $c = 1, 3, 6, 12$. (b) Simplifiez $T(c)$ pour ces durées. (c) Quel $c$ minimal donne une durée à moins de 10 % de la borne ? (d) Si chaque morceau ajoute un coût fixe de 0,05 ms (hypothèse d'énoncé), quel $c$ minimise la durée et que vaut-elle ?
:::

::: sol
(a) La somme vaut 54 ms et le maximum 24 ms. $T(1) = 54$ ms, $T(3) = 18 + \frac{2}{3} \times 24 = 34$ ms, $T(6) = 9 + \frac{5}{6} \times 24 = 29$ ms, $T(12) = 4{,}5 + \frac{11}{12} \times 24 = 26{,}5$ ms.

(b) $T(c) = 24 + 30/c$ : le maximum plus (somme moins maximum) divisé par $c$.

(c) On veut $T \le 1{,}1 \times 24 = 26{,}4$ ms, soit $30/c \le 2{,}4$, donc $c \ge 12{,}5$ : $c = 13$ ($T = 26{,}3$ ms).

(d) $T(c) = 24 + 30/c + 0{,}05\,c$ est minimal pour $c = \sqrt{30/0{,}05} \approx 24{,}5$ ; en entiers, $c = 24$ ou $25$ donne $26{,}45$ ms. Avec ce coût fixe, on **ne peut plus** passer sous 26,4 ms : le gain marginal du découpage s'annule vers $c \approx 25$. Le coût fixe réel se mesure ; l'hypothèse sert à montrer qu'il existe un optimum.
:::

::: exo
[Exercice 6 · ★★ — Le softmax fusionné en bfloat16]{.tag} On applique un softmax par ligne à une matrice $8192 \times 4096$ en `bfloat16` (2 octets par élément) sur un GPU de 3,35 To/s. Rappel du chapitre 5 : cinq opérations séparées lisent $5MN + 2M$ éléments et en écrivent $3MN + 2M$ ; le noyau fusionné lit $MN$ et écrit $MN$. (a) Calculez le trafic de chaque version et le rapport. (b) Donnez les durées minimales. (c) Un noyau fusionné atteint 70 % de la bande passante : quelle durée ? (d) Une mesure donne 90 µs : quelle fraction de la bande passante cela représente-t-il, et que concluez-vous ?
:::

::: sol
(a) Non fusionné : $(8MN + 4M) \times 2 = 536\,936\,448$ octets (536,9 Mo). Fusionné : $2MN \times 2 = 134\,217\,728$ octets (134,2 Mo). Rapport : 4,0005.

(b) $536{,}9 \cdot 10^{6}/3{,}35 \cdot 10^{12} = 160{,}3$ µs et $134{,}2 \cdot 10^{6}/3{,}35 \cdot 10^{12} = 40{,}1$ µs.

(c) $40{,}1/0{,}7 = 57{,}2$ µs.

(d) $134{,}2 \cdot 10^{6}/90 \cdot 10^{-6} = 1{,}49$ To/s, soit 44,5 % de 3,35 To/s. Le noyau est loin de la borne : on cherche des accès non coalescés, une occupation basse ou une `BLOCK_SIZE` mal choisie (auto-réglage), à confirmer avec Nsight Compute. Le noyau peut aussi être limité par le lancement si la matrice est petite : ici 40 µs de borne est assez court pour que le coût de lancement compte.
:::

::: exo
[Exercice 7 · ★★ — Choisir l'échelle de perte]{.tag} Les gradients d'un modèle ont des modules compris entre $3 \cdot 10^{-9}$ et $2 \cdot 10^{-2}$. En FP16, le plus petit nombre positif représentable est $2^{-24} \approx 5{,}96 \cdot 10^{-8}$, le plus petit nombre normal $2^{-14} \approx 6{,}1 \cdot 10^{-5}$ et le plus grand 65 504. (a) Quelles puissances de 2 comme facteur d'échelle $S$ évitent l'annulation du plus petit gradient et le débordement du plus grand ? (b) Même question en exigeant que le plus petit gradient reste dans la plage des nombres normaux. (c) Proposez une stratégie dynamique et dites pourquoi elle est préférable à une valeur fixe.
:::

::: sol
(a) Il faut que le plus petit gradient atteigne le plus petit nombre positif, et que le plus grand reste sous le maximum :

$$3 \cdot 10^{-9} \, S \ge 2^{-24} \;\Rightarrow\; S \ge 19{,}9 \;\Rightarrow\; S \ge 2^5 = 32$$

$$2 \cdot 10^{-2} \, S \le 65\,504 \;\Rightarrow\; S \le 3{,}28 \cdot 10^{6} \;\Rightarrow\; S \le 2^{21} = 2\,097\,152$$

La valeur $2^{22}$ dépasse. Les facteurs de $2^5$ à $2^{21}$ conviennent.

(b) Pour des nombres normaux : $S \ge 2^{-14}/(3 \cdot 10^{-9}) = 20\,345$, donc $S \ge 2^{15} = 32\,768$. La plage devient $2^{15}$ à $2^{21}$.

(c) Les modules changent pendant l'entraînement et les gradients accumulés sur plusieurs micro-lots peuvent dépasser un gradient isolé. Stratégie : partir d'une échelle élevée ; si un gradient contient `inf` ou `NaN`, sauter le pas et diviser l'échelle par 2 ; après un nombre fixé de pas sans incident, la doubler. C'est le principe de `torch.amp.GradScaler`. Une valeur fixe ne suit pas la dérive des modules.
:::

::: exo
[Exercice 8 · ★★ — Lire la sortie de l'analyseur de trace]{.tag} Voici la sortie de `trace_report.py` sur la trace **fabriquée** `fixtures/launch_bound.json` :

~~~text
600 complete events in fixtures/launch_bound.json
operator                           calls    self us   share
aten::mul                            200     1400.0  100.0%
GPU: span 3587 us, busy 994 us, utilization 27.7 %
GPU: 200 kernels, median 5.0 us, copies 0.0 % of device time
VERDICT: LAUNCH-BOUND: many short kernels and an idle device (fuse, CUDA graphs, torch.compile, bigger batch)
~~~

(a) Expliquez le verdict avec les nombres imprimés. (b) Quel est le gain maximal de la suppression des trous ? (c) Quelle durée moyenne s'écoule par noyau et quelle est la part du GPU ? (d) Proposez deux actions, dites laquelle essayer d'abord et ce que vous mesureriez après.
:::

::: sol
(a) Le GPU n'est occupé que 27,7 % du temps (utilisation $< 60$ %) et le noyau médian dure 5,0 µs ($< 50$ µs) : beaucoup de noyaux très courts séparés par des trous, c'est un goulot de lancement.

(b) $3587/994 = 3{,}61$ : en supprimant tous les trous sans changer les noyaux, la durée tomberait au mieux à 994 µs.

(c) $3587/200 = 17{,}9$ µs par noyau, dont 5,0 µs de calcul sur le GPU (utilisation 27,7 %).

(d) Fusionner les 200 multiplications élémentaires (par `torch.compile`, ou un noyau Triton) ou capturer la séquence dans un CUDA graph. Essayez d'abord la fusion : elle supprime les lancements **et** le trafic mémoire intermédiaire, donc elle peut dépasser la borne de 3,6 du graphe. Après, refaites la trace : utilisation, nombre de noyaux, durée de l'étape, et vérifiez que les résultats restent dans la tolérance. Les valeurs viennent d'une trace fabriquée : sur une vraie trace, relisez d'abord le profil.
:::

::: exo
[Exercice 9 · ★★★ — Dimensionner la tuile d'une transposition]{.tag} Le noyau `transpose_tiled` du lab 4.1 utilise 24 registres par thread (sortie de `nvcc`, § 2.3). Version A : tuile de 32 sur 32 avec une colonne de remplissage (`tile[32][33]`, 4224 octets), blocs de 32 sur 8, soit 256 threads.

Version B proposée par un collègue : tuile de 64 sur 64 (`tile[64][64 + pad]`), blocs de 64 sur 16, soit 1024 threads, même nombre de registres.

(a) Calculez l'occupation de A et de B (capacité 8.0) avec un remplissage de 1. (b) Le thread $k$ d'un warp lit `tile[k][c]` : donnez le degré de conflit pour B sans remplissage et avec un remplissage de 1. (c) Donnez le degré de conflit de la tuile de 32 de large pour un remplissage de 0, 1, 2, 3 et 4, et la règle générale. (d) Recommandation et ce que vous mesureriez.
:::

::: sol
(a) A : 8 blocs par les threads, 10 par les registres ($65\,536/(24 \times 256)$), 39 par la mémoire partagée : 8 blocs, 64 warps, **100 %**. B : $64 \times 65 \times 4 = 16\,640$ octets ; 2 blocs par les threads, 2 par les registres ($65\,536/(24 \times 1024) = 2{,}67$), 10 par la mémoire partagée : 2 blocs, 64 warps, **100 %** (`python3 warpmodel.py occupancy --threads 1024 --regs 24 --smem 16640`).

(b) Le pas entre threads vaut 64 mots pour $pad = 0$ : degré **32**. Avec $pad = 1$ : 65 mots, degré **1**.

(c) Largeur 32 : pas de 32, 33, 34, 35, 36 mots, soit des degrés **32, 1, 2, 1, 4**. Règle : pour un pas $p$, le degré vaut $\gcd(p, 32)$ (vérifié par le modèle pour $p$ de 1 à 128) ; un pas impair est sans conflit.

(d) Les deux versions atteignent 100 % d'occupation et A utilise 33 792 octets par SM ($8 \times 4224$) contre 33 280 pour B ($2 \times 16\,640$) : aucune raison de préférer B sur ces seuls critères. On garde A (plus simple, mieux répartie sur de petites matrices) et on mesure les deux avec `transpose.cu` sur GPU : débit en Go/s, conflits de bancs et efficacité des accès globaux avec Nsight Compute. Le modèle élimine les mauvaises options, il ne choisit pas la meilleure.
:::

::: exo
[Exercice 10 · ★★★ — Arbitrer CUDA graphs, fusion et lot sur un décodage]{.tag} Un service de génération de texte décode un token par passe : 32 couches de 12 noyaux, soit 384 noyaux par token.

**Hypothèses d'énoncé, à mesurer sur le vrai service :** chaque noyau dure 4 µs sur le GPU et le CPU a besoin de 6 µs pour en lancer un ; le CPU peut préparer les lancements en avance, donc la durée d'un token est le maximum du temps CPU et du temps GPU.

(a) Calculez le débit en tokens par seconde. (b) Même calcul avec un CUDA graph (coût de lancement du graphe négligé). (c) Même calcul si une compilation fusionne les noyaux à 5 par couche (durée moyenne conservée à 4 µs), avec puis sans graph. (d) Classez les options par gain et par risque, et dites ce que vous mesurez avant de choisir.
:::

::: sol
(a) CPU : $384 \times 6 = 2304$ µs ; GPU : $384 \times 4 = 1536$ µs. Le CPU limite : 2304 µs par token, soit **434 tokens/s**. Le verdict est « lancement ».

(b) Avec un graphe, le coût CPU disparaît : 1536 µs, soit **651 tokens/s** (gain 1,5).

(c) Avec 5 noyaux par couche : $160$ noyaux, CPU 960 µs, GPU 640 µs. Sans graphe : 960 µs, soit **1042 tokens/s** (gain 2,4). Avec graphe : 640 µs, soit **1562 tokens/s** (gain 3,6).

(d) Gain croissant : graphe (1,5), fusion (2,4), fusion et graphe (3,6). Risque : le graphe suppose des formes et adresses stables, ce qui est délicat quand le cache clé-valeur grandit à chaque pas ; `torch.compile` en mode `reduce-overhead` n'est pas garanti (§ 8.4) ; la fusion demande de la validation numérique.

On mesure d'abord le vrai profil : durée réelle des noyaux et du lancement, utilisation du GPU, nombre de ruptures de graphe, et on vérifie que la durée d'un noyau fusionné est bien celle supposée (4 µs est une hypothèse optimiste). Un lot plus grand allonge les noyaux et réduit le poids relatif du lancement, au prix de la latence par requête.
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux calculer l'occupation d'un noyau et nommer sa ressource limitante.** Preuve : l'exercice 1 refait avec les sorties `ptxas` d'un noyau de votre choix.
-   **Je peux prédire la perte due à une mauvaise coalescence ou à des conflits de bancs.** Preuve : le modèle du lab 4.1 complété et l'exercice 9.
-   **Je peux écrire et tester un noyau avec mémoire partagée.** Preuve : le noyau `block_max` de la partie A du lab 4.2 avec ses tests.
-   **Je peux chiffrer un recouvrement de transferts et de calcul.** Preuve : l'exercice 5 refait avec vos propres durées.
-   **Je peux lire un noyau Triton et chiffrer ce que la fusion économise.** Preuve : le lab 4.3 et l'exercice 6.
-   **Je peux expliquer un défaut numérique.** Preuve : l'accumulateur FP16 bloqué à 2048 et l'exercice 7.
-   **Je peux lire une trace et en tirer un verdict et un plafond de gain.** Preuve : le lab 4.4 et l'exercice 8, refaits sur une trace de votre choix.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Un entraînement affiche une utilisation GPU élevée mais un MFU faible. Que regardez-vous ?* Réponse-type : « utilisation » mesure que le GPU a un noyau en cours, pas que ce noyau est efficace. Chercher dans le profil les noyaux dominants, puis, avec Nsight Compute, leur débit de calcul et de mémoire (roofline) ; vérifier les formats (FP32 au lieu de BF16, TF32 désactivé), les noyaux limités par la mémoire à fusionner et l'attention (FlashAttention).
2.  *Pourquoi deux exécutions identiques donnent-elles une perte légèrement différente ?* Réponse-type : l'addition flottante n'est pas associative et l'ordre des réductions parallèles (atomiques, ordonnancement) varie ; des algorithmes non déterministes peuvent aussi être choisis. On fixe graines et algorithmes déterministes pour déboguer, on compare des courbes avec une tolérance, et on n'attend pas de reproductibilité bit à bit entre plateformes.
3.  *Un décodage de modèle de langage ne dépasse pas N tokens par seconde alors que le GPU semble peu chargé. Que faites-vous ?* Réponse-type : suspecter le lancement. Trace : noyaux courts et trous. Plafond de gain calculé, puis fusion, CUDA graphs ou `torch.compile`, en vérifiant les contraintes de formes ; sinon, augmenter le lot de requêtes.

## Lectures et références {#refs}

-   NVIDIA. [*CUDA Programming Guide*](https://docs.nvidia.com/cuda/cuda-programming-guide/index.html), v13.4.2. Lu le 25 octobre 2026. Chapitres 1 et 2 pour les blocs, warps et flux (chapitres 1 et 4 du module) ; annexe 5.1 pour les limites par SM.
-   NVIDIA. [*CUDA C++ Best Practices Guide*](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html). Consulté le 25 octobre 2026. Les sections sur la coalescence, la mémoire partagée et les bancs, l'occupation, la divergence et la mémoire épinglée (chapitres 1, 2 et 4).
-   NVIDIA. [*NVIDIA Hopper Architecture In-Depth*](https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth/), blog technique, 22 mars 2022. Nombre de SM, mémoire partagée, cache L2, formats FP8 (chapitres 2 et 6).
-   NVIDIA. [*Nsight Compute, Profiling Guide*](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html) et [*Command Line Interface*](https://docs.nvidia.com/nsight-compute/NsightComputeCli/index.html). Consultés le 25 octobre 2026. Sections Speed Of Light, Occupancy, Warp State ; filtres `-k` et `-c` (chapitre 7).
-   NVIDIA. [*Nsight Systems, User Guide*](https://docs.nvidia.com/nsight-systems/UserGuide/index.html). Consulté le 25 octobre 2026. `nsys profile`, `nsys stats`, NVTX (chapitre 7).
-   Numba. [*The CUDA Simulator*](https://numba.readthedocs.io/en/stable/cuda/simulator.html). Consulté le 25 octobre 2026. Fonctions prises en charge et limites : à lire avant le lab 4.2.
-   Tillet, Kung, Cox. [*Triton: An Intermediate Language and Compiler for Tiled Neural Network Computations*](http://www.eecs.harvard.edu/~htk/publication/2019-mapl-tillet-kung-cox.pdf). MAPL 2019. L'origine des idées de Triton (chapitre 5).
-   Triton. [Tutoriel *Fused Softmax*](https://triton-lang.org/main/getting-started/tutorials/02-fused-softmax.html) et [*Debugging*](https://triton-lang.org/main/programming-guide/chapter-3/debugging.html). Consultés le 25 octobre 2026. Le décompte du trafic et l'interpréteur (chapitre 5, lab 4.3).
-   Dao, Fu, Ermon, Rudra, Ré. [*FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness*](https://arxiv.org/abs/2205.14135). 2022. Théorèmes 1 et 2, résultats de la section 4 (chapitre 8).
-   Micikevicius et al. [*Mixed Precision Training*](https://arxiv.org/abs/1710.03740). 2017. Copie maîtresse en simple précision, mise à l'échelle de la perte (chapitre 6).
-   PyTorch. [*Profiler recipe*](https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html) et [*torch.profiler*](https://docs.pytorch.org/docs/2.14/profiler.html) (référence de l'API, option `with_flops`). Consultés le 25 octobre 2026. `profile`, `record_function`, `key_averages`, export de trace (chapitre 7, lab 4.4).
-   PyTorch. [*torch.compile*](https://docs.pytorch.org/docs/2.14/generated/torch.compile.html), PyTorch 2.14, consulté le 25 octobre 2026. Modes et limites (chapitre 8).
-   PyTorch. [*Reproducibility*](https://docs.pytorch.org/docs/2.14/notes/randomness.html), PyTorch 2.14, consulté le 25 octobre 2026. Ce que PyTorch garantit et ne garantit pas (chapitre 6).
-   Nguyen et al. [*Accelerating PyTorch with CUDA Graphs*](https://pytorch.org/blog/accelerating-pytorch-with-cuda-graphs/). 2021. Pourquoi les graphes réduisent les trous entre noyaux courts (chapitre 8).
-   PyTorch Kineto. [*ActivityType.h*](https://raw.githubusercontent.com/pytorch/kineto/main/libkineto/include/ActivityType.h), branche `main`, consulté le 25 octobre 2026. Les noms de catégories d'une trace (chapitre 7).

## Sources et portée {#sources}

### Documenté {#documente}

Les faits attribués aux sources ont été relus à la source le 25 octobre 2026 : guide de programmation CUDA v13.4.2 (warps de 32 threads, masquage SIMT, absence de garantie d'ordonnancement entre blocs, limites de la capacité 8.0, asynchronisme, mémoire épinglée requise pour les copies asynchrones, surcoût de lancement et graphes), guide des bonnes pratiques (coalescence en secteurs de 32 octets, 32 bancs, définitions d'occupation, de divergence, remplissage d'une colonne, exemple de 12 Go/s en mémoire épinglée), billet Hopper (132 SM, 50 Mo de L2, 256 Kio combinés, formats FP8), guides Nsight Compute et Nsight Systems (sections, options), documentation du simulateur de Numba, du débogage et de l'auto-réglage de Triton, tutoriel de softmax fusionné, article de Triton, article de FlashAttention (théorèmes, résultats), article de précision mixte, documentation de PyTorch (profileur, précision des produits, `torch.compile`, reproductibilité, exécution asynchrone), billet sur les CUDA graphs et catégories de Kineto. Tous les nombres calculés des exemples et des corrigés ont été refaits en Python. Les sorties capturées viennent d'un portable de rédaction (Linux, 4 vCPU, sans GPU) avec PyTorch 2.14.1 CPU, Numba 0.68.0, Triton 3.8.0, `nvcc` 12.0.140 en compilation seule ; les labs ont été exécutés le 25 octobre 2026.

### Recommandé {#recommande}

L'ordre des chapitres et les durées, la grille Triton, bibliothèque ou CUDA, les quatre verdicts de lecture de trace et leurs seuils (50 µs, 60 %, 85 %, 50 %), l'usage de bornes de gain avant toute optimisation et la règle « profil avant, plafond calculé, profil après » sont des choix de ce parcours, pas des règles des constructeurs. Les hypothèses chiffrées des exercices 5 et 10 sont des données d'énoncé.

### À vérifier {#a-verifier}

**Aucun programme de ce module n'a tourné sur un GPU** : les fichiers `cuda/*.cu` ont seulement été compilés, `bench_gpu.py` seulement octet-compilé, et toutes les prédictions de vitesse (rapports de trafic de 4 et de 4,5, gains de recouvrement, rapport d'environ 24 de FlashAttention tiré de formules en $\Theta$) sont des bornes de modèle à confronter à une mesure. Les commandes `nsys` et `ncu` des chapitres 7 et du lab 4.4 sont documentées mais non exécutées ; leurs options varient selon les versions. Le tableau des limites par SM du guide CUDA a été lu ; seules les valeurs de la capacité 8.0 servent aux calculs, et les colonnes du texte extrait sont parfois fusionnées (nombre de blocs résidents par SM) : relisez le tableau de votre capacité de calcul. Les 228 Kio de mémoire partagée de la capacité 9.0 sont ceux du tableau des capacités de mémoire partagée du même guide. La largeur d'exposant et le mode d'arrondi de TF32, le nombre de moteurs de copie d'un GPU donné, la nécessité de formes et d'adresses stables pour un CUDA graph, les noms des options d'épinglage de PyTorch, l'absence de mise à l'échelle avec `bfloat16` et le surcoût du profilage n'ont pas été relus à la source. La documentation de Triton annonce que l'interpréteur ne gère pas `bfloat16` ; notre essai (Triton 3.8.0) n'a pas levé d'exception mais a rendu des valeurs fausses (observation d'une version, refaite par `probe_observations.py`). L'échec de `@triton.autotune` dans l'interpréteur et l'arrêt brutal sans masque sont aussi des observations d'une version. Les traces de type GPU du lab 4.4 sont fabriquées. Les chiffres de fiche technique du H100 (3,35 To/s) viennent du module 2 et n'ont pas été relus ici.

### Hors périmètre {#hors-perimetre}

Les communications entre GPU (NCCL, voir les modules sur les réseaux), la programmation des cœurs tensoriels (`mma`, CUTLASS), la programmation multi-GPU et les groupes coopératifs, les clusters de blocs et le TMA de Hopper, le scan de Blelloch, les GPU non NVIDIA (ROCm), la sparsité, le partage de GPU (MIG) et l'installation des profileurs. L'observabilité d'une flotte (DCGM, métriques d'utilisation) relève du module sur l'observabilité.
