# Lab 2.3 — Calculateur de MFU

Petit module Python testé qui calcule les FLOP par token d'un transformeur (formule de PaLM, annexe B) et le MFU d'un entraînement.

```bash
python3 -m pip install pytest
./verify.sh
python3 mfu.py --params 7e9 --layers 32 --heads 32 --head-dim 128 --seq-len 4096 \
    --tokens-per-step 4194304 --step-seconds 7.0 --gpus 64 --peak-tflops 989
```

Attention : `--peak-tflops` est le pic **dense** de la précision utilisée (989 pour BF16 sur H100 SXM), pas le chiffre « avec sparsité ».

`./verify.sh` lance 16 tests (formule de PaLM, lignes du tableau 4 de Llama 3, cas limites, ligne de commande de l'exemple 7.2) puis affiche le MFU de cet exemple. Les durées et le nombre de GPU de l'exemple sont des hypothèses, pas une mesure.
