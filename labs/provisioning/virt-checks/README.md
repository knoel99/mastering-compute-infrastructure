# Contrôles de virtualisation du chapitre 9

Outils du chapitre 9 du module 6 (virtualisation et multi-locataire), en lecture seule et sans droits root.

- `iommu_report.py [--root DIR]` liste les groupes IOMMU, leurs périphériques PCI et le pilote lié, et dit quels groupes sont prêts pour VFIO (règle de la documentation VFIO du noyau : le groupe est l'unité de propriété). Sans `--root`, il lit la machine courante.
- `make_fixture.py DIR` écrit l'arborescence **synthétique** d'un serveur fictif à quatre GPU (identifiants PCI réels, disposition inventée) pour l'exercice 13.
- `bind_vfio.sh <adresse PCI>` affiche les commandes qui confient tout le groupe IOMMU d'un périphérique à `vfio-pci` (méthode `driver_override`). Il ne fait rien sans `--apply`, et refuse `--apply` hors de `/sys`.
- `manifests/` : une ressource `KubeVirt` qui autorise un modèle de GPU et une `VirtualMachineInstance` qui en reçoit un. Analysées par `verify.sh`, jamais appliquées.

```bash
bash verify.sh      # environ une seconde
```

**Ce qui n'est pas vérifié.** Aucune VM n'a démarré et aucun GPU n'a été attaché : la machine de rédaction est elle-même une micro-VM sans groupe IOMMU, sans `/dev/kvm` et sans drapeau `vmx` ou `svm` (section C de `verify.sh`).
