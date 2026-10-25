# Contrat d'un projet

Un projet est un livrable de **portfolio public** : un dépôt ou un dossier que le lecteur peut publier sur GitHub et présenter en entretien. Il mobilise plusieurs modules. Les contrôles mécaniques sont dans `tools/check_gates.py`.

## En-tête YAML

```yaml
---
title: "Projet 2 — Étude de passage à l'échelle d'un entraînement"
subtitle: "Projet 2 · 20 h · modules : perf-models, distributed-training"
description: "Une phrase."
project:
  id: scaling-study        # = nom du dossier
  number: 2
  hours: 20
  modules: [perf-models, distributed-training]
badges:
  - {label: "Portfolio", class: core}
  - {label: "Code de départ vérifié", class: verified}
---
```

## Sections (ancres imposées)

```
## Contexte et objectif {#contexte}
## Cahier des charges {#cahier}
## Jalons {#jalons}                (≥ 3 jalons numérotés ou en tableau, chacun avec durée et preuve)
## Livrables {#livrables}
## Critères de réussite {#criteres}   (≥ 4 critères mesurables : valeur, seuil, commande qui le montre)
## Pistes et indices {#pistes}
## Extensions {#extensions}
## Pour le portfolio {#portfolio}      (README type, ce qu'il faut montrer, ce qu'un recruteur cherche, 3 phrases d'accroche honnêtes)
```

## Règles

- Réalisable **sans GPU** dans sa version de base (laptop ou bac à sable) ; la variante GPU est une extension : sa page donne le matériel (nombre et type de GPU) et renvoie à la méthode de chiffrage de la page Environnement de travail (§ Budget), sans prix.
- Un **code de départ** vérifié existe dans `labs/projects/<id>/` (tests fournis, `verify.sh` passe sur le code de référence), et le dossier contient une **solution de référence** dans `labs/projects/<id>/reference/` que le cours présente comme « à consulter après votre propre tentative ».
- Les critères de réussite sont **mesurables** (ex. « le job reprend après un `kill -9` et la loss continue sans saut > 1 % », « le rapport donne le MFU avec sa formule »).
- Le projet nomme les **décisions de conception** à documenter (un ADR d'une page) : un recruteur lit cela avant le code.
- Pas de promesse de résultat d'embauche ; l'accroche portfolio reste factuelle.
