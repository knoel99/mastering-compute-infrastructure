# Lab 6.2 — Terraform : une flotte décrite en code

Une carte `nodes` (nom → rack, modèle de GPU, nombre de GPU, MAC, IP, IP du BMC) est la source de vérité. Le module `modules/fleet` en dérive cinq fichiers : inventaire Ansible, lignes `dhcp-host` de dnsmasq, lignes `NodeName=` de Slurm, `dnsmasq.conf` (PXE → iPXE) et `boot.ipxe`. Deux environnements (`envs/dev`, `envs/prod`) appellent le même module.

```bash
PYTHON=/chemin/vers/venv/bin/python bash verify.sh      # environ 10 s
```

Prérequis : Terraform >= 1.6 (testé le 2026-10-24 avec 1.16.7 et `hashicorp/local` 2.9.1, téléchargé une fois depuis le registre ; `TF_PLUGIN_CACHE_DIR` évite de le retélécharger), optionnellement `dnsmasq-base` et `ansible-core` pour les étapes H0 et H. `verify.sh` travaille sur une **copie** du lab dans un répertoire temporaire : aucun état, plugin ou fichier généré n'atterrit dans le dépôt.

| Étape | Preuve |
|---|---|
| A, B | `fmt`, `validate`, `terraform test` (3 scénarios : totaux, MAC dupliquée refusée, 7 GPU refusés) |
| C | `apply` : 11 objets dans l'état (6 `terraform_data` + 5 `local_file`), sorties `nodes=6`, `gpus=36` |
| D | `plan -detailed-exitcode` = 0 (rien à faire) |
| E | dérive : une ligne ajoutée à la main dans `prod-dhcp-hosts.conf` → code 2, puis `apply` la supprime |
| F | retirer `cpu-n01` de la carte : `Plan: 4 to add, 0 to change, 5 to destroy` (un enregistrement détruit, quatre fichiers remplacés) |
| G | MAC dupliquée : refus avec le message de validation |
| H0 | `dnsmasq --test` répond « syntax check OK » ; `boot.ipxe` : chaque `goto` a son étiquette, MAC uniques |
| H | `ansible-inventory --list` lit l'inventaire généré (6 hôtes, 3 groupes de racks) |

**Simulé / non exécuté.** Aucun nœud n'est démarré : le PXE n'est **pas** testé de bout en bout (pas de réseau de démarrage ici), `dnsmasq.conf` n'est vérifié que syntaxiquement et `boot.ipxe` que structurellement. Les adresses viennent des plages de documentation (RFC 5737) et les MAC sont « localement administrées » : rien ne désigne un vrai réseau.

**Observation (pas une règle documentée).** Avec `hashicorp/local` 2.9.1, éditer un fichier généré fait retirer la ressource de l'état au moment du rafraîchissement : le plan annonce `1 to add` et non `1 to change`.
