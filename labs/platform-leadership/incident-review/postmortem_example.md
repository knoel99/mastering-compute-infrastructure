# Post-mortem — Pré-entraînement bloqué pendant près de deux heures (incident synthétique)

*Document écrit à partir d'un journal d'incident inventé pour l'exercice (`incident.log`) : aucun système, cluster ni personne réels.*

## Résumé

Le pré-entraînement de 128 GPU (job 8841) a cessé de progresser à 02:11 UTC, lorsque le GPU du nœud gpu-17 a disparu du bus. Aucune alerte ne s'est déclenchée : la supervision lisait l'utilisation des GPU, restée à 98 %. Un chercheur a signalé une courbe de perte plate à 03:51. L'astreinte a drainé le nœud et relancé le job depuis son dernier checkpoint à 04:09.

## Impact

GPU-heures sans progression : 251,7 (128 GPU pendant 1 h 58 min, de l'anomalie à l'atténuation). Le job est reparti du checkpoint de 01:33, soit 38 min 40 s de calcul à refaire : 82,5 GPU-heures de plus. Aucune donnée perdue, aucun autre job touché.

## Chronologie

- 01:33 — dernier checkpoint du job, au pas 18 400.
- 02:11 — le noyau journalise un Xid 79 sur gpu-17 : le GPU a disparu du bus.
- 02:11 — le rang 41 cesse d'écrire son journal ; le délai d'attente de la collective n'est pas atteint.
- 02:12 — le tableau de bord affiche toujours 98 % d'utilisation pour le job.
- 03:51 — un chercheur signale une courbe de perte plate depuis environ 02:10.
- 03:55 — l'astreinte acquitte.
- 04:03 — diagnostic : le rang 41 est silencieux sur gpu-17, `dmesg` montre le Xid 79.
- 04:09 — gpu-17 est drainé, le job est remis en file depuis le checkpoint du pas 18 400.
- 04:31 — le job tourne de nouveau à plein débit.

Délai de détection : 1 h 40 min. Délai d'acquittement : 4 min. Délai d'atténuation : 18 min.

## Cause racine

La perte du GPU de gpu-17 a laissé le rang 41 silencieux et bloqué la collective de tout le job. Les autres rangs tournaient dans des noyaux d'attente : l'utilisation restait élevée et ne signalait pas l'arrêt du calcul utile.

## Facteurs contributifs

- L'alerte « job inactif » était fondée sur l'utilisation des GPU, qui reste élevée pendant une collective bloquée ; l'activité des unités tensorielles, elle, tombe à zéro.
- Un nœud ne passait pas automatiquement en drain sur un Xid 79.
- Aucune alerte ne signalait l'absence de journal d'un rang.

## Ce qui a bien marché

Un checkpoint récent limitait le calcul à refaire à 38 min 40 s. L'astreinte a acquitté en 4 minutes et posé le diagnostic en 7 minutes de plus. Le message du noyau était lisible et le runbook de drain existait.

## Ce qui a mal marché

La panne a été détectée par une personne et non par la supervision, 1 h 40 après son début. Le tableau de bord donnait un signal rassurant et faux.

## Actions

| Action | Propriétaire | Échéance | Vérification |
|---|---|---|---|
| Remplacer l'alerte fondée sur l'utilisation par une alerte fondée sur l'activité des unités tensorielles | équipe plateforme | 2026-03-28 | test promtool qui rejoue l'incident : utilisation à 98 %, activité tensorielle à 0, alerte déclenchée |
| Drainer automatiquement un nœud sur un Xid 79 | équipe plateforme | 2026-04-11 | test d'intégration sur un nœud d'essai : un Xid simulé met le nœud en drain |
| Mesurer chaque trimestre le délai de détection par un exercice de panne | responsable de l'astreinte | 2026-06-30 | exercice consigné avec un délai de détection mesuré inférieur à 10 minutes |

## Leçons

Un tableau de bord vert ne prouve pas que le calcul progresse : il faut une métrique qui mesure le travail utile. Un incident bien documenté permet de transformer chaque délai de la chronologie en une action vérifiable.
