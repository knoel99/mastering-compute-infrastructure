# Réponse de niveau 3 (excellente)

**Cadrage d'abord.** Le délai de 100 jours est-il ferme, ou est-ce une préférence ? Quel budget ? Qui d'autre utilise les GPU pendant ce temps ? Les données
sont-elles prêtes ? Je note ce que je ne sais pas : le MFU réel de ce code sur ce réseau, et le taux de panne réel de ce parc.

**Calcul.** 6 × 70e9 × 2e12 = 8,4e23 FLOP. À 989 TFLOP/s de pic par GPU et un MFU de 0,40, 256 GPU (32 nœuds) donnent 96 jours ; 248 GPU suffiraient pour 100 jours « sur le papier ».
**Sensibilité** : à un MFU de 0,35, la même machine met 110 jours et rate l'objectif. Le MFU est donc le paramètre qui décide, et je ne m'engage pas sans l'avoir mesuré.

**Fiabilité.** Checkpoint de 980 Go (14 octets par paramètre, hypothèse dite), 20 s à 50 Go/s ; MTBF du job d'environ 19,5 h pour un taux supposé de 0,0002 par GPU-heure ;
période de Young et Daly d'environ 28 min, durée avec pannes d'environ 99,6 jours. Avec 248 GPU, la durée dépasserait 100 jours : je choisis donc 256, soit 32 nœuds, pas 248.

**Avant de m'engager.** Une étude de passage à l'échelle de 8 à 64 GPU pour mesurer le MFU et la part de communication, un test de reprise exacte après `kill -9`, et une alerte sur l'activité des unités tensorielles
et non sur l'utilisation. **Goulots à surveiller** : le réseau entre nœuds, qui limite le MFU quand on passe à l'échelle, et le stockage, qui doit absorber un checkpoint sans arrêter l'entraînement.

**Décision et signal de révision.** 256 GPU réservés pour la durée du run. Je rouvre la décision si le MFU mesuré à 64 GPU est inférieur à 0,38 ou si le taux de panne mesuré dépasse trois fois l'hypothèse.
