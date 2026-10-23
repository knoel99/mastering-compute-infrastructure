# Contrat d'un module de cours

Tout `courses/<id>/index.md` respecte ce contrat. Les contrôles mécaniques sont dans `tools/check_gates.py` ; la qualité de fond relève de la revue (voir `AGENTS.md`).

## 1. Langue et voix

- Prose en **français**, vouvoiement du lecteur (« vous »). Termes techniques anglais établis conservés tels quels (*checkpoint*, *scheduler*, *rank*, *throughput*), en italique à la première occurrence et définis. Pas de calque artificiel (« ordonnanceur » ne remplace pas *scheduler* partout : écrire « ordonnanceur (*scheduler*) » à la première occurrence puis choisir et s'y tenir).
- **Code, identifiants, commentaires de code, messages de commit : en anglais** (le lecteur publiera ce code sur GitHub).
- Phrases complètes. Pas de style « notes télégraphiques ». Un paragraphe ≤ 100 mots, une idée par paragraphe (gate `check_airiness.py` : A1 ≤ 100 mots par bloc, A2 ≤ 6 formules en ligne, A3 formule longue sur sa propre ligne en `$$…$$`).
- Chaque affirmation chiffrée sur un système réel (panne, débit, coût, taille de cluster) porte une source en lien. Sans source : la reformuler comme **ordre de grandeur** ou la supprimer. Jamais de chiffre inventé « pour faire vrai ».
- Les versions d'outils sont toujours datées (« testé avec Slurm X.Y le 2026-10-22 ») ; ne jamais affirmer « dernière version » sans l'avoir lue sur la source officielle.

## 2. En-tête YAML (obligatoire)

```yaml
---
title: "Slurm et exploitation d'un cluster HPC"
subtitle: "Module 05 · Phase 2 · 30 h"
description: "Une phrase."
module:
  id: slurm            # = nom du dossier
  number: 5
  phase: 2
  hours: 30            # volume d'étude total (lecture + labs + exercices)
  level: 2             # niveau d'entrée 1 | 2 | 3
prerequisites: [linux-systems]      # ids de modules, [] si aucun
status: core           # pour le lecteur de référence : core | skim | bonus
badges:
  - {label: "Cœur du parcours", class: core}      # core | skim | bonus
  - {label: "Labs vérifiés dans un bac à sable", class: verified}   # ou unverified
labs:
  - {id: slurm-single-node, kind: sandbox}   # sandbox | cluster | gpu
---
```

## 3. Squelette (ids d'ancre imposés)

```
## Introduction et vue d'ensemble {#intro}
### Fiche du module {#fiche}             (tableau Clé | Valeur)
### Ce que vous saurez vérifier {#acquis} (liste de capacités observables)
### Plan de séances {#seances}
## Avant de commencer {#avant}           (3 questions de positionnement, avec ::: sol)
## 1. Titre du chapitre {#ch1}           (… jusqu'à #chN, 5 à 10 chapitres, numérotés sans trou)
## Labs {#labs}
## Exercices {#ex}
## Checkpoint de sortie {#exit}
## Lectures et références {#refs}
## Sources et portée {#sources}
```

**Fiche du module** : volume (h) · niveau d'entrée · prérequis · statut pour le lecteur de référence · livrable · environnement requis (portable CPU suffisant ? GPU optionnel et coût indicatif) · lien vers les projets qui s'appuient sur ce module.

**Plan de séances** : tableau exact `| Séance | Durée | Niveau | Contenu | Pratique |`. Séances de 2 à 3 h ; durées au format `3 h` ou `2.5 h` ; **la somme est égale à `module.hours`** ; niveau 1 = fondations, 2 = méthodes de cœur, 3 = avancé/recherche, **jamais décroissant**. Chaque ligne cite chapitres, labs et exercices.

## 4. Chapitres

- 5 à 10 chapitres `## N. Titre {#chN}`, sous-sections `### N.k. Titre`.
- Au moins **un exemple travaillé par chapitre** (`::: ex`) avec calcul ou commande réels et leur résultat.
- Boîtes disponibles : `::: def` (définition), `::: thm` (loi, théorème, règle empirique chiffrée), `::: ex` (exemple travaillé), `::: note` (remarque), `::: key` (règle à ne pas oublier ; max 2 par chapitre), `::: war` (retour d'expérience ou panne **documentée** avec lien vers la source), `::: recap` (« Points clés » en fin de chapitre). Le titre de la boîte s'écrit `[Titre]{.tag}` en première ligne.
- Mathématiques en `$…$` / `$$…$$` (KaTeX). N'en mettre que si elles servent un calcul que le lecteur refera (Amdahl, roofline, modèle α-β, MFU, coût d'un checkpoint…).
- Code : blocs `~~~python`, `~~~bash`, `~~~yaml`… toujours avec langage. Le code montré dans le cours existe, **sous forme complète et exécutable ou linté**, dans `labs/<id>/…` et le cours y renvoie.
- Pas de capture d'écran. Schémas : SVG écrits à la main dans le dossier du module, légendés, lisibles en clair et en sombre (pas de couleur codée en dur : utiliser `currentColor` et les variables CSS du site) ; maximum 6 par module.

## 5. Labs

- Section `## Labs {#labs}` : **au moins 2** blocs `::: lab`, titre `[Lab N.M — Titre]{.tag}`.
- Chaque lab : **Objectif** · **Durée** · **Prérequis matériels** (laptop CPU / cluster / GPU, coût indicatif si payant) · **Étapes** numérotées · **Critère de réussite** observable (une valeur, une sortie, un graphe) · **Pour aller plus loin**.
- Code et fichiers dans `labs/<module-id>/<lab-id>/` avec `README.md`. Les labs `kind: sandbox` ont un script exécutable `verify.sh` qui **réussit (code 0) sur une machine Linux sans GPU** et affiche la valeur du critère de réussite. Les labs `cluster` et `gpu` sont au moins linté (shellcheck/`bash -n`, `python -m py_compile`, YAML parsé) et le disent honnêtement dans `badges` (`unverified`).
- Un lab dont le script n'a pas été exécuté ne peut pas porter le badge `verified`.

## 6. Exercices

- `## Exercices {#ex}` : **au moins 8**, au format
  ```
  ::: exo
  [Exercice 3 · ★★ — titre court]{.tag} Énoncé…
  :::

  ::: sol
  Corrigé complet (calculs, commandes, résultat).
  :::
  ```
- Difficulté : ★ (rappel/application directe), ★★ (raisonnement multi-étapes), ★★★ (conception ou diagnostic ouvert). Au moins 2 de chaque.
- Variété obligatoire : calcul chiffré, lecture de log ou de sortie de commande, diagnostic de panne, conception/dimensionnement, comparaison d'options avec arbitrage chiffré.
- Chaque corrigé est **vérifié** (le calcul a été refait en Python ou à la main, la commande a été exécutée ou lue dans la documentation officielle).

## 7. Checkpoint de sortie

5 à 8 capacités formulées « Je peux… » avec la **preuve attendue** (un artefact à produire ou une explication à fournir) et 3 questions d'entretien de type « compute infrastructure engineer » avec une réponse-type.

## 8. Références et sources

- `## Lectures et références {#refs}` : 6 à 15 entrées, uniquement des ressources **dont l'existence a été vérifiée** (idéalement tirées de `data/resources/learning.json`), avec : auteurs/fournisseur, titre, année, lien, et une phrase sur l'usage (« lire §3 pour… »).
- `## Sources et portée {#sources}` : trois listes distinctes — **documenté** (faits issus de sources citées), **recommandé** (choix pédagogique de ce parcours) et **à vérifier** (point instable ou dépendant du fournisseur). Cette section dit aussi ce que le module ne couvre pas.

## 9. Interdits

- Pas de contenu copié de supports de cours existants ; reformuler et citer.
- Pas de fausse précision (« exactement 93,7 % ») sans mesure reproductible fournie.
- Pas de promesse d'emploi ou de salaire.
- Pas de noms de clients de l'auteur. Pas de mention de l'employeur ciblé par le lecteur.
- Pas de secret, jeton ou clé dans le code (utiliser des variables d'environnement).
