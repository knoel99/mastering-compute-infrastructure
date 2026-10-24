# Projet 6 — RFC et prototype : une plateforme de calcul de 8 à 256 GPU

Énoncé complet : `projects/capstone-rfc/index.md` (page du site).

```
starter/      requirements.yaml et mmc_sim.py (fournis) ; capacity.py, rfc_lint.py à écrire ; rfc.md : gabarit à remplir
reference/    solution de référence : modèle, vérificateur, et une RFC complète (à consulter après votre tentative)
tests/        37 tests partagés ; IMPL=starter|reference choisit le code et la RFC testés
verify.sh     prouve : référence verte, départ rouge
```

**Le cahier des charges est fictif** (`requirements.yaml`) : prix en unités arbitraires, taux de panne et
d'interruption inventés. La RFC de référence en tire tous ses chiffres par le modèle ; remplacez les données par
les vôtres pour un usage réel.

```bash
export PYTHON=/chemin/vers/python           # pytest et pyyaml
IMPL=starter $PYTHON -m pytest -q tests     # votre travail : 36 échecs sur 37 au départ
PYTHON=$PYTHON bash verify.sh               # référence verte (37), départ rouge
python3 reference/rfc_lint.py reference/rfc.md --requirements reference/requirements.yaml
```
