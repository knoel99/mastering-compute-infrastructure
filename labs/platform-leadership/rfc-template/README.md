# Lab 16.1 — Écrire une décision d'architecture (ADR) vérifiable

`adr_lint.py` contrôle mécaniquement une décision d'une page : titre `# ADR-NNN — ...`, statut daté, contexte,
décision, **au moins deux alternatives écartées avec une raison** (« parce que »), conséquences positives **et** négatives,
et un **signal de révision** (la mesure qui rouvrirait la décision), le tout en 120 à 700 mots.

```bash
python3 adr_lint.py example_adr.md        # ok
python3 adr_lint.py adr_template.md       # refusé : le gabarit vierge n'est pas une décision
PYTHON=python3 bash verify.sh
```

`example_adr.md` reprend la décision de la RFC de référence du projet 6 (données **fictives**, chiffres issus de son
modèle). Pour une RFC complète, utilisez `labs/projects/capstone-rfc/reference/rfc_lint.py`.

Le vérificateur ne juge pas la qualité du raisonnement : il garantit qu'on a écrit ce qu'une relecture réclamera.
