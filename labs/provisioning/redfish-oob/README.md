# Lab 6.4 — Supervision hors bande : un client Redfish contre un BMC simulé

`redfish_client.py` découvre les systèmes depuis la racine du service (`/redfish/v1/`), lit `Status.Health` et `HealthRollup`, décide (`ok`, `watch`, `drain`) et peut demander un `ComputerSystem.Reset` en respectant la liste `ResetType@Redfish.AllowableValues` annoncée par le BMC. `mock_bmc.py` est un **simulateur** (bibliothèque standard) qui suit les chemins et les noms de propriétés de la spécification DMTF avec des valeurs synthétiques.

```bash
PYTHON=/chemin/vers/venv/bin/python bash verify.sh      # environ 5 s, sans root
```

Ce qui est prouvé : 9 tests (racine lisible sans authentification, ressources protégées, mauvais mot de passe refusé, verdict selon la pire santé, valeur inconnue comptée comme avertissement, `Reset` limité à la liste annoncée, BMC injoignable = erreur propre) puis le client en ligne de commande contre un processus de fond (code 1 = agir, c'est-à-dire `drain` ou `watch`, 2 = erreur).

**Limites assumées.** Le simulateur parle HTTP et Basic, alors que la spécification (DSP0266 1.22.0) exige HTTPS pour l'authentification Basic : ne copiez jamais ce transport. Il n'implémente ni sessions, ni `EventService`, ni schémas OEM. Le client n'a **jamais** été lancé contre un vrai BMC. Le mot de passe passe par la variable d'environnement `BMC_PASSWORD`, jamais par un argument de ligne de commande.

`ipmi_example.sh` est l'exemple `ipmitool` de la page (mot de passe par `-E`). Il est vérifié par `bash -n` et `shellcheck`, **jamais exécuté** : il n'y a pas de BMC.
