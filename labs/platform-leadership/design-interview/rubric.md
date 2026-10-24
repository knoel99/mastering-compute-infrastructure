# Grille d'évaluation — exercice de conception « de 8 à 256 GPU »

**Énoncé donné au candidat.** « Votre équipe veut entraîner un modèle dense de 70 milliards de paramètres sur 2 000 milliards de jetons en moins de 100 jours, sur des GPU de génération H100. Concevez la plateforme : combien de GPU, quel réseau, quel stockage, quelle fiabilité. Vous avez trente minutes et le droit de poser des questions. »

Chaque critère est noté de 0 à 2 : 0 absent ou faux, 1 partiel, 2 solide. Les critères ★ sont éliminatoires.

| Critère | 0 | 1 | 2 |
|---|---|---|---|
| ★ Cadrage | part directement vers une solution | pose une ou deux questions | précise l'objectif, le délai ferme ou souple, le budget, les autres utilisateurs, ce qui n'est pas dans le périmètre |
| ★ Calcul de dimensionnement | aucun calcul, ou un ordre de grandeur faux | calcule la durée mais sans hypothèse dite | part des FLOPs (6 P D), dit l'utilisation visée (MFU) et sa source, obtient la durée et le nombre de nœuds |
| Hypothèses | non dites | dites mais non discutées | dites, discutées, et l'effet d'une erreur chiffré (par exemple MFU de 0,35) |
| Fiabilité | « on relance à la main » | mentionne les checkpoints | chiffre la taille et le temps d'écriture, le MTBF supposé et la période de checkpoint |
| Goulots | oublie réseau et stockage | les nomme | dit ce qui limiterait l'entraînement et comment le mesurer avant de s'engager |
| Compromis | une seule option | deux options | compare des options avec un critère et dit laquelle il choisit et pourquoi |
| Communication | confuse | claire mais longue | structurée, avec ce qu'il ne sait pas dit explicitement |

**Barèmes indicatifs.** Moins de 8 points sur 14 : réponse insuffisante. De 8 à 11 : solide. 12 à 14 avec les deux critères éliminatoires à 2 : excellente. Ces seuils sont un repère pour s'entraîner, pas un standard.

**Calculs de référence** (`python3 sizing.py`, voir `README.md`) : 8,4e23 FLOP ; 96,0 jours à 256 GPU avec un MFU de 0,40 ; 248 GPU suffisent « sur le papier » pour 100 jours, mais avec les pannes supposées la durée passe à 99,6 jours à 256 GPU, c'est-à-dire presque sans marge.
