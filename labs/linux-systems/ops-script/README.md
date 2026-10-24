# Lab 1.5 — Un script d'exploitation idempotent

`ensure_sysctl.sh` met un paramètre noyau à la valeur voulue dans un fichier de `/etc/sysctl.d/`, **sans le dupliquer**,
en conservant le reste du fichier, avec une réécriture atomique (fichier temporaire puis `mv`).

Codes de retour (un appelant s'en sert pour savoir s'il doit recharger quelque chose) :
`0` rien à changer, `10` modifié (ou le serait avec `--dry-run`), `2` erreur d'usage, `1` échec.

```bash
./ensure_sysctl.sh --dry-run --conf /tmp/90-mci.conf vm.swappiness=10   # rien n'est écrit, code 10
./ensure_sysctl.sh --conf /tmp/90-mci.conf vm.swappiness=10             # écrit, code 10
./ensure_sysctl.sh --conf /tmp/90-mci.conf vm.swappiness=10             # inchangé, code 0
bash verify.sh
```

`--apply` règle aussi la valeur du noyau en cours d'exécution (root) ; le test d'intégration le fait avec la valeur
**déjà active**, donc sans effet sur la machine.

## Partie B — vérifier une unité systemd hors ligne

`check_unit.sh` enveloppe `systemd-analyze verify`, qui **retourne 0 même quand il affiche un avertissement**
(une valeur invalide est ignorée, pas fatale). Pour une vérification en intégration continue, toute sortie est un
échec. `units/gpu-exporter.service` est propre ; `units/bad.service` contient `Restart=sometimes`.
Systemd n'a pas besoin de tourner : la vérification se fait sur le fichier.

## Partie C — ce que `set -e` ne rattrape pas

`errexit_demo.sh` montre, par exécution, trois pièges : `set -e` est **neutralisé** dans une condition `if` et dans
une liste `||` (la fonction continue après un échec) ; un pipeline dont la première commande échoue retourne 0
sans `set -o pipefail`. `verify.sh` en vérifie la sortie.
