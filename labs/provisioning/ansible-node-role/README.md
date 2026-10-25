# Lab 6.1 — Un rôle Ansible de nœud de calcul

Un rôle `gpu_node` qui pose limites, paramètres noyau, liste noire de `nouveau`, minuterie de contrôle et fait fact local sur trois nœuds **simulés** : chaque nœud est un répertoire (`node_root`) et la connexion est `local`. Rien n'est écrit dans `/etc` de la machine.

```bash
PYTHON=/chemin/vers/venv/bin/python bash verify.sh     # environ 40 s, sans root
```

Prérequis : `pip install ansible-core ansible-lint yamllint` (testé le 2026-10-24 avec ansible-core 2.21.5 et ansible-lint 26.10.1).

Ce que `verify.sh` démontre, avec des compteurs et du contenu de fichier, jamais des durées :

| Étape | Preuve |
|---|---|
| A | première exécution : `changed>0` sur les trois nœuds ; 3 lignes dans le journal d'actions (les 3 *handlers*) |
| B | seconde exécution : `changed=0` partout, le journal ne grandit pas (idempotence) |
| C | dérive : `--check --diff` montre `-* - memlock 1` / `+* - memlock unlimited` sans toucher au fichier ; l'exécution réelle corrige |
| D | déploiement progressif : `serial: [1, "100%"]`, le premier nœud (canari) est drainé en premier |
| E | un échec injecté sur le canari avec `max_fail_percentage: 0` : les deux autres nœuds ne sont jamais touchés |
| F | secret : variable chiffrée par `ansible-vault encrypt_string`, fichier en `0600`, mot de passe absent de la sortie même avec `--diff` |
| G | anti-patron : `-e gpu_node_stamp=true` met un horodatage dans un fichier géré, la seconde exécution change encore chaque nœud |

`playbooks/production_update.yml` est une **esquisse de production** (drain Slurm, attente, rôle, redémarrage, recette rapide, remise en service) : syntaxe vérifiée et linter, jamais exécutée.

**Simulé.** Les *handlers* du backend `log` écrivent une ligne dans `var/log/gpu_node_actions.log` au lieu de lancer `sysctl --system`, `update-initramfs -u` ou `systemctl`. Les variantes `systemd` (`gpu_node_service_backend: systemd`) sont passées au linter, **pas exécutées** ici. Les valeurs de limites et de sysctl sont des **exemples**, pas des recommandations validées.

**Mutation de contrôle.** En retirant `no_log: true` de `playbooks/secrets.yml`, `verify.sh` échoue (« found in secrets.log ») : le test discrimine.

Sur une vraie flotte : retirez `ansible_connection: local` et `node_root` de l'inventaire (ou fixez `node_root: ""`), utilisez l'inventaire généré par le lab 6.2, passez le backend à `systemd`.
