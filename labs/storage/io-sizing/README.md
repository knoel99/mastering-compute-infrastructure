# Lab 8.4 — Dimensionner : débit de lecture, checkpoint, striping, requêtes, cache, capacité

Les formules du module sous forme de petites fonctions testées (`iosizing.py`). Aucun appel à un système réel : ce lab sert à **refaire
chaque calcul de la page** et à les refaire avec vos propres chiffres.

```bash
export PYTHON=/chemin/vers/python   # pytest suffit
bash verify.sh                      # moins de 5 s
python3 iosizing.py demo            # les exemples des chapitres
python3 iosizing.py exercises       # les chiffres des corrigés
```

## Ce que les fonctions couvrent

| Fonction | Formule | Chapitre |
|---|---|---|
| `read_bandwidth` | consommateurs × échantillons/s × octets | 1 |
| `checkpoint_state_bytes`, `checkpoint_write_bandwidth` | $14\Psi$ ; $S/(f\tau)$ | 1 et 6 |
| `stripes_needed`, `aggregate_bandwidth` | plafond de $B/b$ ; minimum côté clients et côté serveurs | 2 |
| `metadata_operations`, `requests_per_second`, `prefixes_needed` | fichiers × 3 ; $B/n$ ; préfixes = requêtes/s divisées par le minimum documenté par préfixe | 3 et 4 |
| `half_performance_size`, `request_efficiency`, `in_flight` | $\alpha B$ ; $(n/B)/(\alpha+n/B)$ ; loi de Little | 3 et 4 |
| `sync_overhead`, `async_overhead` | $T_p/I$ ; $(s+\max(0,T_p-I))/I$ | 6 |
| `lru_epoch_hit_ratio`, `pinned_cache_hit_ratio`, `simulate_epoch_hit_ratio`, `effective_read_bandwidth`, `epoch_times` | $x+(1-x)\ln(1-x)$ ; $x$ ; simulation ; mélange harmonique ; affectation collante ou aléatoire | 7 |
| `retained_checkpoint_bytes`, `monthly_cost` | rotation « $K$ derniers + un sur $L$ » ; octets × prix | 8 |

## Étiquettes d'honnêteté

- Les entrées des exemples sont des **valeurs d'exemple** (taille d'image, débit par GPU, latence d'un magasin d'objets, débit d'un backend) ; ce ne sont pas des mesures d'un produit. Les seuls chiffres documentés sont ceux que la page attribue à une source (au moins 5 500 GET/s par préfixe S3, un minimum documenté et non un plafond ; 8 × 3,84 To de cache NVMe d'un DGX H100).
- La formule du taux de succès d'un cache LRU lors d'époques en ordre aléatoire est une **dérivation de ce parcours** (champ moyen, voir la docstring) ; elle est vérifiée par simulation à 3 points près. Ce n'est pas un résultat de la littérature.
- Aucun prix n'est donné : `monthly_cost` prend le prix en argument ; lisez la page de prix de votre fournisseur le jour même.
