# Lab 16.3 — Exercice de conception : de 8 à 256 GPU

`sizing.py` est le calculateur d'un entretien de conception : FLOPs d'entraînement (6 P D), durée selon le nombre de GPU et
le MFU, nombre de GPU pour un délai, taille et temps d'un checkpoint (hypothèse d'octets par paramètre **à énoncer**),
MTBF du job, période de Young et Daly et durée avec pannes.

```bash
python3 sizing.py --params 70e9 --tokens 2e12 --gpus 256 --peak-tflops 989 --mfu 0.40 \
  --bytes-per-param 14 --write-gb-s 50 --gpu-failure-rate 0.0002
PYTHON=python3 bash verify.sh
```

`rubric.md` donne l'énoncé et la grille ; `answers/` contient trois réponses (insuffisante, solide, excellente), **inventées pour l'exercice**, dont les
chiffres sont recoupés par les tests (nombre de jours, taille et temps de checkpoint, MTBF, période de Young et Daly, durée avec pannes). Les valeurs d'entrée (MFU de 0,40, 50 Go/s, taux de panne de 0,0002 par GPU-heure) sont
des **hypothèses d'exercice**, pas des mesures : changez-les et voyez la conclusion bouger.
