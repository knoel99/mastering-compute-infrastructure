---
title: "Environnement de travail"
subtitle: "Trois niveaux de machine, ce que chaque module exige, comment vérifier, comment ne pas se ruiner"
description: "Ce qu'il faut pour suivre le parcours : un ordinateur sans GPU suffit pour la base, une machine Linux jetable pour Slurm, un GPU loué seulement pour les extensions."
---

## Principe : commencer sans GPU {#principe}

Ce parcours se suit **sans GPU** pour tout ce qui est noté « vérifié » : les mécanismes d'infrastructure (ordonnancement, reprise après panne, mesure de passage à l'échelle, alertes) se travaillent sur des processeurs, et leurs pannes se reproduisent à la demande. Un GPU loué ne sert qu'aux **extensions** et à la validation finale d'hypothèses que ce site signale comme telles.

::: key
[Règle de budget]{.tag} Ne louez rien avant d'avoir lu l'énoncé de l'extension et écrit ce que vous voulez mesurer. Une machine GPU allumée « pour voir » coûte plus cher qu'une heure de réflexion.
:::

### Les trois niveaux {#niveaux}

| Niveau | Machine | Ce qu'elle permet | Coût |
|---|---|---|---|
| **A** | Ordinateur personnel, 4 cœurs, 8 Go de mémoire conseillés, sans droits administrateur | Modules 2 et 3, projets 2, 3, 4 et 6, tous les tests Python | Aucun |
| **B** | Machine ou conteneur **Linux jetable** avec accès root, 4 cœurs, 8 Go | Tout le niveau A, plus les labs Slurm (module 5), `promtool` (projet 5) et les labs système du module 1 | Aucun en local ; quelques heures de VM en nuage sinon |
| **C** | Machine avec un ou plusieurs GPU, louée à l'heure | Extensions GPU : noyaux, NCCL, variantes de projets | Voir « Budget » |

Le niveau B est un choix de sécurité autant que de commodité : les scripts de Slurm écrivent dans `/etc/slurm`, créent des utilisateurs et démarrent des démons en `root`. **Ne les lancez jamais** sur une machine de travail ou de production. Le script `labs/slurm/slurm-sandbox/teardown.sh` défait l'installation (l'option `--purge-db` efface aussi la comptabilité) ; les deux autres labs Slurm s'appuient sur la même installation.

## Configuration testée {#testee}

Les « labs vérifiés » de ce site ont été exécutés dans la configuration suivante. Elle n'a rien d'exigeant : si la vôtre est comparable, vous devriez obtenir des résultats comparables, pas identiques.

| Élément | Valeur |
|---|---|
| Système | Linux 6.18, Ubuntu 24.04, machine virtuelle sans GPU |
| Ressources | 4 processeurs logiques, 16 Go de mémoire |
| Python | 3.13, PyTorch 2.14.1 pour CPU, NumPy 2.5, SciPy 1.18, pytest 9.1, PyYAML 6.0 |
| Slurm | 23.11.4 (paquets Ubuntu), avec MariaDB 10.11 et `slurmdbd` |
| Prometheus | 2.45.3 (paquet Ubuntu : fournit `promtool`) |
| Pandoc | 3.1.3, seulement pour régénérer ce site |

Durées mesurées dans cette configuration, utiles pour planifier une séance : les trois labs Slurm vérifient en 36 s, 141 s et 52 s ; la vérification complète du projet 3 prend environ 1 min 15 s ; celle du projet 2, environ 40 s ; celle du projet 5, environ 6 s.

## Installation {#install}

Sous Ubuntu ou Debian. Ces commandes sont celles qui ont servi à préparer la configuration testée.

~~~bash
# Niveau A : Python et outils de test
sudo apt-get update && sudo apt-get install -y python3-venv python3-pip git
python3 -m venv ~/mci-venv && . ~/mci-venv/bin/activate
pip install numpy scipy pytest pyyaml
pip install torch --index-url https://download.pytorch.org/whl/cpu   # version pour CPU
~~~

L'environnement Python complet occupe environ **1,1 Go** sur disque, presque tout pour PyTorch.

~~~bash
# Niveau B : Slurm avec comptabilité, et promtool (machine JETABLE, root)
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y munge slurm-wlm slurmdbd mariadb-server
sudo apt-get install -y prometheus     # fournit promtool ; arrêtez le démon s'il démarre
~~~

Le paquet `prometheus` peut démarrer un démon qui occupe le port 9090 ; les projets n'en ont pas besoin, seulement de `promtool`.

Rien de tout cela n'est requis pour lire les pages : seuls les labs et les tests l'exigent.

### Vérifier l'installation {#verifier}

Le script `labs/check_env.sh` n'installe rien : il indique ce que la machine peut exécuter, niveau par niveau. L'option `--strict` fait échouer la commande si le niveau A est incomplet, ce qui sert dans une chaîne d'intégration continue.

~~~bash
PYTHON=~/mci-venv/bin/python bash labs/check_env.sh
~~~

Sur la configuration testée, il affiche pour le niveau A les versions de Python, de `torch`, `numpy`, `scipy`, `pytest` et `yaml`, puis pour le niveau B la présence de `sinfo`, `sbatch`, `sacctmgr`, `munge`, `mariadbd` et `promtool`. Sans GPU il écrit « none detected (fine: nothing is required) ».

## Ce que chaque élément exige {#exigences}

| Élément | Niveau | Remarque |
|---|---|---|
| Module 2, modèles de performance | A | PyTorch CPU pour le lab de l'all-reduce ; mesures plus stables avec 4 cœurs |
| Module 5, Slurm | B | Labs sur un vrai Slurm 23.11 ; durée de chaque vérification : moins de trois minutes |
| Projet 2, passage à l'échelle | A | 4 cœurs recommandés : avec moins, les « rangs » se disputent les processeurs |
| Projet 3, entraîneur tolérant aux pannes | A | Aucune dépendance système |
| Projet 5, observabilité | A et `promtool` | `promtool` s'installe avec `sudo apt-get install prometheus`, ou depuis les binaires du projet Prometheus |
| Modules et projets pas encore publiés | selon plan | Le niveau est donné dans leur plan, voir la page des plans détaillés |

## Budget {#budget}

Cette page **ne donne aucun prix** : les tarifs des fournisseurs changent, varient selon la région et la disponibilité, et un chiffre recopié ici serait faux au moment où vous le lisez. La méthode, elle, ne change pas.

Le coût d'une extension est le produit de trois quantités : la durée pendant laquelle la machine est allumée, le tarif horaire relevé **le jour même** sur la page de prix du fournisseur, et le nombre de machines. Ajoutez le stockage conservé après l'arrêt, souvent facturé séparément, et la sortie de données si vous en copiez. Pour borner la durée, partez des durées mesurées ci-dessus et multipliez par trois : vous perdrez du temps en configuration, pas en calcul.

::: war
[Trois protections avant la première machine louée]{.tag} Premièrement, une alerte de budget chez le fournisseur, créée **avant** la première machine. Deuxièmement, un arrêt automatique ou un délai d'expiration sur chaque machine. Troisièmement, une étiquette commune sur tout ce que vous créez, pour tout retrouver et tout supprimer à la fin, volumes et adresses IP compris.
:::

Les machines préemptibles ou « spot » coûtent moins cher en échange du droit pour le fournisseur de les reprendre à tout moment. C'est un excellent terrain d'entraînement pour le [projet 3](../projects/resilient-trainer/index.html), dont l'entraîneur reprend après une interruption brutale ; ce n'est pas un bon choix pour un lab que vous ne savez pas encore reprendre.

## Problèmes fréquents {#problemes}

- **Un lab Slurm bloque sur « InvalidAccount ».** La comptabilité n'est pas démarrée : `slurmdbd` ou MariaDB est arrêté. Relancez `setup.sh`, qui est idempotent.
- **Un lab Slurm échoue après un arrêt brutal de la machine.** L'état de la base peut être incohérent : lancez `teardown.sh --purge-db` puis `setup.sh`.
- **Les mesures du projet 2 varient beaucoup d'un essai à l'autre.** Fermez les autres programmes, vérifiez `OMP_NUM_THREADS=1`, et rappelez-vous que quatre processus sur quatre cœurs laissent le système sans marge.
- **`pytest` ne trouve pas `torch`.** Le `python` qui lance `pytest` n'est pas celui de l'environnement virtuel : exportez `PYTHON` vers `~/mci-venv/bin/python`, comme le demandent les scripts `verify.sh`.
- **`promtool` n'est pas trouvé.** Installez-le, ou exportez `PROMTOOL` vers le binaire ; les tests le lisent dans cette variable.
