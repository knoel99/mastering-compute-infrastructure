# Réponse de niveau 2 (solide)

Je pars du calcul. Un modèle dense coûte environ 6 FLOP par paramètre et par jeton : 6 × 70e9 × 2e12 = 8,4e23 FLOP.
Un GPU de la génération H100 donne 989 TFLOP/s en BF16 dense ; avec une utilisation (MFU) de 0,40, valeur du même ordre que
celles publiées pour de grands entraînements, 256 GPU fournissent environ 1,0e17 FLOP/s utiles. La durée est donc d'environ 96 jours,
sur 32 nœuds de 8 GPU. Ce MFU est une hypothèse : je la mesurerai avant de m'engager.

Pour la fiabilité, je suppose 14 octets par paramètre dans un checkpoint (poids en BF16, poids maîtres et deux moments d'Adam en FP32) : 980 Go.
À 50 Go/s d'écriture agrégée, 20 secondes. Avec un taux de panne supposé de 0,0002 par GPU-heure, le job a un MTBF d'environ 19,5 heures ;
la période de checkpoint de Young et Daly est d'environ 28 minutes et la durée monte à environ 99,6 jours avec les pannes.

Conclusion : 256 GPU tiennent les 100 jours, mais presque sans marge. Je demanderais si le délai est ferme.
