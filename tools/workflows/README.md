# Workflows d'agents (Claude Code)

Scripts du tool `Workflow` utilisés pour produire ce dépôt. Ils ne sont pas exécutés par le site.

- `research.js` — enquête sourcée (masters, offres d'emploi, ressources). Les agents écrivent leurs fichiers **de façon incrémentale** dans `data/` et lisent les pages avec `tools/fetch_text.py` ; `tools/verify_quotes.py` contrôle ensuite mécaniquement chaque citation.
- `modules.js` — rédaction des modules : `args = {modules: [ids]}` ; chaque rédacteur lit lui-même son entrée de `data/curriculum.json`, exécute ses labs, passe les contrôles (`tools/check_gates.py`), puis un relecteur sceptique recalcule les chiffres, relit les sources et relance les labs.
- `review.js` — relecture indépendante de pages déjà écrites : `args = {targets: [{kind: "course"|"project", id: "..."}]}`. Le relecteur recalcule au moins douze chiffres, revérifie douze affirmations et toutes les citations, lance deux fois chaque `verify.sh`, essaie des mutations du code de référence (un test qui survit à une mutation est une anomalie) et signale toute assertion qui dépend du chronométrage.

## Ce qu'il faut savoir avant de relancer

**Limites d'usage.** Une exécution complète consomme des millions de tokens de sous-agents. Lancez par lots de deux à quatre modules et vérifiez qu'aucun agent n'échoue avec « usage limit » avant de continuer. Deux premières tentatives de ce dépôt ont échoué ainsi ; les résultats sont écrits dans les fichiers du dépôt au fil de l'eau pour que rien ne soit perdu.

**Machine partagée.** Au plus deux agents tournent en même temps sur quatre processeurs virtuels. Les scripts d'un module ne doivent donc **jamais** affirmer sur un chronométrage ; ils comptent des événements, des octets, des ratios avec tolérance. Les prompts le disent aux rédacteurs.

**Chemins propres au bac à sable.** `PY` et `SCR` désignent l'interpréteur Python et le dossier de travail du bac à sable de l'auteur : adaptez-les. Le bac à sable est en cgroups v1 (hybrides), sans GPU, sans processus 1 systemd, avec `perf` et `bpftrace` absents ; les prompts le précisent pour éviter des labs impossibles à vérifier.

**Une seule instance Slurm.** `labs/slurm/slurm-sandbox/setup.sh` démarre un Slurm unique ; deux agents ne doivent pas l'utiliser en même temps.
