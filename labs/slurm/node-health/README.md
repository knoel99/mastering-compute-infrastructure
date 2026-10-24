# Lab 5.3 — Drain, prolog et vérification de santé

`node_check.sh` est lancé par `slurmd` (`HealthCheckProgram`) toutes les 10 s : il draine le nœud si un contrôle échoue et le remet en service seulement si c'est lui qui l'avait drainé. `prolog_gate.sh` montre l'autre mécanisme : un prolog qui échoue draine le nœud et retient le job.

```bash
sudo bash verify.sh     # environ 1 minute
```

L'erreur GPU est **simulée** par un fichier `/tmp/fake_gpu_xid`. Un contrôle réel lirait DCGM, `nvidia-smi` ou `dmesg` (voir module 14).
