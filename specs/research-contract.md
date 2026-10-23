# Contrat de recherche — masters HPC et exigences du marché

Ce contrat fixe la taxonomie et le format des données collectées. Il est la **seule** référence pour les agents de recherche et pour `tools/validate_research.py`.

Date de référence des relevés : **2026-10-22** (année académique 2026-2027 quand elle est publiée, sinon la plus récente).

## Règles d'honnêteté (non négociables)

1. Un fait n'entre dans une fiche que s'il a été lu sur une page réellement ouverte (WebFetch) ou dans un résultat de recherche cité. Chaque fait structurant (durée, crédits, intitulé d'un cours, accès à une machine) porte un `evidence` avec l'URL **et** un extrait court (≤ 25 mots) copié de la page.
2. Ce qui vient de la mémoire du modèle porte `"source": "memory"` et `confidence: "low"`. Ce n'est jamais présenté comme confirmé. La phase de vérification supprime ou requalifie ces éléments.
3. Un syllabus inaccessible n'est pas un syllabus vide : la couverture d'un thème vaut `null` (inconnu), pas `0`.
4. Un chiffre (crédits, heures, durée, nombre de nœuds, classement) est recopié avec son unité d'origine (ECTS, US credit hours, 学分…). Pas de conversion silencieuse.
5. Pas d'invention d'URL. Une URL qui ne répond pas est notée dans `blocked_sources`.

## Taxonomie des thèmes (`topic_coverage`)

Valeurs : `2` = cours dédié ou module obligatoire dont le titre nomme le thème · `1` = mentionné dans la description, les objectifs ou le syllabus d'un cours · `0` = syllabus accessible et thème absent · `null` = inconnu (syllabus non accessible).

| id | thème |
|---|---|
| `openmp-threads` | Parallélisme à mémoire partagée (OpenMP, threads, TBB) |
| `mpi` | Passage de messages (MPI) |
| `gpu-prog` | Programmation GPU (CUDA, HIP, SYCL, OpenCL, OpenACC, Triton) |
| `perf-model` | Modèles de performance, profilage, optimisation, roofline |
| `arch` | Architecture des ordinateurs (multicœur, hiérarchie mémoire, vectorisation) |
| `numerics` | Méthodes numériques, algèbre linéaire, calcul scientifique |
| `simulation-apps` | Simulation et applications (EDP, CFD, dynamique moléculaire, climat…) |
| `parallel-algos` | Algorithmique parallèle et complexité |
| `distributed-sys` | Systèmes distribués (consensus, tolérance aux pannes, cloud) |
| `sysadmin` | Administration système et exploitation de clusters (Linux, provisioning) |
| `scheduling` | Ordonnancement de jobs et gestion de ressources (Slurm, Kubernetes) |
| `interconnect` | Réseaux et interconnexions (InfiniBand, Ethernet/RoCE, topologies) |
| `storage-io` | Stockage et E/S parallèles (Lustre, GPFS, HDF5, MPI-IO) |
| `containers-k8s` | Conteneurs, virtualisation, Kubernetes |
| `cloud` | Cloud computing, coûts, multi-fournisseurs |
| `bigdata` | Données massives (Spark, Hadoop, flux) |
| `ml-dl` | Apprentissage automatique et profond |
| `ml-systems` | Systèmes pour l'IA : entraînement distribué, parallélisme de modèle, ML systems |
| `hpc-software-eng` | Génie logiciel HPC (tests, CI, reproductibilité, Spack, CMake) |
| `energy` | Efficacité énergétique, calcul frugal |
| `quantum-emerging` | Quantique et architectures émergentes |
| `viz` | Visualisation et analyse de données scientifiques |
| `thesis-internship` | Mémoire, projet de recherche, stage en entreprise |
| `soft-skills` | Gestion de projet, communication, éthique |
| `resilience` | Résilience, checkpointing, fiabilité à grande échelle |
| `observability-sre` | Supervision, observabilité, SRE |

## Fichier `data/masters/<unit>.json`

```json
{
  "unit": "fr-a",
  "region": "france",
  "retrieved_on": "2026-10-22",
  "programmes": [{
    "id": "fr-uvsq-chps",
    "country": "FR",
    "institution": "…",
    "programme_name": "…",
    "degree": "M2 | MSc | MS | MEng | Diploma | Certificate | …",
    "urls": ["https://…"],
    "duration": "… (valeur d'origine)",
    "credits": "… (valeur d'origine, avec unité)",
    "language": "…",
    "delivery": "on-site | online | hybrid",
    "entry_requirements": "…",
    "focus": "hpc-core | ml-systems | cse | cloud-distributed | ops-sysadmin | mixed",
    "structure_summary": "2-4 phrases factuelles",
    "core_courses": [{"name": "…", "credits": "…", "topics": ["mpi"], "url": "https://…"}],
    "electives": [{"name": "…", "topics": ["gpu-prog"], "url": "https://…"}],
    "capstone": "…",
    "machines_access": ["noms de supercalculateurs/clusters cités, avec URL en evidence"],
    "industry_links": ["…"],
    "topic_coverage": {"openmp-threads": 2, "mpi": 2, "…": null},
    "evidence": [{"claim": "…", "url": "https://…", "quote": "≤ 25 mots copiés de la page", "source": "web"}],
    "confidence": "high | medium | low",
    "notes": "…"
  }],
  "ecosystem": [{
    "id": "…", "kind": "centre | compétition | formation-courte | cours-ouvert | certification | réseau",
    "name": "…", "url": "https://…", "why_relevant": "…",
    "evidence": [{"claim": "…", "url": "https://…", "quote": "…", "source": "web"}]
  }],
  "blocked_sources": ["URL — raison"],
  "verification": {"status": "unverified | verified", "checked_claims": 0, "corrected": 0, "removed": 0, "notes": "…"}
}
```

`topic_coverage` contient **toutes** les clés de la taxonomie (26).

## Fichier `data/jobs/<unit>.json` (offres d'emploi)

Relevé de postes « compute / ML infrastructure » (cluster GPU, plateforme d'entraînement, HPC), au 2026-10-22. Les deux annonces d'une startup de robotique à Paris, déjà connues du lecteur, sont incluses sous le nom `"startup robotique (Paris)"` sans URL.

```json
{
  "unit": "jobs-a",
  "retrieved_on": "2026-10-22",
  "postings": [{
    "id": "…", "company": "…", "company_type": "ai-lab | gpu-cloud | hyperscaler | hpc-centre | vendor | startup | other",
    "title": "…", "location": "…", "url": "https://…", "seniority": "ic | senior | lead | staff | manager | unspecified",
    "years_required": null,
    "skills": [{"id": "slurm", "level": "required | bonus", "quote": "≤ 25 mots copiés"}],
    "responsibilities": ["…"],
    "notes": "…"
  }],
  "blocked_sources": []
}
```

Taxonomie des compétences (`skills[].id`) : `python`, `systems-lang` (Go/Rust/C++), `linux-admin`, `slurm`, `kubernetes`, `ray`, `multicloud-skypilot`, `terraform-iac`, `ansible-config`, `containers`, `pytorch-distributed`, `nccl-collectives`, `cuda-gpu`, `infiniband-roce`, `parallel-fs-storage`, `object-storage`, `prometheus-grafana`, `dcgm-gpu-monitoring`, `logging-tracing`, `experiment-tracking`, `checkpoint-fault-tolerance`, `scheduler-design`, `hyperscaler-cloud`, `gpu-cloud-providers`, `finops-cost`, `procurement-vendor`, `capacity-planning`, `security-compliance`, `sre-oncall`, `leadership-mgmt`, `hpc-experience`, `ml-training-experience`, `rl-infra`, `data-pipelines`, `networking-general`, `bare-metal-provisioning`, `ci-cd`, `inference-serving`.

## Fichier `data/resources/learning.json` (ressources d'apprentissage)

Livres, cours ouverts, articles, certifications, documentations de référence, communautés. Chaque entrée est **vérifiée** : le titre, les auteurs ou le fournisseur, l'année et l'URL ont été lus sur la page cible.

```json
{
  "unit": "res",
  "retrieved_on": "2026-10-22",
  "items": [{
    "id": "…",
    "kind": "book | course | paper | certification | docs | community | tool",
    "title": "…", "by": "auteurs ou fournisseur", "year": 2024,
    "url": "https://…",
    "topics": ["mpi"],
    "level": "intro | intermediate | advanced",
    "cost": "free | paid | unknown",
    "why": "1 phrase : ce que cette ressource apporte à un futur compute infrastructure engineer",
    "evidence": {"url": "https://…", "quote": "≤ 25 mots copiés de la page cible"}
  }],
  "blocked_sources": [],
  "verification": {"status": "unverified | verified", "checked": 0, "corrected": 0, "removed": 0, "notes": ""}
}
```
