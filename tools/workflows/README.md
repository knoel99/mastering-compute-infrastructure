# Workflows d'agents (Claude Code)

Scripts du tool `Workflow` utilisés pour produire ce dépôt. Ils ne sont pas exécutés par le site.

- `research.js` — enquête sourcée (masters, offres d'emploi, ressources). Les agents écrivent leurs fichiers **de façon incrémentale** dans `data/` et lisent les pages avec `tools/fetch_text.py`; `tools/verify_quotes.py` contrôle ensuite mécaniquement chaque citation. L'état du fichier est celui de la dernière exécution (unités `eu-b`, `row`, `jobs`) ; les premières unités (`fr-a`, `fr-b`, `us`, `cn-a`, `cn-b`, `eu-a`) ont été lancées avec la liste complète.
- `modules.js` — rédaction des modules : `args = {modules: [ids], curriculum: <data/curriculum.json>}` ; un rédacteur par module (labs exécutés, gates passés) puis un relecteur technique sceptique.

**Attention aux limites d'usage.** Une exécution complète consomme des millions de tokens de sous-agents : lancez par lots de deux ou trois modules, et vérifiez qu'aucun agent n'échoue avec « usage limit » avant de continuer. Le fichier `modules.js` référence un interpréteur Python du bac à sable de l'auteur (`PY`) : adaptez-le.
