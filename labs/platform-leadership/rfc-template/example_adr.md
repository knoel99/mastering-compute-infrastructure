# ADR-001 — Le pré-entraînement tourne sur capacité préemptible

## Statut

Accepté le 2026-03-02.

## Contexte

Le groupe de recherche (fictif) lance en moyenne 1,5 pré-entraînement de 128 GPU par mois, de 240 heures de calcul chacun. Cette classe représente 86 % de la demande de 53 740 GPU-heures par mois et décide du coût de la plateforme. Le budget mensuel est de 450 000 unités arbitraires. Avec les prix et les taux de panne inventés du cahier des charges, le modèle de capacité donne 580 388 u à la demande et 317 161 u avec ce choix. Les trois ingénieurs de plateforme n'assurent une astreinte qu'en heures ouvrées : toute interruption doit donc être absorbée sans intervention humaine.

## Décision

Nous exécutons le pré-entraînement sur de la capacité préemptible, avec écriture atomique des checkpoints, relance automatique et détection de blocage, et une bascule vers la capacité à la demande si la capacité préemptible n'est pas obtenue en trente minutes.

## Alternatives écartées

- **Pré-entraînement à la demande** : peu d'interruptions et exploitation plus simple. Écartée parce que le coût de 580 388 u dépasse le budget de 130 388 u.
- **Pool réservé de 128 GPU** : aucun délai d'obtention. Écartée parce qu'un pool de 128 GPU, qui ne fait tourner qu'un pré-entraînement à la fois, donne une attente au 90e centile d'environ 903 heures contre un objectif de 48 heures, et qu'un pool de 256 GPU coûte plus d'un million d'unités.
- **Pré-entraînement réparti sur plusieurs petits jobs** : réduirait l'exposition aux interruptions. Écartée parce qu'elle change la nature de l'entraînement et sort du périmètre de cette plateforme.

## Conséquences

**Positives**

- Le coût mensuel du pré-entraînement passe de 492 741 u à 229 515 u dans le modèle.
- Le budget global tient avec une marge de 29,5 %.

**Négatives**

- Environ 52 incidents attendus par job (dont environ 45 interruptions de la capacité préemptible), donc une dépendance forte à la reprise automatique.
- L'hypothèse la plus fragile est la disponibilité de 128 GPU préemptibles d'un seul tenant : elle n'est pas mesurée.

Signal de révision : si plus d'un lancement sur quatre doit basculer vers la capacité à la demande, ou si le taux d'interruption mesuré dépasse environ 1,0 par heure de job, cette décision est rouverte.
