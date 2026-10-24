# Lab 12.1 — Kueue : files, quotas, préemption

Type : **sandbox** (aucun cluster, aucun réseau, aucun GPU). Ce qui est vérifié ici :

1. les manifestes `manifests/` (ClusterQueue, LocalQueue, ResourceFlavor, Topology, WorkloadPriorityClass, un Job) sont **valides** : les types Kueue contre le schéma OpenAPI des CRD de Kueue v0.20.3 (`schemas/kueue-v1beta2.json`, descriptions retirées), les types Kubernetes contre les schémas 1.37 du paquet `kubernetes-validate`, en mode strict ;
2. le validateur **rejette neuf ClusterQueue mutées** (faute de frappe, valeur d'énumération, `borrowingLimit` sans cohorte, `lendingLimit` supérieur au quota…) ;
3. un **modèle simplifié** de l'admission de Kueue (quota, emprunt, prêt, préemption « classique ») est écrit en Python en deux versions : `starter/` à compléter et `reference/` ; les 36 tests passent sur `reference/` et 11 échouent sur `starter/` ;
4. `run_scenario.py` rejoue une journée sur le pool de 64 GPU, `gang_deadlock.py` calcule la probabilité d'interblocage d'un ordonnancement pod par pod, `topology_fit.py` illustre le placement par niveau de topologie.

## Ce que le modèle est, et n'est pas

C'est une **simulation écrite d'après la documentation** (pages « Preemption » et « ClusterQueue », champs des CRD), pas le code de Kueue. Il modélise un seul *flavor*, l'ordre « priorité puis ancienneté » dans une file, `StrictFIFO` contre `BestEffortFIFO`, `nominalQuota`, `borrowingLimit`, `lendingLimit`, `withinClusterQueue`, `reclaimWithinCohort`, `borrowWithinCohort` avec son seuil de priorité, l'ordre des candidats (files qui empruntent, priorité croissante, admission la plus récente) et la minimisation de la liste de victimes. Il ne modélise **pas** : l'équité (*fair sharing*), la fongibilité des *flavors*, les *admission checks*, l'admission partielle, la durée réelle d'une éviction, le sort exact d'une demande portant sur une ressource que la file ne couvre pas (le modèle la déclare inadmissible, choix du lab non vérifié dans la documentation). Les raisons de préemption de la sortie (`InClusterQueue`, `InCohort`) ne sont documentées que pour la première ; la seconde est une étiquette du lab.

## Lancer

```bash
python3 -m pip install pytest pyyaml jsonschema kubernetes-validate
PYTHON=python3 bash verify.sh            # tout : environ 10 s
python3 validate_manifests.py manifests  # validation seule
IMPL=starter python3 -m pytest -q tests  # votre travail : 11 échecs au départ
python3 run_scenario.py scenarios/platform-day.yaml
python3 gang_deadlock.py && python3 topology_fit.py
```

Les schémas se régénèrent avec `python3 fetch_schemas.py v0.20.3` (accès à raw.githubusercontent.com). Les règles CEL des CRD ne sont pas exécutables par un validateur JSON Schema : quatre sont réécrites à la main dans `validate_manifests.py`, une règle de bon sens est ajoutée (`lendingLimit` ≤ `nominalQuota`) ; le serveur d'API réel du lab 12.4 applique les règles CEL elles-mêmes.

## Pour aller plus loin

Ajoutez le *fair sharing* au modèle, ou une seconde ressource contrainte (mémoire) ; écrivez un test qui échoue si deux files échangent indéfiniment des préemptions ; installez Kueue sur un cluster de test et comparez la trace réelle de `kubectl get workloads` à celle du modèle.
