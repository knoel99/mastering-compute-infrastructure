# ADR-002 — Les sessions interactives passent par un JupyterHub

## Statut

Proposé le 2026-04-06.

## Contexte

Le groupe de recherche (fictif) compte 40 personnes et lance environ 650 sessions interactives par mois, de 1,2 heure en moyenne : la demande moyenne est d'environ 1,07 GPU simultané. L'objectif de service est de démarrer une session en moins de 5 minutes. Les trois ingénieurs de plateforme ne peuvent pas exploiter un second système de lancement : la solution doit réutiliser la plateforme de la RFC-001 et s'arrêter seule quand elle est inactive.

## Décision

Nous déployons un JupyterHub qui lance un serveur mono-utilisateur par session sur le pool réservé de développement, avec un arrêt automatique après inactivité et une image de base épinglée par empreinte.

## Alternatives écartées

- **Portail de lancement de jobs de type Open OnDemand** : bonne intégration avec un ordonnanceur HPC et des applications interactives variées. Écartée parce que la plateforme retenue n'exécute pas les sessions sous Slurm ; Open OnDemand dispose d'un adaptateur Kubernetes, mais son coût d'exploitation face à celui d'un hub n'a pas été comparé, ce qui est le point à mesurer si le signal de révision se déclenche.
- **Accès SSH direct aux machines** : aucune infrastructure à écrire. Écartée parce qu'il n'y a ni isolation entre utilisateurs ni expiration automatique des sessions, donc des GPU réservés oubliés.

## Conséquences

**Positives**

- Une seule interface pour démarrer un environnement, avec des images contrôlées par l'équipe.
- L'arrêt après inactivité réduit les GPU réservés oubliés, que l'alerte d'allocation inactive du projet 5 surveille.

**Négatives**

- Un composant de plus à exploiter, avec ses mises à jour et sa sécurité.
- Le délai de démarrage dépend de la disponibilité du pool réservé : il n'est pas mesuré avant la mise en service.

Signal de révision : si le délai de démarrage au 90e centile dépasse 5 minutes pendant deux semaines consécutives, cette décision est rouverte.
