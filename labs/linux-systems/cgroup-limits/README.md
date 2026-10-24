# Lab 1.4 — cgroups : limite mémoire, OOM, quota CPU

`cgroup_lab.sh` crée un cgroup jetable, y lance un programme qui alloue 300 Mio sous une limite de 100 Mio
(il doit être tué : statut 137, compteur `oom_kill` à 1), puis une boucle active sous un quota de 20 % d'un
cœur (la part obtenue doit tomber entre 0,10 et 0,35).

```bash
sudo PYTHON=python3 bash verify.sh
```

**Ce qui a été exécuté.** Le script détecte la version : la branche **cgroup v1** (hiérarchies `memory` et
`cpu` séparées, y compris hybrides) a été exécutée dans le bac à sable, qui est en v1 avec seulement
`hugetlb` côté v2. La branche **cgroup v2** (`memory.max`, `cpu.max`, `memory.events`) suit la documentation
du noyau mais **n'a pas été exécutée**. Sur une machine v2 moderne (Ubuntu 22.04 et suivantes, par défaut),
c'est cette branche que vous exercez : signalez tout écart avec la page du module.

Lecture seule recommandée avant d'exécuter : le script écrit dans `/sys/fs/cgroup` en tant que root.
