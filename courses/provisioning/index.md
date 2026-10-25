---
title: "Provisioning, images et santé des nœuds GPU"
subtitle: "Module 06 · Phase 2 · 24 h"
description: "Du châssis nu au nœud en production : démarrage réseau, images, Ansible et Terraform, pile GPU, recette et burn-in, mises à jour, RMA et supervision hors bande."
module:
  id: provisioning
  number: 6
  phase: 2
  hours: 24
  level: 2
prerequisites: [linux-systems]
status: core
badges:
  - {label: "Cœur du parcours", class: core}
  - {label: "Labs : 3 vérifiés dans un bac à sable, la recette GPU non exécutée", class: unverified}
labs:
  - {id: ansible-node-role, kind: sandbox}
  - {id: terraform-fleet, kind: sandbox}
  - {id: node-acceptance, kind: gpu}
  - {id: redfish-oob, kind: sandbox}
---

## Introduction et vue d'ensemble {#intro}

**La question à laquelle ce module répond :** comment passer d'un châssis qui vient d'être vissé dans une baie à un nœud qui peut recevoir un entraînement de deux semaines, de façon répétable, et comment savoir que le centième nœud est identique au premier ? Un ingénieur d'infrastructure ne se juge pas à la première installation, mais à la deux-centième, et à la façon dont il remplace un nœud en panne un mardi à 3 h.

Ce module suit la vie d'un nœud : démarrage réseau et images, configuration idempotente avec Ansible, description de la flotte avec Terraform, pile logicielle du GPU, recette et *burn-in* (test de rodage sous charge), mises à jour sans arrêter la production, remplacement sous garantie (*RMA*), et supervision par le contrôleur de gestion (*BMC*) quand le système d'exploitation ne répond plus.

::: key
[Règle de ce module]{.tag} Déclarez l'état voulu, laissez des outils idempotents le réaliser, puis **prouvez-le** avant de laisser un job entrer. Un nœud dont on ne peut pas montrer la recette n'est pas en production : il est seulement allumé.
:::

Les labs s'exécutent sans GPU, par simulation. Chaque simulation est étiquetée comme telle sur la page et dans le README du lab : un BMC simulé n'est pas un BMC, un répertoire n'est pas un nœud, et une preuve de recette synthétique n'est pas une mesure. Les parties qui exigent du matériel ou un cluster (la collecte réelle de la recette, le démarrage PXE de bout en bout, un vrai BMC, la mise à jour en production) sont au mieux lintées ou vérifiées en syntaxe, et **jamais exécutées ici**.

### Fiche du module {#fiche}

| Clé | Valeur |
|---|---|
| Volume | 24 h, dont 8 h de lecture, 10,5 h de labs et 5,5 h d'exercices |
| Niveau d'entrée | 2 : à l'aise avec Linux, systemd et le réseau (module 1) |
| Prérequis | [Module 1 — Linux, systèmes et diagnostic](../linux-systems/index.html) |
| Statut pour le lecteur de référence | cœur : Kubernetes, Terraform et FinOps sont acquis, mais ni le démarrage réseau, ni la recette GPU, ni les BMC |
| Livrable | un rôle Ansible testé, un module Terraform qui dérive tout de la carte des nœuds, un script de recette dont la logique de décision est testée, un client Redfish testé |
| Environnement | un portable ou une VM Linux, sans GPU ; Terraform, ansible-core et dnsmasq pour les labs. La recette réelle demande un nœud GPU avec DCGM (optionnel ; coût non chiffré ici, à demander à votre fournisseur) |
| Projets liés | [Projet 1 — Mini-cluster Slurm instrumenté](../../projects/homelab-slurm/index.html), [Projet 6 — RFC de plateforme](../../projects/capstone-rfc/index.html) |

### Ce que vous saurez vérifier {#acquis}

-   Décrire la chaîne firmware, DHCP, TFTP, iPXE, HTTP, image, configuration, enregistrement dans l'ordonnanceur, et dire où elle casse (chapitres 1 et 2).
-   Écrire un rôle Ansible idempotent, le tester en mode vérification, le déployer par lots avec un canari et protéger un secret (chapitre 3).
-   Décrire une flotte avec Terraform, lire un plan, détecter une dérive et refuser une destruction involontaire (chapitre 4).
-   Vérifier la compatibilité pilote, CUDA et Fabric Manager d'un nœud avant qu'un job n'échoue (chapitre 5).
-   Concevoir une recette à trois issues (accepter, rejouer, refuser) et expliquer pourquoi un code de retour ne suffit pas (chapitre 6).
-   Planifier une mise à jour progressive et dimensionner un volant de nœuds de rechange (chapitre 7).
-   Interroger un BMC par Redfish et décider de drainer un nœud sur sa santé matérielle (chapitre 8).

### Plan de séances {#seances}

Neuf séances, soit 24 h. Chaque séance contient ses chapitres, sa part de lab et ses exercices, et un exercice n'est placé qu'après la séance qui enseigne ce dont il a besoin. Le niveau ne diminue jamais.

| Séance | Durée | Niveau | Contenu | Pratique |
|---|---|---|---|---|
| 1 | 2 h | 1 | ch. 1 Cycle de vie d'un nœud (45 min) ; questions de positionnement (15 min) ; ch. 2 §2.1 La chaîne de démarrage (30 min) | Ex. 1 |
| 2 | 2 h | 1 | ch. 2 §2.2 à §2.5 Démarrage réseau et images | Ex. 2, 3 |
| 3 | 3 h | 2 | ch. 3 Gestion de configuration avec Ansible | Lab 6.1 partie A ; Ex. 4 |
| 4 | 3 h | 2 | ch. 4 Terraform pour la flotte | Lab 6.1 partie B ; Ex. 5 |
| 5 | 3 h | 2 | Synthèse des chapitres 2 à 4 par le lab | Lab 6.2 |
| 6 | 2.5 h | 2 | ch. 5 Pile GPU, ch. 6 §6.1 à §6.3 Tests, outils et remappage | Ex. 6, 8 |
| 7 | 2.5 h | 2 | ch. 6 §6.4 et §6.5 Recette : règles de décision | Lab 6.3 partie A ; Ex. 7 |
| 8 | 3 h | 3 | ch. 7 Mises à jour, pannes et RMA | Lab 6.3 partie B ; Ex. 9 |
| 9 | 3 h | 3 | ch. 8 BMC, Redfish et IPMI | Lab 6.4 ; Ex. 10, 11 |

## Avant de commencer {#avant}

Consacrez 15 minutes à ces trois questions. Elles servent à vous orienter, pas à vous noter. Si elles vous semblent routinières, parcourez les exercices ★★★ et le chapitre 6.

1.  **Idempotence.** Un script shell installe un paquet et ajoute une ligne à un fichier de configuration. Que se passe-t-il à la deuxième exécution, et que change un outil de configuration déclarative ?

2.  **Premier octet.** Un serveur sans disque démarre sur le réseau. Dans quel ordre interroge-t-il quels services, et que télécharge-t-il en premier ?

3.  **Couche fautive.** `nvidia-smi` liste huit GPU sur un nœud neuf, mais l'initialisation de NCCL (la bibliothèque NVIDIA de communication collective entre GPU) échoue dans le premier job. Citez trois couches logicielles ou matérielles à contrôler avant de soupçonner le code d'entraînement.

::: sol
**Réponses.**

1.  Le script ajoute la ligne une seconde fois et peut échouer sur le paquet déjà présent : il décrit des actions. Un outil déclaratif décrit un état et n'agit que si l'état réel diffère ; relancé sur un nœud conforme, il ne change rien. Voir le chapitre 3.

2.  Le micrologiciel (*firmware*) demande une adresse par DHCP, reçoit l'adresse d'un serveur et le nom d'un programme d'amorçage, le télécharge par TFTP (iPXE ou GRUB), puis ce programme télécharge noyau, *initrd* (le petit système de fichiers que le noyau charge en mémoire au démarrage) et image, le plus souvent par HTTP. Voir le chapitre 2.

3.  Par exemple : la version du pilote face à celle de CUDA dans le conteneur, le service Fabric Manager sur un système à NVSwitch, la topologie PCIe et NVLink (liens dégradés), le réseau d'interconnexion. Voir les chapitres 5 et 6.
:::

## 1. Cycle de vie d'un nœud : recette, installation, exploitation, retrait {#ch1}

Un nœud GPU n'est pas un objet qu'on installe une fois. Il traverse des états, chacun avec une porte d'entrée vérifiable et une porte de sortie. Ce chapitre fixe le vocabulaire du module et montre, chiffres publiés à l'appui, pourquoi la porte qui sépare « installé » de « en production » est celle qui rapporte le plus.

### 1.1. Les états d'un nœud

Le parcours ci-dessous est un choix pédagogique de ce module, pas une norme. Il distingue ce que l'inventaire sait d'un nœud (identité), ce que les outils de configuration lui ont fait (état voulu) et ce que l'ordonnanceur en pense (état de service).

<figure class="fig">
<svg viewBox="0 0 560 250" role="img" aria-labelledby="lc-t lc-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="lc-t">Cycle de vie d'un nœud GPU</title>
<desc id="lc-d">Quatre états en ligne : reçu, installé, recette, production. De la production on passe à drainé, puis à réparation, qui retourne à la recette, ou au retrait.</desc>
<defs><marker id="lc-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="currentColor"/></marker></defs>
<g fill="var(--bg)" stroke="currentColor" stroke-width="1.5">
<rect x="8" y="30" width="96" height="46" rx="6"/>
<rect x="124" y="30" width="96" height="46" rx="6"/>
<rect x="240" y="30" width="96" height="46" rx="6" stroke="var(--accent)" stroke-width="3"/>
<rect x="356" y="30" width="100" height="46" rx="6"/>
<rect x="356" y="150" width="100" height="46" rx="6"/>
<rect x="196" y="150" width="120" height="46" rx="6"/>
<rect x="30" y="150" width="120" height="46" rx="6"/>
</g>
<g fill="currentColor" font-size="15" text-anchor="middle">
<text x="56" y="58">reçu</text>
<text x="172" y="58">installé</text>
<text x="288" y="58">recette</text>
<text x="406" y="58">production</text>
<text x="406" y="178">drainé</text>
<text x="256" y="178">réparation</text>
<text x="90" y="178">retiré</text>
<text x="280" y="22" fill="var(--accent)">la porte qui compte</text>
<text x="416" y="118" text-anchor="start" font-size="14">panne, mise à jour</text>
</g>
<g stroke="currentColor" stroke-width="1.8" fill="none" marker-end="url(#lc-a)">
<path d="M104 53H122"/><path d="M220 53H238"/><path d="M336 53H354"/>
<path d="M406 76V148"/><path d="M356 173H318"/><path d="M196 173H152"/>
<path d="M256 150V80" stroke-dasharray="5 4"/>
</g>
<text x="262" y="118" font-size="14" fill="currentColor">rejeu de la recette</text>
</svg>
<figcaption>Les sept états de ce module. Le rectangle épais est la recette : un nœud n'y reçoit aucun job. Après une réparation, il repasse par la recette (flèche pointillée).</figcaption>
</figure>

Dans Slurm (module 5), un nœud en recette est drainé avec une raison explicite, par exemple `acceptance`. Le drain est le mécanisme qui matérialise l'état : le nœud existe, il est joignable, aucun job n'y entre.

| État | Porte d'entrée | Qui en décide |
|---|---|---|
| reçu | numéro de série, MAC et adresse du BMC saisis dans l'inventaire | l'inventaire (lab 6.2) |
| installé | image déployée, configuration convergée (`changed=0` à la seconde passe) | l'outil de configuration (lab 6.1) |
| recette | tests du chapitre 6 passés sans rejet | le script de recette (lab 6.3) |
| production | verdict *accept*, nœud remis en service dans l'ordonnanceur | l'ordonnanceur |
| drainé | contrôle de santé en échec ou mise à jour planifiée | l'automatisation |
| réparation | intervention, éventuellement échange sous garantie | un humain, avec dossier |
| retiré | fin de vie ou échange définitif, identité révoquée | l'inventaire |

### 1.2. Pourquoi la porte de la recette rapporte le plus

Deux publications de Meta donnent des ordres de grandeur sur de très grands clusters d'entraînement. Elles décrivent leur flotte, pas la vôtre : lisez-les comme des échelles, pas comme des cibles.

::: war
[Ce que mesurent deux grands clusters]{.tag} Sur 54 jours d'entraînement de Llama 3 405B, [Dubey et al. (2024)](https://arxiv.org/abs/2407.21783) comptent 466 interruptions de job, dont 47 planifiées (firmware, configuration) et 419 inattendues. Environ 78 % des interruptions inattendues sont attribuées à du matériel confirmé ou suspecté. Le temps d'entraînement effectif dépasse 90 %, avec une maintenance automatisée qui provoque au moins une interruption par jour.

[Kokolis et al. (2024)](https://arxiv.org/abs/2410.21680) mesurent sur deux clusters de recherche des taux moyens de 6,50 (RSC-1) et 2,34 (RSC-2) pannes pour 1 000 nœuds-jours, qui varient dans le temps (de l'ordre de 2,5 à 17,5 sur RSC-1). Le MTTF (*mean time to failure*, temps moyen avant panne) est de 7,9 h pour les jobs de 1 024 GPU contre 47,7 jours pour ceux de 8 GPU.

Ils décrivent aussi des « nœuds citrons » (*lemon nodes*) : 40 nœuds identifiés, dont l'éviction fait passer les échecs de gros jobs (512 GPU et plus) de 14 % à 4 %. Les mêmes auteurs signalent jusqu'à 50-75 % de perte de bande passante réseau pendant la mise en service de l'un des clusters.
:::

La leçon d'infrastructure est simple. Quand un job occupe 1 024 GPU, un seul nœud défaillant l'arrête. Un nœud qui sort de l'usine ou de la réparation avec un défaut latent coûte alors des centaines de GPU-heures avant qu'on ne le trouve. La recette déplace la découverte du défaut avant le premier job.

::: ex
[Exemple 1.1 — Lire un tableau publié avec méfiance]{.tag} Le tableau 5 de l'article Llama 3 classe les 419 interruptions inattendues par composant. Le script `labs/provisioning/exercise-calcs/calc.py` en recopie les 18 lignes et les recoupe avec le texte (sortie réelle, Python 3.13, 2026-10-24) :

~~~text
$ python3 calc.py llama
sum of counts      : 419  (the text says 419 unexpected interruptions)
sum of printed %   : 94.9
mismatch           : Faulty GPU: 148/419 = 35.3 % but the table prints 30.1 %
interruptions/day  : 8.63 total, 7.76 unexpected, 0.87 planned (466, 419, 47 over 54 days)
~~~

Les effectifs recoupent bien le texte, mais la ligne « Faulty GPU » affiche 30,1 % alors que 148 sur 419 donne 35,3 %, et les pourcentages imprimés ne totalisent que 94,9 %. L'article est internement incohérent sur ce point : une coquille probable, que nous ne corrigeons pas à sa place. Retenez les **effectifs**, utilisables, et ne citez pas ce pourcentage seul.
:::

### 1.3. Identité et inventaire : la source de vérité

Tout le reste du module suppose qu'un nœud a une identité stable et lisible par des machines. Quatre éléments suffisent à commencer : le numéro de série du châssis, l'adresse MAC de l'interface de démarrage, l'adresse du BMC, et la position (baie, hauteur). On y ajoute plus tard les identifiants des GPU, que `nvidia-smi` expose, et ceux des cartes réseau.

Le point de départ de ce module est une **carte des nœuds**, un fichier déclaratif de votre dépôt. Le lab 6.2 en dérive l'inventaire Ansible, la configuration DHCP, le script de démarrage et les lignes `NodeName=` de Slurm. Écrire une information à un seul endroit est la seule façon pour que quatre outils ne divergent jamais.

La recette a besoin d'une référence. Plutôt qu'une valeur lue sur une fiche technique, comparez chaque nœud à un nœud « doré » (*golden node*) que vous avez qualifié à la main, et à la médiane de la flotte. Le seuil d'acceptation de la bande passante, au chapitre 6, est un paramètre de site mesuré ainsi.

::: recap
Points clés — chapitre 1

-   Un nœud traverse sept états ; chaque porte d'entrée est une preuve, pas une impression.
-   Sur de grands clusters publiés, une part majoritaire des interruptions inattendues vient du matériel ; un job de 1 024 GPU a un MTTF de quelques heures (7,9 h chez Kokolis et al.).
-   Un tableau publié se recoupe avant d'être cité : celui de Llama 3 est incohérent sur un pourcentage.
-   L'identité d'un nœud vit dans un fichier déclaratif unique, dont les autres outils sont dérivés.
:::

## 2. Démarrage réseau et images : PXE, iPXE, MAAS, Warewulf, BCM {#ch2}

Un serveur neuf n'a ni système ni configuration : tout ce qu'il sait faire, c'est demander du réseau. Ce chapitre décrit la chaîne qui le mène de là à un noyau Linux, la façon dont on choisit ce que le serveur reçoit, et les trois familles d'outils que vous rencontrerez, avec leurs forces et leurs limites telles que leurs documentations les décrivent.

### 2.1. La chaîne de démarrage

La documentation de Warewulf décrit la séquence générique du démarrage réseau d'un nœud de cluster. Le micrologiciel (BIOS ou UEFI) initialise le matériel, dont la carte réseau, puis son client PXE (*Preboot eXecution Environment*, le démarrage réseau intégré au firmware) obtient une adresse par BOOTP/DHCP. Le serveur DHCP répond avec une adresse et une option « serveur suivant » (*next-server*) qui désigne où télécharger, par TFTP (*Trivial File Transfer Protocol*, un protocole minimal de transfert de fichiers), un programme d'amorçage : iPXE ou GRUB.

Ce programme lit sa configuration et télécharge le noyau, l'image et les compléments de configuration, ici par HTTP. Enfin Linux démarre avec cette image comme système de fichiers racine.

<figure class="fig">
<svg viewBox="0 0 560 330" role="img" aria-labelledby="bc-t bc-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="bc-t">Chaîne de démarrage réseau</title>
<desc id="bc-d">Six étapes de haut en bas : firmware, DHCP, TFTP, iPXE, HTTP, Linux. L'étape iPXE refait une requête DHCP avant de recevoir l'URL d'un script.</desc>
<defs><marker id="bc-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="currentColor"/></marker></defs>
<g fill="var(--bg)" stroke="currentColor" stroke-width="1.5">
<rect x="10" y="8" width="190" height="38" rx="6"/><rect x="10" y="62" width="190" height="38" rx="6"/>
<rect x="10" y="116" width="190" height="38" rx="6"/><rect x="10" y="170" width="190" height="38" rx="6" stroke="var(--accent)" stroke-width="3"/>
<rect x="10" y="224" width="190" height="38" rx="6"/><rect x="10" y="278" width="190" height="38" rx="6"/>
</g>
<g fill="currentColor" font-size="15">
<text x="105" y="33" text-anchor="middle">firmware (PXE)</text><text x="105" y="87" text-anchor="middle">serveur DHCP</text>
<text x="105" y="141" text-anchor="middle">serveur TFTP</text><text x="105" y="195" text-anchor="middle">iPXE s'exécute</text>
<text x="105" y="249" text-anchor="middle">serveur HTTP</text><text x="105" y="303" text-anchor="middle">noyau Linux</text>
<text x="222" y="33" font-size="14">demande une adresse</text><text x="222" y="87" font-size="14">adresse + nom du programme</text>
<text x="222" y="141" font-size="14">télécharge le binaire iPXE</text><text x="222" y="195" font-size="14" fill="var(--accent)">refait un DHCP, reçoit une URL</text>
<text x="222" y="249" font-size="14">script, noyau, initrd, image</text><text x="222" y="303" font-size="14">enregistrement au scheduler</text>
</g>
<g stroke="currentColor" stroke-width="1.8" fill="none" marker-end="url(#bc-a)">
<path d="M105 46V60"/><path d="M105 100V114"/><path d="M105 154V168"/><path d="M105 208V222"/><path d="M105 262V276"/>
</g>
</svg>
<figcaption>Les deux demandes DHCP : celle du firmware reçoit le binaire iPXE, celle d'iPXE reçoit l'adresse d'un script. Sans cette distinction, le serveur renverrait iPXE indéfiniment.</figcaption>
</figure>

| Étape | Protocole | Panne typique |
|---|---|---|
| adresse | DHCP | aucun serveur sur le bon VLAN, ou deux serveurs qui répondent |
| programme d'amorçage | TFTP | mauvais fichier pour l'architecture (BIOS ou UEFI) |
| script, noyau, image | HTTP | URL absente, image trop grosse pour la mémoire disponible |
| système démarré | Linux | pilote réseau absent de l'*initrd*, disque non vu |

### 2.2. La boucle iPXE et sa parade

Beaucoup de firmwares ne savent faire que du TFTP. On les amène donc à charger iPXE, qui sait faire du HTTP et exécuter des scripts. Mais iPXE, au démarrage, refait sa propre requête DHCP : si le serveur lui répond de nouveau « télécharge iPXE », la machine charge iPXE qui charge iPXE, sans fin.

::: war
[La boucle d'iPXE, un piège documenté]{.tag} La page *Chainloading iPXE* du projet décrit exactement ce cas : le DHCP doit répondre autrement à la deuxième requête, soit par un script intégré à iPXE ou un script `autoexec`, soit en ne livrant le binaire iPXE qu'à la première requête. Voir [ipxe.org/howto/chainloading](https://ipxe.org/howto/chainloading).
:::

Avec dnsmasq, on distingue les deux requêtes par l'option DHCP 175, que seul iPXE envoie. Le lab 6.2 génère cette configuration depuis la carte des nœuds. En voici le cœur, tel que Terraform l'a écrit :

::: ex
[Exemple 2.1 — Une configuration PXE générée et validée]{.tag} Extrait de `prod-dnsmasq.conf` produit par `labs/provisioning/terraform-fleet` (adresses de documentation RFC 5737), puis la validation de syntaxe par dnsmasq 2.91 (Ubuntu 24.04, 2026-10-24) :

~~~text
dhcp-range=192.0.2.2,static
dhcp-match=set:ipxe,175
dhcp-match=set:efi64,option:client-arch,7
dhcp-match=set:efi64,option:client-arch,9
dhcp-boot=tag:!ipxe,tag:efi64,ipxe.efi
dhcp-boot=tag:!ipxe,tag:!efi64,undionly.kpxe
dhcp-boot=tag:ipxe,http://192.0.2.2/prod-boot.ipxe

$ dnsmasq --test -C prod-dnsmasq.conf
dnsmasq: syntax check OK.
~~~

Lecture : `static` ne distribue d'adresse qu'aux machines listées par une ligne `dhcp-host` (une machine inconnue ne reçoit rien). Le firmware, sans l'option 175, reçoit un binaire iPXE choisi selon son architecture annoncée dans l'option 93 (le [RFC 4578](https://www.rfc-editor.org/rfc/rfc4578.txt) attribue 9 à EFI x86-64 et 7 à EFI Byte Code ; des firmwares UEFI x86-64 annoncent l'un ou l'autre selon les constructeurs : le gabarit couvre les deux, à confirmer par une capture sur votre matériel). iPXE, lui, reçoit l'URL d'un script.

**Ce que cela ne prouve pas.** `--test` ne vérifie que la syntaxe. Aucune machine, réelle ou virtuelle, n'a démarré sur cette configuration dans le bac à sable : le chemin PXE de bout en bout est **non testé** ici.
:::

Le script `boot.ipxe` généré identifie le nœud par sa MAC, choisit un profil (`gpu` ou `cpu`) et refuse de démarrer une machine inconnue :

~~~text
#!ipxe
set base http://192.0.2.2/images
isset ${net0/mac} || goto unknown
iseq ${net0/mac} 02:00:00:00:02:01 && goto node_gpu_n01 ||
...
:unknown
echo MAC ${net0/mac} is not in the inventory: refusing to boot
~~~

Les commandes `iseq`, `goto`, `kernel`, `initrd` et `boot` et le réglage `net0/mac` sont décrits dans la documentation d'iPXE. Le lab vérifie la structure du script (chaque `goto` a son étiquette, les MAC sont uniques), pas son exécution.

### 2.3. Deux philosophies d'image

Une fois le noyau démarré, la question est ce qui constitue le système. Deux familles dominent.

-   **Sans état** (*stateless*). L'image du système est téléchargée à chaque démarrage et vit en mémoire ; le disque, s'il existe, ne porte que des données locales. Un nœud défectueux se « répare » par un redémarrage. La mise à jour consiste à changer l'image puis à redémarrer les nœuds.
-   **Avec état** (*stateful*). L'image est écrite sur le disque du nœud par un installateur, puis le nœud démarre sur disque. Les mises à jour peuvent se faire en place, ce qui laisse les nœuds diverger si on n'y prend garde.

Entre les deux, une troisième voie, très répandue : installer une image générique, puis laisser un outil de configuration (chapitre 3) faire converger le nœud. Elle demande moins d'outillage au départ et plus de discipline ensuite.

La documentation de Warewulf signale un détail d'exploitation utile quel que soit l'outil : en mode « une seule étape », l'image est livrée directement par le programme d'amorçage, ce qui ne fonctionne pas dans tous les environnements (certaines dispositions de mémoire ne sont pas gérées par iPXE ni GRUB pour de grosses images). En « deux étapes », un petit système d'amorçage récupère l'image complète, ce qui est souvent plus rapide.

### 2.4. Trois outils, leurs forces et leurs limites

Les faits ci-dessous viennent des pages officielles lues le 24 octobre 2026. Les limites marquées « raisonnement » sont des déductions de ce parcours, pas des affirmations des projets.

| Outil | Ce que sa documentation établit | Limites à évaluer |
|---|---|---|
| MAAS (Canonical) | mise sous tension par le BMC, démarrage d'un environnement éphémère en mémoire (programme d'amorçage par TFTP ou HTTP, puis noyau, *initrd* et système de fichiers fournis par MAAS), scripts de profilage matériel et de tests, puis déploiement : *curtin* partitionne et écrit l'image, *cloud-init* la personnalise ; pilotes d'alimentation dont IPMI et Redfish ; fournisseur Terraform `canonical/maas` | installation avec état (raisonnement) ; périmètre et images à confirmer pour votre distribution |
| Warewulf | provisionnement sans état de grappes Linux, images gérables avec des outils de conteneurs, surcouches (*overlays*) de configuration, commandes `wwctl` dont `node sensors` | l'état local est reconstruit à chaque démarrage (raisonnement) ; le pilote GPU est figé dans l'image |
| NVIDIA Base Command Manager (BCM) | simplifie le provisionnement des clusters, la gestion des charges et la supervision de l'infrastructure (d'après la page de la documentation) ; guide de déploiement d'un système personnalisé sur DGX ; licence gratuite proposée par la page produit | produit propriétaire ; **conditions de licence à relire le jour de l'achat** |

D'autres projets existent et n'ont pas été évalués ici : OpenCHAMI (plateforme ouverte de gestion de systèmes HPC), OpenStack Ironic (service de nœuds nus) et xCAT. Leurs pages d'accueil ont été lues ; leurs capacités n'ont pas été comparées.

Le choix se joue moins sur une fonctionnalité que sur trois questions : qui possède l'image et son cycle de vie, comment on reconstruit un nœud à l'identique, et quelle équipe sait déboguer le démarrage à 3 h du matin. L'exercice 3 les met en balance.

### 2.5. Le réseau de démarrage n'est pas de confiance

N'importe quelle machine du VLAN de démarrage peut répondre à une requête DHCP ou servir un faux noyau : le démarrage réseau classique n'authentifie pas le serveur. Isolez ce réseau, n'y laissez que les nœuds et le serveur de provisionnement, et conservez la règle de la section 2.2 : une machine absente de l'inventaire ne reçoit ni adresse ni image.

::: recap
Points clés — chapitre 2

-   La chaîne est : firmware, DHCP, TFTP (iPXE), HTTP (script, noyau, image), Linux, enregistrement dans l'ordonnanceur.
-   Distinguez les deux requêtes DHCP (firmware, puis iPXE) pour ne pas boucler ; dnsmasq le fait avec l'option 175.
-   Sans état, avec état ou installation puis configuration : trois choix, avec des coûts d'exploitation différents.
-   MAAS, Warewulf et BCM sont documentés sur ce qu'ils font ; leurs limites se jugent sur votre contexte et sur les conditions du jour.
-   Une machine inconnue ne reçoit rien ; le réseau de démarrage est isolé.
:::

## 3. Gestion de configuration : Ansible, idempotence, inventaires, secrets {#ch3}

Une image ou une installation donne un système ; la configuration le rend conforme. Sur une flotte, la propriété qui compte est la **convergence prouvée** : après chaque exécution, on sait que le nœud est dans l'état voulu, et on sait le dire en un chiffre. Ce chapitre utilise Ansible, outil sans agent qui parle à ses cibles par SSH, et le rôle du lab 6.1.

### 3.1. Idempotence, définition et preuve

Le glossaire d'Ansible définit l'idempotence ainsi : une opération est idempotente si le résultat de son exécution unique est exactement le même que celui de son exécution répétée, sans intervention entre-temps. Les modules déclaratifs (`template`, `file`, `sysctl`) comparent l'état réel à l'état voulu et n'agissent que s'ils diffèrent.

La preuve pratique est le décompte `changed` de la récapitulation (*PLAY RECAP*) à la **seconde** exécution : zéro partout. Un `changed=1` récurrent est un défaut du rôle, pas un détail cosmétique, car une flotte qui ne converge jamais ne peut jamais être déclarée conforme.

Les trois causes habituelles sont les modules `command` et `shell` sans `changed_when`, les valeurs qui changent à chaque exécution (horodatage, aléatoire) dans un fichier géré, et les fichiers réécrits avec des permissions différentes de celles que le module relit.

### 3.2. Un rôle, un inventaire

Le rôle `gpu_node` du lab 6.1 pose des limites de ressources, des paramètres noyau, la liste noire du pilote `nouveau` (la documentation de DCGM compte un `nouveau` chargé parmi les causes d'échec de son test de déploiement), une minuterie systemd de contrôle rapide et un fait local qui publie la révision de configuration. Il suit l'arborescence standard d'Ansible : `defaults/`, `tasks/`, `templates/`, `handlers/`, `meta/`.

~~~yaml
- name: Set kernel parameters
  ansible.builtin.template:
    src: sysctl.conf.j2
    dest: "{{ node_root }}/etc/sysctl.d/90-gpu-training.conf"
    mode: "0644"
  notify: Apply sysctl settings
~~~

La variable `node_root` est l'astuce du lab : sur la flotte réelle elle est vide et les chemins sont ceux du système ; dans le bac à sable, elle désigne un répertoire par nœud, et la connexion `local` remplace SSH. Le code du rôle est identique dans les deux cas, et rien ne touche `/etc` de la machine d'essai.

L'inventaire range les nœuds en groupes (ici `gpu_nodes`) ; les valeurs communes vont dans `group_vars/gpu_nodes.yml`, les exceptions dans `host_vars/<nom>.yml`. Au lab 6.2, l'inventaire n'est plus écrit à la main : Terraform le génère depuis la carte des nœuds, en groupes de racks.

### 3.3. Les gestionnaires n'agissent que sur un changement

Recharger les paramètres noyau ou régénérer l'*initramfs* à chaque exécution serait coûteux et parfois dangereux. Un *handler* est une tâche qui ne s'exécute que si une tâche l'a notifiée **et** a signalé un changement ; par défaut, les gestionnaires tournent à la fin du jeu de tâches, une seule fois.

Le lab prouve la règle sans lancer de vraie commande : en mode `log`, chaque gestionnaire ajoute une ligne à `var/log/gpu_node_actions.log`. Après la première exécution le journal compte trois lignes (sysctl, initramfs, systemd) ; après la seconde, toujours trois. Le mode `systemd` du même rôle lance les vraies commandes et n'a été que linté.

### 3.4. Mode vérification et mode différence

`--check` simule : Ansible dit ce qu'il changerait sans le faire ; `--diff` affiche les différences de contenu. La documentation prévient que la simulation ne produit pas de sortie pour les tâches dont une condition dépend du résultat d'une tâche précédente. Elle valide donc bien une configuration déclarative, moins bien un enchaînement impératif.

C'est l'outil de détection de dérive d'une flotte : lancé périodiquement en `--check`, il liste les nœuds dont l'état réel a quitté l'état voulu, sans rien modifier.

::: ex
[Exemple 3.1 — Convergence, idempotence et dérive sur un nœud]{.tag} Sorties réelles du bac à sable (ansible-core 2.21.5, Python 3.13, 2026-10-24), nœud simulé `gpu-n01`. Première exécution, puis seconde :

~~~text
gpu-n01 : ok=9 changed=9 unreachable=0 failed=0 skipped=3 rescued=0 ignored=0
gpu-n01 : ok=6 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
~~~

Les neuf changements sont six tâches et trois gestionnaires ; les trois tâches ignorées sont les variantes `systemd` des gestionnaires, inutiles dans ce mode. On modifie ensuite à la main `memlock unlimited` en `memlock 1`, puis on lance `--check --diff` :

~~~text
-* - memlock 1
+* - memlock unlimited
 * - nofile 1048576
changed: [gpu-n01]
~~~

Le fichier n'est pas modifié par `--check` (le lab compare son contenu avant et après) ; l'exécution réelle suivante le corrige, puis une troisième exécution revient à `changed=0`. Les chiffres sont reproductibles : `bash labs/provisioning/ansible-node-role/verify.sh`.
:::

### 3.5. Déployer par lots, avec un canari

Changer la configuration de toute une flotte d'un coup est la façon la plus rapide de la mettre toute en panne. Le mot-clé `serial` découpe le jeu de tâches en lots ; chaque lot est un jeu complet sur un sous-ensemble de nœuds. Avec `max_fail_percentage: 0`, un seul échec dans un lot interrompt la suite.

~~~yaml
- name: Roll the node configuration out in batches
  hosts: gpu_nodes
  gather_facts: false
  serial:
    - 1
    - "100%"
  max_fail_percentage: 0
~~~

Le premier lot ne contient qu'un nœud, le **canari**. Si l'on injecte un échec sur lui, le lab constate que les deux autres nœuds ne sont jamais touchés (leurs fichiers de configuration n'existent pas). Sans cette garde, un rôle défectueux atteint toute la flotte avant qu'on ait lu la première erreur. La documentation d'Ansible précise aussi que, si tous les hôtes d'un lot échouent, le jeu échoue.

Dans une exploitation réelle, on intercale avant le rôle une étape de drain (chapitre 7) et après lui une étape de validation qui remet le nœud en service. Le lab les simule par des lignes dans `rollout.log`.

### 3.6. Secrets

Un mot de passe de BMC n'a rien à faire en clair dans un dépôt. `ansible-vault encrypt_string` chiffre une valeur (AES-256) en une variable inscriptible dans un fichier YAML ordinaire ; le mot de passe de chiffrement se passe par fichier ou par script, jamais par argument.

Chiffrer ne suffit pas, car Ansible affiche volontiers les valeurs qu'il manipule. Le lab écrit le fichier d'identifiants en mode `0600` avec `no_log: true`.

::: note
[Une mesure du lab : sans no_log, le secret fuit dans --diff]{.tag} Le lab génère un secret aléatoire à chaque exécution, le chiffre, déploie le fichier avec `--diff`, puis vérifie que le secret n'apparaît ni dans le fichier chiffré ni dans la sortie. En retirant `no_log: true` du playbook, la vérification échoue : le mot de passe apparaît dans la sortie de `--diff`. C'est une observation du bac à sable, pas une garantie générale.
:::

::: recap
Points clés — chapitre 3

-   L'idempotence se prouve par `changed=0` à la seconde exécution ; un horodatage dans un fichier géré la détruit (le lab le démontre).
-   Les gestionnaires ne tournent qu'après un changement : « pas de changement, pas de redémarrage ».
-   `--check --diff` est un détecteur de dérive sans effet de bord, avec ses limites sur les tâches conditionnelles.
-   `serial` et `max_fail_percentage` font d'un nœud le canari de la flotte.
-   Un secret se chiffre, se dépose en `0600` et se protège de l'affichage par `no_log`.
:::

## 4. Terraform pour l'infrastructure : état, modules, environnements, dérive {#ch4}

Vous connaissez Terraform. Ce chapitre ne le réexplique pas : il en fixe l'usage pour une flotte GPU, où l'objet décrit est souvent un serveur physique que Terraform ne sait pas visser dans une baie. Il montre ce qu'il gère bien (la carte des nœuds et tout ce qui s'en dérive), et ce qu'il ne doit jamais pouvoir détruire.

### 4.1. Ce que Terraform gère dans une flotte

Terraform garde dans son état la correspondance entre les objets déclarés dans la configuration et les objets réels qu'il a créés. Pour un cluster de GPU dans un nuage, ces objets sont des instances, des réseaux, des volumes. Pour un cluster sur site, il n'y a pas d'API de « création de serveur » universelle ; Terraform reste utile à deux endroits.

Le premier est la **carte des nœuds**, source de vérité du lab 6.2, dont il rend les fichiers dérivés : inventaire, DHCP, Slurm, démarrage. Le second est l'orchestration d'un outil de provisionnement qui expose une API : un fournisseur `canonical/maas` existe dans le registre Terraform (version 2.10.0 publiée le 2026-09-09, d'après l'API du registre).

Dans le lab, les objets sont des fichiers locaux et des enregistrements `terraform_data`, une ressource du fournisseur intégré (aucun téléchargement) qui, d'après sa documentation, suit le cycle de vie standard d'une ressource sans effectuer d'autre action directe. Chaque nœud y devient un objet distinct de l'état, ce qui rend visible la disparition d'un nœud de la carte.

### 4.2. Plan, application et dérive

`terraform plan` compare la configuration, l'état et la réalité rafraîchie. Avec `-detailed-exitcode`, la documentation fixe le code de sortie : 0 si le plan est vide, 2 s'il contient des changements (1 pour une erreur). C'est le test d'idempotence et de dérive à brancher dans une intégration continue ; le mode `-refresh-only` ne met à jour que l'état pour refléter la réalité.

::: ex
[Exemple 4.1 — Idempotence, dérive, retrait d'un nœud]{.tag} Le lab 6.2, sorties réelles (Terraform 1.16.7, `hashicorp/local` 2.9.1, 2026-10-24). Environnement `prod`, six nœuds :

~~~text
Plan: 11 to add, 0 to change, 0 to destroy.     # première application
plan -detailed-exitcode = 0                     # seconde passe : rien à faire
Plan: 1 to add, 0 to change, 0 to destroy.      # après une ligne ajoutée à la main : code 2
Plan: 4 to add, 0 to change, 5 to destroy.      # après retrait de cpu-n01 de la carte
~~~

Onze objets : six enregistrements de nœud et cinq fichiers. Dans le troisième plan, la ressource `local_file` modifiée à la main est **retirée de l'état** au rafraîchissement puis recréée (« 1 to add », pas « 1 to change »). C'est un comportement observé avec ce fournisseur, non une règle de Terraform.

Dans le quatrième, retirer `cpu-n01` détruit son enregistrement (`terraform_data.node["cpu-n01"] will be destroyed`) et **remplace** les quatre fichiers qui dépendent de la liste des nœuds : 4 créations, 5 destructions. Le fichier `dnsmasq.conf`, qui n'en dépend pas, ne bouge pas.
:::

### 4.3. Modules, environnements, validation

Le module `fleet` prend la carte des nœuds, `cluster_name` et `output_dir`. Les environnements `dev` et `prod` sont deux répertoires qui appellent le même module avec des valeurs différentes. Le choix entre répertoires séparés et espaces de travail (*workspaces*) relève de la préférence de l'équipe ; ce parcours recommande les répertoires, parce qu'une revue de code montre alors directement ce qui diffère entre les environnements.

La validation est le vrai gain. Les règles s'expriment dans des blocs `validation` et échouent avant tout changement :

~~~hcl
validation {
  condition     = length(distinct([for n in values(var.nodes) : n.mac])) == length(var.nodes)
  error_message = "Two nodes share the same MAC address: the DHCP server could not tell them apart."
}
~~~

Le lab en a cinq sur la carte des nœuds (et une sixième sur le nom du cluster) : forme des adresses MAC, unicité des MAC, unicité des adresses IP et BMC, forme des adresses IPv4, nombre de GPU parmi 0, 4 et 8. La commande `terraform test` (disponible depuis Terraform 1.6) exécute des scénarios sans rien créer : trois ici, dont deux qui **doivent** être refusés grâce à `expect_failures`.

### 4.4. Ce qui ne doit jamais se détruire

Une destruction involontaire est la pire opération possible sur un parc de serveurs. L'option `prevent_destroy` semble faite pour l'empêcher, mais la documentation précise sa limite.

::: war
[prevent_destroy ne protège pas d'un retrait de la configuration]{.tag} La page *lifecycle* indique qu'à l'exception de `create_before_destroy`, Terraform n'enregistre pas la règle de cycle de vie dans l'état. En conséquence, il détruit l'infrastructure réelle lors d'un `apply` si vous retirez la **configuration** de la ressource, même avec `prevent_destroy`. Voir [developer.hashicorp.com/terraform/language/meta-arguments/lifecycle](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle).
:::

Trois pratiques en découlent. Faites relire par un humain le résumé `Plan:` de chaque changement qui touche la carte des nœuds, et refusez tout plan qui détruit plus que prévu. Gardez pour les nœuds physiques une ressource qui ne représente qu'un **enregistrement**, pas la machine : détruire l'enregistrement ne doit rien éteindre. Enfin, stockez l'état dans un système distant avec verrouillage, car l'état est une source de vérité partagée.

::: recap
Points clés — chapitre 4

-   Terraform garde la correspondance configuration et objets réels ; sur site, il dérive les fichiers de la carte des nœuds et pilote les outils à API.
-   `plan -detailed-exitcode` vaut 0 (rien) ou 2 (changements) : c'est le test de dérive d'une intégration continue.
-   Les blocs `validation` et `terraform test` refusent une carte invalide avant tout changement.
-   `prevent_destroy` ne protège pas d'un retrait de configuration : relisez le résumé `Plan:` et ne modélisez pas la machine, seulement son enregistrement.
:::

## 5. La pile GPU : pilote, CUDA, Fabric Manager, DCGM, conteneurs {#ch5}

La majorité des pannes « mystérieuses » d'un nœud neuf sont des incompatibilités entre couches installées par des mains différentes. Ce chapitre ordonne ces couches, donne les règles de compatibilité documentées par NVIDIA et montre comment les transformer en un contrôle automatique.

### 5.1. Les couches

<figure class="fig">
<svg viewBox="0 0 560 330" role="img" aria-labelledby="st-t st-d" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:inherit">
<title id="st-t">Les couches logicielles d'un nœud GPU</title>
<desc id="st-d">Six couches empilées. Les quatre du bas sont installées sur l'hôte, les deux du haut vivent dans l'image du conteneur. Le pilote de l'hôte limite la version de CUDA que le conteneur peut utiliser.</desc>
<g fill="var(--bg)" stroke="currentColor" stroke-width="1.5">
<rect x="10" y="10" width="330" height="40" rx="6"/><rect x="10" y="58" width="330" height="40" rx="6"/>
<rect x="10" y="118" width="330" height="40" rx="6"/><rect x="10" y="166" width="330" height="40" rx="6" stroke="var(--accent)" stroke-width="3"/>
<rect x="10" y="214" width="330" height="40" rx="6"/><rect x="10" y="262" width="330" height="40" rx="6"/>
</g>
<g fill="currentColor" font-size="15">
<text x="24" y="35">framework (PyTorch)</text><text x="24" y="83">CUDA toolkit, NCCL</text>
<text x="24" y="143">runtime de conteneur, toolkit NVIDIA</text><text x="24" y="191">services : Fabric Manager, DCGM</text>
<text x="24" y="239">pilote : module noyau + bibliothèques</text><text x="24" y="287">firmware : GPU, NVSwitch, BIOS, BMC</text>
<text x="352" y="38" font-size="14">dans l'image</text><text x="352" y="86" font-size="14">du job</text>
<text x="352" y="146" font-size="14">sur l'hôte</text><text x="352" y="194" font-size="14" fill="var(--accent)">à garder alignés</text>
<text x="352" y="242" font-size="14">(le pilote borne</text><text x="352" y="262" font-size="14">la version de CUDA)</text>
</g>
</svg>
<figcaption>Les deux couches du haut appartiennent aux utilisateurs, les quatre du bas à l'équipe d'infrastructure. La recette vérifie que les quatre du bas sont cohérentes entre elles et avec l'image.</figcaption>
</figure>

### 5.2. Pilote et CUDA : la table de compatibilité

Le guide de compatibilité CUDA établit la règle de la compatibilité de version mineure : depuis CUDA 11, une application compilée avec un toolkit d'une famille majeure peut tourner, avec des fonctionnalités limitées, sur un système dont le pilote est au moins égal au minimum de cette famille.

| Toolkit CUDA | Pilote minimal |
|---|---|
| 13.x | 580 ou plus |
| 12.x | 525 ou plus |
| 11.x | 450 ou plus |

Le paquet de compatibilité ascendante (`cuda-compat-<majeur>-<mineur>`) permet d'exécuter une application construite avec un toolkit plus récent sur un pilote plus ancien, d'une famille majeure à l'autre. La documentation le réserve aux GPU de centre de données, à certaines références RTX « serveur » et aux cartes Jetson.

Le partage des rôles est la clé de lecture : le pilote est une propriété du **nœud**, la version de CUDA une propriété du **job**. L'infrastructure n'a pas la main sur la seconde ; elle doit pouvoir répondre à la question « quelle version de CUDA ce nœud accepte-t-il ? » avant que le job ne la pose.

::: ex
[Exemple 5.1 — Un contrôle de compatibilité en une ligne]{.tag} Le script `labs/provisioning/exercise-calcs/calc.py compat` applique la table. Sorties réelles :

~~~text
$ python3 calc.py compat --driver 570 --cuda 12.9
CUDA 12.9 needs driver >= 525; driver 570 -> OK
$ python3 calc.py compat --driver 570 --cuda 13.0
CUDA 13.0 needs driver >= 580; driver 570 -> TOO OLD
~~~

Un nœud en pilote 570 accepte donc les images CUDA 12 et refuse les images CUDA 13. La recette (chapitre 6) refait ce contrôle dans `check_stack`, pour la version de CUDA que vous déclarez comme cible du site.
:::

### 5.3. Fabric Manager sur les systèmes à NVSwitch

Les serveurs à huit GPU de NVIDIA (plateformes HGX et DGX) relient leurs GPU par des NVSwitch, commutateurs de la liaison GPU à GPU NVLink. Le guide de Fabric Manager (FM) décrit un processus privilégié qui configure ces commutateurs, forme une fabrique mémoire commune entre les GPU participants et surveille les liens NVLink. Le guide indique que l'administrateur doit **activer et démarrer à la main** le service `nvidia-fabricmanager` après une installation par paquets individuels.

Les règles de version sont explicites. Au démarrage, FM vérifie la compatibilité de la pile pilote chargée et s'arrête si elle est incompatible. Sur les systèmes antérieurs à la quatrième génération de NVSwitch (avant NVLink 5), la version de la bibliothèque doit correspondre à celle de FM. À partir de la branche de pilote 620, FM et les composants NVSwitch s'installent indépendamment du pilote, avec une version sémantique propre (2.0.x).

::: war
[Un Fabric Manager de mauvaise version s'arrête]{.tag} Le tableau des dépendances du guide dit, pour les systèmes antérieurs à NVLink 5 : si la version de la bibliothèque `libnvidia-fmdrv.so.1` ne correspond pas à celle de Fabric Manager, FM s'arrête et signale que la version de la bibliothèque n'est pas prise en charge. Une mise à jour partielle, qui ne change que le pilote, peut, par déduction de ce parcours, produire cette situation. Voir le [guide Fabric Manager](https://docs.nvidia.com/datacenter/tesla/fabric-manager-user-guide/index.html).
:::

### 5.4. Les autres services de l'hôte

Trois éléments complètent la liste des contrôles de la recette.

-   **Le démon de persistance** `nvidia-persistenced` : la page *Driver Persistence* de NVIDIA le décrit comme un démon d'espace utilisateur qui maintient l'état du pilote entre deux jobs CUDA, avec une approche plus robuste que le mode de persistance historique ([docs.nvidia.com/deploy/driver-persistence](https://docs.nvidia.com/deploy/driver-persistence/persistence-daemon.html)).
-   **Les conteneurs.** Le guide du NVIDIA Container Toolkit exige d'abord le pilote ; `nvidia-ctk runtime configure --runtime=docker` configure le runtime. Depuis la version 1.18.0, une spécification CDI (*Container Device Interface*, description standard des périphériques exposés aux conteneurs) est générée et tenue à jour par le service `nvidia-cdi-refresh` ; certaines situations demandent toujours une régénération manuelle.
-   **DCGM**, qui fournit le diagnostic de la recette et la surveillance continue (module 14).

### 5.5. Piéger les versions

Trois habitudes évitent la plupart des surprises. Fixez les versions de pilote et de Fabric Manager comme **variables du rôle**, jamais comme « la dernière » ; mettez-les à jour ensemble, dans une mise à jour progressive (chapitre 7) qui se termine par la recette. Enregistrez les versions observées parmi les preuves de recette : le fichier `versions.json` du lab 6.3 en est la trace.

Enfin, testez toute montée de version sur un petit groupe de nœuds de pré-production avant la flotte. Ce n'est pas une règle de NVIDIA, c'est la conclusion pratique du fait que les couches du milieu s'installent séparément et se cassent ensemble.

::: recap
Points clés — chapitre 5

-   Pilote, services, runtime de conteneur : le pilote borne la version de CUDA que les jobs peuvent utiliser (13.x exige 580, 12.x exige 525, 11.x exige 450 selon la table de compatibilité).
-   Sur NVSwitch, FM doit tourner, être démarré à la main, et correspondre à la version du pilote avant NVLink 5.
-   Le démon de persistance, `nouveau` en liste noire et CDI font partie du contrôle d'un nœud.
-   Fixez les versions en variables, mettez-les à jour ensemble et gardez-les parmi les preuves de recette.
:::

## 6. Recette et burn-in : DCGM, gpu-burn, nccl-tests, mémoire, PCIe, NVLink {#ch6}

La recette répond à une question à trois issues : ce nœud peut-il entrer en production (*accept*), faut-il rejouer une partie des tests (*retest*), ou doit-il rester dehors et ouvrir un dossier (*reject*). Ce chapitre décrit les outils qui produisent les preuves, puis les règles qui les transforment en verdict. La logique de décision est testée dans le lab 6.3 ; la collecte sur de vrais GPU ne l'est pas.

### 6.1. Des tests à plusieurs profondeurs

La documentation de DCGM Diagnostics (`dcgmi diag`) propose quatre niveaux d'exécution, `-r 1` à `-r 4`, dont chacun inclut les précédents. Elle les destine à des usages différents : le niveau 1 comme mesure de disponibilité, le niveau 2 comme épilogue après une panne, les niveaux 3 et 4 comme analyse a posteriori par un administrateur.

| Niveau | Durée annoncée (mesurée sur des systèmes Hopper, génération de GPU H100) | Usage documenté |
|---|---|---|
| `-r 1` | moins de 2,5 s | état de préparation |
| `-r 2` | moins de 2,5 min (4 GPU), moins de 10,5 min (8 GPU) | épilogue sur panne |
| `-r 3` | moins de 10 min (4 GPU), moins de 35 min (8 GPU) | diagnostic matériel |
| `-r 4` | moins de 45 min (4 GPU), moins de 2,25 h (8 GPU) | diagnostic matériel long |

Ces durées sont des **bornes supérieures** données par le constructeur pour un modèle de GPU ; mesurez les vôtres. Le choix d'utiliser le niveau 2 à chaque démarrage et le niveau 3 à la réception est un choix de ce parcours, pas une prescription de NVIDIA.

La documentation précise aussi ce que DCGM Diagnostics n'est pas : un outil de diagnostic matériel complet, un outil de réparation, un remplaçant des outils de diagnostic de terrain, ni un support du processus de RMA. Gardez cette limite en tête avant de brandir un résultat `Pass` comme preuve de bonne santé.

### 6.2. Les outils et ce qu'ils prouvent

-   **`dcgmi diag -r N -j`** : tests logiciels (bibliothèques, `nouveau`), PCIe et NVLink, mémoire, bande passante mémoire, puis contraintes de calcul et de puissance aux niveaux supérieurs. L'option `-j` produit du JSON ; le code de sortie 226 signifie « diagnostic exécuté, mais il a signalé une erreur », le 205 « le diagnostic demande d'isoler ».
-   **`gpu_burn`** : sature les GPU pour révéler des défauts sensibles à la chaleur et à la puissance. Options lues dans son README : `-m N%` (part de mémoire), `-d` (doubles), `-tc` (cœurs tensoriels). Il termine par `Tested N GPUs:` suivi de `GPU i: OK` ou `GPU i: FAULTY`.
-   **nccl-tests** : mesure les collectives NCCL et **vérifie les valeurs**. Une collective correcte à la mauvaise vitesse et une collective rapide mais fausse sont deux pannes distinctes.
-   **`nvbandwidth`** : mesure la bande passante de copies entre hôte et GPU et entre GPU. Il complète nccl-tests ; le lab ne l'exécute pas.
-   **`nvidia-smi -q -d PERFORMANCE`** : affiche l'état de performance et les « Clocks Event Reasons » (plafond de puissance logiciel, ralentissement thermique…), qui expliquent un GPU plus lent que ses voisins.
-   **Le journal du noyau** : les erreurs `NVRM: Xid` pendant la recette (codes d'erreur que le pilote NVIDIA écrit dans le journal du noyau). Le catalogue NVIDIA décrit le code 79 comme « GPU has fallen off the bus ».

La bande passante de bus est la grandeur de comparaison de nccl-tests, car l'algorithme de bande passante $S/t$ dépend du nombre de rangs. Pour un all-reduce sur $n$ rangs, la documentation de nccl-tests donne :

$$\text{busbw} = \text{algbw} \times \frac{2(n-1)}{n}, \qquad \text{algbw} = \frac{S}{t}$$

Pour $n = 8$, le facteur vaut $1{,}75$. Le programme peut aussi juger lui-même : si la variable d'environnement `NCCL_TESTS_MIN_BW` est fixée, il marque la moyenne de bande passante de bus comme échouée quand elle tombe sous 0,9 fois cette valeur (lu dans le code source, branche principale, le 24 octobre 2026).

### 6.3. Mémoire du GPU, remappage de lignes et RMA

Les GPU de centre de données remappent les lignes de mémoire HBM (*High Bandwidth Memory*, la mémoire empilée de ces GPU) qui produisent des erreurs non corrigibles. Le guide de gestion des erreurs mémoire de NVIDIA définit deux drapeaux qui gouvernent la recette. Le drapeau *remapping pending* signale qu'un remappage aura lieu à la **prochaine réinitialisation du GPU**. Le drapeau *remapping failure* signale que le matériel ne peut plus remapper.

Le guide énumère les événements qui lèvent le second : une tentative de remappage sur une banque mémoire (*bank*) qui compte déjà huit lignes non corrigibles remappées, sur une ligne déjà remappée, ou après 512 remappages au total. Il précise que le critère de RMA est rempli quand ce drapeau est levé **et validé** par l'outil de diagnostic de terrain de NVIDIA.

Les règles de la recette en découlent : drapeau *failure* levé, rejet et dossier ; drapeau *pending* levé, réinitialisation du GPU (`nvidia-smi -r`) puis nouvelle recette. La documentation de `nvidia-smi` précise que, si Fabric Manager ne tourne pas (ou pour une architecture antérieure à Ampere), les GPU reliés en NVLink à un GPU réinitialisé doivent l'être dans la même commande. Dans le doute, drainez le nœud entier avant toute réinitialisation.

### 6.4. Du faisceau de preuves au verdict

Le script `acceptance.sh` range les preuves dans un répertoire : `smi.csv`, `dcgm.json` et `dcgm.rc`, `nccl.json`, `burn.log`, `xid.log`, `versions.json`. Puis `run_decision.py` applique six règles de contrôle, une par famille de preuves, dont chacune produit des constats de gravité *reject* ou *retest* :

| Règle | Rejet | Rejeu |
|---|---|---|
| pile | pilote trop ancien pour CUDA, FM inactif ou de version différente, `nouveau` chargé | version de CUDA inconnue |
| `nvidia-smi` | nombre de GPU inattendu, drapeau *failure*, erreur ECC (correction d'erreurs de la mémoire) non corrigible, lien PCIe dégradé | drapeau *pending* |
| DCGM | test en échec, sortie 226 ou 205 | outil en erreur, test requis absent |
| nccl-tests | valeurs fausses, bande passante sous 90 % de la référence | entre 90 % et 95 %, ou non lancé en recette complète |
| gpu_burn | un GPU `FAULTY` | non lancé en recette complète |
| journal | toute erreur Xid pendant la recette | |

Le verdict est le pire des constats. Les seuils de ces règles (90 %, 95 %, nombre de GPU, largeur PCIe) sont dans `policy.json` : ce sont des **paramètres de site**, à étalonner sur le nœud doré du chapitre 1. Les valeurs du lab sont rondes à dessein.

::: key
[Un code de retour n'est pas un verdict]{.tag} Ne décidez jamais sur le seul code de sortie d'un outil. Un outil peut terminer proprement en ayant signalé un défaut dans sa sortie, une version peut changer la sémantique d'un code, et un test absent ne se manifeste par aucun code. Le lab teste ce cas : un JSON DCGM dont un test échoue alors que le code vaut 0 est rejeté.
:::

::: ex
[Exemple 6.1 — Trois nœuds, trois verdicts]{.tag} Le lab rejoue des preuves **synthétiques** (aucun GPU, aucun nombre mesuré) à travers `acceptance.sh --fixtures`. Pour chaque scénario, le code de sortie est celui du script et le constat est extrait du JSON de verdict qu'il affiche (sorties réelles, mises en forme sur une ligne) :

~~~text
fixtures/remap_failure   -> exit 1   GPU 3: row-remapping failure flag set (RMA candidate)
fixtures/pending_remap   -> exit 3   GPU 5: remap/retirement pending, takes effect at the next GPU reset: reset then retest
fixtures/nccl_marginal   -> exit 3   bus bandwidth 93.0 GB/s is 93% of the baseline: marginal, run again
fixtures/dcgm_fail_rc0   -> exit 1   DCGM test 'memory' status Fail (entities [4])
~~~

Le jeu de tests compte 30 cas ; la solution de référence les passe tous (`30 passed`) et le squelette `starter/decide.py`, qui accepte tout, en échoue 24 (`24 failed, 6 passed`) : c'est la preuve que les tests discriminent. Vous complétez le squelette au lab 6.3.
:::

### 6.5. Ce que la collecte réelle ajoute, et ce qui reste non vérifié

La branche réelle de `acceptance.sh` (celle qui lance les outils) tient en quelques lignes. L'extrait ci-dessous est simplifié et correspond au niveau `full` ; le niveau `quick` lance `dcgmi diag -r 2` et ne lance ni `gpu_burn` ni nccl-tests.

~~~bash
nvidia-smi --query-gpu="$smi_fields" --format=csv > "$evidence/smi.csv"
dcgmi diag -r 3 -j > "$evidence/dcgm.json" || rc=$?
gpu_burn "$burn_seconds" > "$evidence/burn.log" 2>&1 || true
"$nccl_bin" -b 8 -e 1G -f 2 -g "$gpus" -J "$evidence/nccl.json" > "$evidence/nccl.txt" 2>&1 || true
~~~

Elle a passé `bash -n` et `shellcheck`, et **n'a jamais tourné sur un GPU**. Cinq points y sont à vérifier chez vous : la liste des champs de `nvidia-smi --query-gpu` (contrôlez-la avec `--help-query-gpu`), l'enveloppe exacte du JSON de `dcgmi diag` (la documentation n'en montre qu'un fragment), les noms de clés du JSON de nccl-tests (lus dans le code source de la branche principale, qui peut changer), la version de CUDA runtime et la génération de NVSwitch.

Le script lit ces deux dernières dans des variables d'environnement faute de mieux (`CUDA_RUNTIME_VERSION`, `NVSWITCH_GENERATION`). Sans elles, la version de CUDA vaut `unknown` (verdict *retest*) et le contrôle de Fabric Manager est ignoré : renseignez-les.

::: recap
Points clés — chapitre 6

-   DCGM propose quatre profondeurs de test ; leurs durées sont des bornes constructeur à remesurer, et l'outil ne remplace ni le diagnostic de terrain ni le processus de RMA.
-   nccl-tests donne un débit de bus comparable entre nombres de rangs ($\text{algbw}\times 2(n-1)/n$ pour un all-reduce) et vérifie les valeurs.
-   Le drapeau de remappage *pending* appelle une réinitialisation, le drapeau *failure* appelle un dossier ; les seuils de RMA sont ceux de NVIDIA.
-   Le verdict à trois issues est le pire des constats ; les seuils sont des paramètres de site.
-   La collecte réelle reste à valider sur votre matériel.
:::

## 7. Mises à jour et pannes : rolling updates, firmware, RMA, traçabilité {#ch7}

Une flotte n'est jamais « à jour » une fois pour toutes : noyau, pilote, firmware, configuration changent toute l'année, pendant que des jobs de plusieurs jours occupent les GPU. Ce chapitre traite deux difficultés liées : changer sans interrompre la production, et gérer les nœuds qui tombent malgré tout, jusqu'à leur remplacement sous garantie.

### 7.1. Une mise à jour progressive en cinq temps

Le schéma est toujours le même. On **draine** un lot de nœuds (l'ordonnanceur n'y place plus de job, les jobs en cours finissent), on **change**, on **redémarre**, on **vérifie** par la recette rapide, puis on **remet en service**. Trois garde-fous l'encadrent : un canari en premier lot, une taille de lot bornée par la capacité que vous pouvez perdre, et un arrêt de tout le déploiement au premier échec.

La commande de redémarrage de Slurm applique ce schéma. D'après la documentation de `scontrol`, `reboot` redémarre les nœuds quand ils deviennent inactifs, avec le `RebootProgram` de `slurm.conf`. L'option `ASAP` pose le drapeau `DRAIN` pour empêcher de nouveaux jobs et fixe la raison à « Reboot ASAP ». Après le redémarrage, le programme de contrôle de santé s'exécute **une fois**, puis le nœud s'enregistre.

::: war
[scontrol reboot, sans ASAP, ne bloque pas les nouveaux jobs]{.tag} La page *scontrol* le dit : par défaut, la commande n'empêche pas de nouveaux jobs d'être planifiés sur les nœuds avant le redémarrage. Il faut utiliser `ASAP` ou drainer les nœuds au préalable. Un nœud qui ne s'enregistre pas dans le délai `ResumeTimeout` reçoit la raison « reboot timed out ». Voir [slurm.schedmd.com/scontrol.html](https://slurm.schedmd.com/scontrol.html) (page lue le 24 octobre 2026, version courante de la documentation).
:::

Le playbook `playbooks/production_update.yml` du lab 6.1 écrit le même enchaînement avec Ansible : drain, attente de la fin des jobs, rôle, redémarrage, recette rapide, remise en service, par lots (`serial`) et arrêt au premier échec. C'est une **esquisse de production** : syntaxe vérifiée et passée au linter, jamais exécutée, car elle exige un contrôleur Slurm et de vrais nœuds.

::: ex
[Exemple 7.1 — Combien dure une mise à jour progressive ?]{.tag} Une flotte de 64 nœuds, des jobs de 24 h au plus, un redémarrage suivi de validation de 15 minutes, et la décision de ne jamais retirer plus de 8 nœuds à la fois (12,5 %). Dans le pire cas, chaque lot attend le plus long job, puis redémarre :

$$T_{\text{pire}} = \left\lceil \frac{N}{b} \right\rceil \times \left( T_{\text{job}} + T_{\text{reboot}} \right)$$

Avec $N = 64$ et $b = 8$, il y a 8 lots de 24,25 h. Sortie réelle de `calc.py rolling --nodes 64 --batch 8 --walltime-h 24 --reboot-h 0.25` :

~~~text
nodes=64 batch=8 -> 8 waves
worst case per wave: wait for the longest job (24.0 h) + reboot and validation (0.25 h) = 24.25 h
worst case total   : 194.00 h = 8.08 days
capacity offline   : at most 8/64 = 12.5 % of the nodes at any time
~~~

C'est un **majorant** : en pratique, les jobs ne durent pas tous 24 h et les lots se chevauchent. Il montre surtout le compromis : doubler le lot divise la durée par deux et double la capacité retirée.
:::

### 7.2. Firmware : le plus risqué des changements

Un nœud GPU porte plusieurs firmwares : BIOS, BMC, cartes réseau, GPU, NVSwitch. L'article Llama 3 cite les mises à jour de firmware et de noyau parmi les opérations d'une maintenance automatisée, qui provoque, dans leur exploitation, au moins une interruption d'entraînement par jour. Le coût d'une mise à jour se compte donc aussi en jobs interrompus.

Trois règles de ce parcours, à valider avec vos constructeurs : relever les versions de firmware dans l'inventaire (elles font partie de l'identité d'un nœud) ; ne jamais mettre à jour un firmware sans matrice de compatibilité du constructeur avec le pilote et le BMC ; mettre à jour d'abord le canari, puis rejouer la recette complète, pas seulement la recette rapide. Les outils de mise à jour de firmware ne sont pas couverts ici (voir la section « Sources et portée »).

### 7.3. Pannes, traçabilité, RMA

Un nœud en panne est drainé avec une raison lisible (module 5), puis traité selon une arborescence simple : un défaut logiciel se règle par réinstallation de l'image ; un défaut matériel transitoire par réinitialisation puis recette ; un défaut matériel avéré par remplacement de la pièce ou échange sous garantie. Chaque branche se termine par une recette complète : un nœud réparé n'est pas un nœud qualifié.

Le dossier de RMA se constitue avec les preuves déjà produites : numéro de série du châssis et identifiants des GPU, verdict de recette avec ses constats, rapport DCGM, journal Xid, valeur des drapeaux de remappage. NVIDIA rappelle que la décision revient à son outil de diagnostic de terrain ; votre dossier sert à la déclencher, pas à la remplacer.

La traçabilité sert une seconde fin : repérer les nœuds « citrons » dont les pannes se répètent. Kokolis et al. signalent que l'historique est indispensable pour trouver les nœuds défectueux, et citent parmi les signaux les plus corrélés le nombre de jobs distincts qui ont exclu le nœud, le nombre d'erreurs Xid distinctes et le nombre de tickets de réparation ouverts pour lui. Tenez donc un registre d'événements par nœud (drains, raisons, verdicts, tickets, pièces remplacées), et conservez-le au-delà de la vie de l'image.

### 7.4. Dimensionner un volant de nœuds de rechange

Combien de nœuds de réserve garder pour absorber les pannes pendant qu'on réparait ? Si les nœuds tombent au taux $\lambda$ par nœud et par jour et restent en réparation $T$ jours, la loi de Little donne le nombre moyen de nœuds hors service dans une flotte de $N$ nœuds :

$$\bar{R} = N \cdot \lambda \cdot T$$

Le nombre réel fluctue autour de cette moyenne ; on le modélise par une loi de Poisson de moyenne $\bar{R}$ et l'on retient le plus petit nombre de réserves dont la probabilité de suffire atteint le niveau choisi (95 % ici). Ce modèle suppose des pannes indépendantes : des pannes corrélées (nœuds citrons, panne d'un commutateur) le rendent optimiste.

::: ex
[Exemple 7.2 — Un volant pour 256 nœuds]{.tag} Entrées : un taux de 2,5 pannes pour 1 000 nœuds-jours, du même ordre que les 2,34 publiés par Kokolis et al. pour RSC-2 (6,50 pour RSC-1, avec des périodes jusqu'à environ 17,5), et une réparation de 10 jours, **hypothèse de l'exemple**. Sortie réelle de `calc.py spares` :

~~~text
failures per week  : 256 x 0.0025 x 7 = 4.48
nodes in repair    : mean 6.40 (Little: arrival rate x 10.0 days)
Poisson quantile   : P(in repair <= 11) = 0.969 >= 0.95  -> keep 11 spare nodes
~~~

Soit 11 nœuds de rechange, 4,3 % de la flotte, pour couvrir 95 % des situations avec ces entrées. Contrôle indépendant : avec SciPy, la fonction de répartition de la loi de Poisson de moyenne 6,4 vaut 0,939 en 10 et 0,969 en 11. Avec un taux de pointe de 17,5, la moyenne passerait à 44,8 : le volant se dimensionne sur votre taux **mesuré**, pas sur un ordre de grandeur emprunté.
:::

### 7.5. Retirer un nœud proprement

Le retrait est le dernier état. Il révoque l'identité du nœud : suppression de la ligne `dhcp-host` et de l'entrée d'inventaire (c'est une modification de la carte des nœuds du chapitre 4, relue avant application), retrait de la liste `NodeName=` de Slurm, désactivation des comptes du BMC et effacement des disques selon votre politique de sécurité. L'effacement sécurisé n'est pas couvert par ce module.

::: recap
Points clés — chapitre 7

-   Une mise à jour progressive se fait en cinq temps (drainer, changer, redémarrer, vérifier, remettre) avec un canari, un lot borné et un arrêt au premier échec.
-   `scontrol reboot` sans `ASAP` ne bloque pas les nouveaux jobs ; avec `ASAP`, le nœud est drainé puis redémarré.
-   Le temps de pire cas d'un déploiement par lots vaut le nombre de lots multiplié par la durée du plus long job plus le redémarrage.
-   La recette complète clôt toute réparation ; le registre d'événements par nœud sert le RMA et la détection des nœuds citrons.
-   Le volant de rechange se calcule : moyenne de Little, quantile de Poisson, taux mesuré chez vous.
:::

## 8. BMC, Redfish, IPMI et supervision hors bande {#ch8}

Quand le système d'exploitation ne répond plus, tout ce qui reste est le **BMC** (*baseboard management controller*), un petit ordinateur indépendant embarqué dans le serveur, avec sa propre interface réseau. Il permet d'allumer, d'éteindre, de lire des capteurs et d'ouvrir une console sans passer par le système. C'est aussi, pour cette raison, la porte la plus sensible de la machine.

### 8.1. Ce qu'un BMC permet, et l'outil historique

L'usage le plus courant dans une chaîne de provisionnement est la mise sous tension à distance : MAAS utilise le BMC pour allumer la machine et propose des pilotes d'alimentation dont IPMI et Redfish. Un BMC fournit aussi les capteurs (températures, ventilateurs, alimentations), un journal d'événements matériels et une console série par le réseau. Le projet OpenBMC publie une pile de firmware de BMC ouverte.

L'interface historique est **IPMI**. L'outil `ipmitool` (version 1.8.19 sur Ubuntu 24.04) en expose les commandes : `chassis` (état et alimentation), `sdr` et `sensor` (capteurs), `sel` (journal), `sol` (console par le réseau), `user` (comptes) et `mc` (contrôleur de gestion). Son aide documente les options de connexion (`-I` interface, `-H` hôte, `-U` utilisateur, `-C` suite de chiffrement) et plusieurs manières de passer le mot de passe.

~~~bash
ipmitool -I lanplus -H "$BMC_HOST" -U "$BMC_USER" -E chassis power status
~~~

L'option `-E` lit le mot de passe dans la variable `IPMI_PASSWORD` ; l'option `-P mot-de-passe` le place sur la ligne de commande, où tous les utilisateurs locaux le voient dans la liste des processus. Utilisez `-E` ou `-f fichier`. Cette commande est dans `labs/provisioning/redfish-oob/ipmi_example.sh` ; elle n'a pas été exécutée (aucun BMC), seulement vérifiée par `shellcheck`, et sa syntaxe est celle de l'aide de la version installée.

### 8.2. Redfish : une API REST normalisée

Redfish, publié par le DMTF, est l'interface moderne : HTTP, JSON, hypermédia. La spécification DSP0266 (version 1.22.0, 5 février 2025) fixe que l'URL racine d'un service Redfish 1.x est `/redfish/v1/` et que le service ne doit pas exiger d'authentification pour la servir. Elle exige que toute requête avec authentification Basic passe en HTTPS ; l'authentification par session est l'alternative.

Le client découvre les ressources en suivant les liens (`@odata.id`) à partir de la racine, sans coder en dur `/Systems/1` : les constructeurs diffèrent. Dans le schéma des ressources du DMTF, la santé d'un composant (`Status.Health`) prend l'une des valeurs `OK`, `Warning`, `Critical`, et `HealthRollup` agrège celle des sous-composants. L'action `ComputerSystem.Reset` annonce dans la ressource les valeurs de `ResetType` qu'elle accepte (par exemple `GracefulShutdown`, `ForceRestart`, `PowerCycle`).

::: ex
[Exemple 8.1 — Un client Redfish contre un BMC simulé]{.tag} Le lab 6.4 lance `mock_bmc.py`, un **simulateur** qui suit ces chemins et ces noms, avec une santé forcée à `Critical`, et interroge-le avec `redfish_client.py`. Sorties réelles (Python 3.13, 2026-10-24) :

~~~text
/redfish/v1/Systems/1: power=On health=Critical rollup=Critical
/redfish/v1/Chassis/1: power=None health=Critical rollup=Critical
worst=Critical action=drain
OK wrong password: exit 2 (error: 401 on /redfish/v1/Systems)
~~~

Le code de sortie 1 signifie « agir » (`drain` pour `Critical`, `watch` pour `Warning`), le 2 « erreur » (mauvais mot de passe, BMC injoignable). Neuf tests couvrent : racine lisible sans authentification, ressources protégées, verdict selon la pire santé, valeur inconnue traitée comme avertissement, `Reset` refusé côté client s'il sort de la liste annoncée, et refusé côté serveur si on force la requête.

**Limites.** Le simulateur parle HTTP, ce que la spécification interdit pour l'authentification Basic ; le client n'a jamais été lancé contre un vrai BMC ; sessions, événements et extensions constructeur sont hors du simulateur.
:::

### 8.3. Du signal hors bande à une décision

Le BMC voit ce que le système ne voit pas : une alimentation redondante défaillante, un ventilateur arrêté, une température critique, un nœud figé. La règle de ce parcours est de **ne jamais agir automatiquement au-delà du drain**. Un `Critical` ou un `Warning` persistant draine le nœud avec une raison ; un humain, ou une procédure documentée et limitée en fréquence, décide du redémarrage.

Quand le nœud est figé, le BMC est le seul chemin : arrêt progressif d'abord, puis redémarrage forcé, puis coupure et remise sous tension, du moins brutal au plus brutal. Chaque escalade s'inscrit dans le registre d'événements du chapitre 7 : un nœud qu'on doit couper trois fois est un candidat à la recette complète, pas un nœud « réparé ».

### 8.4. Sécuriser le BMC

Un BMC compromis donne le contrôle du serveur sous le système d'exploitation, y compris son firmware. Les pratiques de ce parcours, **non sourcées ici** car les pages de guidance des agences que nous avons tenté de lire ont refusé l'accès depuis le bac à sable : réseau de gestion isolé et non routable depuis les réseaux utilisateurs, aucun compte par défaut conservé, mots de passe uniques par machine et hors du dépôt (chapitre 3), HTTPS avec certificats vérifiés, interfaces inutilisées désactivées, et firmware du BMC tenu à jour comme n'importe quel autre.

::: recap
Points clés — chapitre 8

-   Le BMC est un ordinateur indépendant : il allume, éteint, lit les capteurs et sert de dernier recours.
-   IPMI est l'interface historique (`ipmitool`) ; passez le mot de passe par `-E` ou `-f`, jamais `-P`.
-   Redfish : racine `/redfish/v1/` sans authentification, Basic uniquement en HTTPS, santé `OK`, `Warning` ou `Critical`, action de reset annoncée avec ses valeurs permises.
-   Le signal hors bande draine ; il ne redémarre pas seul.
-   Le réseau de gestion est isolé, les identifiants sont uniques et secrets.
:::

## Labs {#labs}

Les quatre labs tournent sur un portable ou une VM Linux **sans GPU**, n'exigent pas les droits root (seule l'installation des paquets en a besoin) et ne touchent jamais la configuration de la machine : chaque nœud est un répertoire temporaire. Les outils utilisés ont été testés le 24 octobre 2026 avec Python 3.13, ansible-core 2.21.5, ansible-lint 26.10.1, Terraform 1.16.7 (fournisseur `hashicorp/local` 2.9.1), dnsmasq 2.91 et shellcheck. Installation préalable :

~~~bash
python3 -m venv .venv && . .venv/bin/activate
pip install ansible-core ansible-lint yamllint pytest
sudo apt-get install -y dnsmasq-base shellcheck
# Terraform >= 1.6 : binaire officiel sur releases.hashicorp.com, vérifié par la somme SHA-256
~~~

Chaque lab se lance avec `PYTHON=$(which python) bash verify.sh` depuis son dossier `labs/provisioning/<lab>/`. Les scripts n'affirment rien sur la durée d'exécution : ils comptent des changements, des codes de sortie et des lignes de fichier.

::: lab
[Lab 6.1 — Un rôle Ansible de nœud de calcul]{.tag}

**Objectif.** Faire converger trois nœuds simulés avec un rôle idempotent, détecter et corriger une dérive, déployer par lots avec un canari et protéger un secret. **Durée.** 3 h (partie A 1,5 h, partie B 1,5 h). **Prérequis matériels.** Portable CPU, Python et ansible-core ; coût nul ; aucun root.

1.  Partie A. Lisez `roles/gpu_node/tasks/main.yml` et `handlers/main.yml` : repérez chaque `notify` et le mécanisme `node_root`.
2.  Lancez deux fois `playbooks/site.yml` avec `-e lab_root=$(mktemp -d)` et relevez `changed` dans chaque récapitulation.
3.  Remplacez `unlimited` par `1` dans un fichier géré, puis lancez `--check --diff --limit gpu-n02` : le fichier doit rester tel quel. Corrigez avec une exécution réelle.
4.  Partie B. Lancez `playbooks/rolling.yml`, puis ajoutez `-e fail_host=gpu-n01` et vérifiez que les deux autres nœuds ne reçoivent rien.
5.  Générez un secret, chiffrez-le avec `ansible-vault encrypt_string` et déployez `playbooks/secrets.yml` avec `--diff` : le secret ne doit apparaître ni dans la sortie ni ailleurs que dans un fichier `0600`. Retirez ensuite `no_log: true` et constatez la fuite.
6.  Relancez deux fois `site.yml` avec `-e gpu_node_stamp=true` : c'est le défaut d'idempotence de l'exercice 4.
7.  Lisez `playbooks/production_update.yml` (drain, attente, rôle, redémarrage, recette rapide, remise en service), sans l'exécuter.

**Critère de réussite.** `bash verify.sh` sort avec le code 0 et affiche `OK idempotence: changed=0 and the action log did not grow (3 lines)` puis, en dernière ligne, `OK ansible-node-role: converge, idempotence, check-mode drift, rolling abort, vaulted secret`. Ce sont des compteurs et des contenus de fichier, jamais des durées. Comptez environ une minute.

**Pour aller plus loin.** Passez `gpu_node_service_backend: systemd` sur une VM jetable avec systemd et vérifiez que les gestionnaires lancent les vraies commandes. Ajoutez un test Molecule si vous le connaissez (non couvert ici).
:::

::: lab
[Lab 6.2 — Terraform : une flotte décrite en code]{.tag}

**Objectif.** Dériver d'une seule carte des nœuds l'inventaire Ansible, la configuration DHCP et PXE, le script iPXE et les lignes Slurm ; lire un plan ; provoquer et corriger une dérive. **Durée.** 3 h. **Prérequis matériels.** Portable CPU, Terraform 1.6 ou plus, accès au registre pour télécharger `hashicorp/local` 2.9.1 (version épinglée dans `versions.tf`, une seule fois) ; dnsmasq et ansible-core pour deux contrôles facultatifs.

1.  Lisez `modules/fleet/variables.tf` : les cinq règles de validation de la carte des nœuds.
2.  Dans `modules/fleet`, lancez `terraform init -backend=false`, `validate`, `test`, et lisez `tests/fleet.tftest.hcl`.
3.  Dans `envs/prod`, appliquez avec `-var output_dir=<répertoire>` et inspectez les cinq fichiers produits ; passez `prod-dnsmasq.conf` à `dnsmasq --test -C`.
4.  Ajoutez une ligne à la main à `prod-dhcp-hosts.conf`, lancez `plan -detailed-exitcode` (code 2), puis appliquez.
5.  Retirez `cpu-n01` de `terraform.tfvars` et lisez le résumé `Plan:` (exercice 5).
6.  Dupliquez une adresse MAC et lisez le message de validation.

**Critère de réussite.** `bash verify.sh` sort avec le code 0, affiche `dnsmasq: syntax check OK.` et `OK removing cpu-n01 destroys its record (1) and replaces the 4 node-dependent files (4 destroy + 4 add); dnsmasq.conf does not depend on the node list`, puis `OK terraform-fleet: validate, test, apply, idempotence, drift, node removal, input validation`. Environ dix secondes une fois le fournisseur en cache. **Aucun démarrage PXE n'est testé :** seuls la syntaxe de dnsmasq et la structure du script iPXE sont vérifiées.

**Pour aller plus loin.** Remplacez `local_file` par le fournisseur `canonical/maas` sur un MAAS de test (non couvert), ou ajoutez un environnement `staging`. Testez le démarrage réel avec une VM et un bridge isolé si vous disposez de KVM.
:::

::: lab
[Lab 6.3 — Recette d'un nœud GPU]{.tag}

**Objectif.** Écrire et tester les règles de décision d'une recette (accepter, rejouer, refuser) à partir de preuves ; connaître la collecte réelle. **Durée.** 3 h (partie A 1,5 h, partie B 1,5 h). **Prérequis matériels.** Portable CPU et pytest pour tout sauf l'étape 6 ; **un nœud GPU avec DCGM, gpu-burn et nccl-tests pour l'étape 6, non vérifiée et facultative**.

1.  Partie A. Lisez `acceptance.sh` et `policy.json` : les sept fichiers de preuves, les trois codes de sortie, les seuils de site.
2.  Lancez `bash verify.sh`, puis rejouez à la main `acceptance.sh --fixtures fixtures/<scénario>` pour `remap_failure`, `pending_remap`, `nccl_marginal`, `dcgm_fail_rc0` et `multi`.
3.  Lisez `lib/parsers.py` et `reference/decide.py` ; repérez la table de compatibilité CUDA et les codes 226 et 205.
4.  Partie B. Remplissez `starter/decide.py` jusqu'à ce que `IMPL=starter python -m pytest tests` passe.
5.  Ajoutez un scénario à `make_fixtures.py` (par exemple des erreurs ECC corrigibles seulement) et le test qui l'accompagne.
6.  Facultatif, sur matériel : lancez `./acceptance.sh --level quick`, comparez le verdict à votre attente et corrigez les écarts de format (champs de `nvidia-smi`, enveloppe JSON de DCGM).

**Critère de réussite.** `bash verify.sh` sort avec le code 0, affiche `30 passed` pour la solution de référence, une ligne `starter (failures expected): ... failed ...` pour le squelette, les verdicts `good -> exit 0`, `remap_failure -> exit 1` et `nccl_marginal -> exit 3`, puis `OK node-acceptance (replay branch): decision rules proven on synthetic evidence`. **Le lab porte le type `gpu` et le badge « non vérifié » :** la branche de rejeu est vérifiée, la collecte réelle ne l'est pas, et le script le rappelle en dernière ligne (`NOT EXECUTED: live branch on real GPUs`).

**Pour aller plus loin.** Ajoutez un compteur de rejeux par nœud (au troisième *retest*, rejeter), puis branchez le verdict sur `scontrol update state=drain` (module 5).
:::

::: lab
[Lab 6.4 — Supervision hors bande avec Redfish]{.tag}

**Objectif.** Interroger un BMC simulé par Redfish, décider de drainer sur sa santé et n'accepter qu'un reset annoncé par le service. **Durée.** 1,5 h. **Prérequis matériels.** Portable CPU, Python 3 et pytest ; aucun BMC.

1.  Lisez `mock_bmc.py` : les chemins, la racine sans authentification, la liste `ResetType@Redfish.AllowableValues`.
2.  Lisez `redfish_client.py` : découverte par liens, pire santé, valeurs inconnues traitées comme avertissement, mot de passe en variable d'environnement.
3.  Lancez `python -m pytest tests`.
4.  Démarrez le simulateur en arrière-plan avec `--health Critical`, interrogez-le avec le client et relevez le code de sortie ; arrêtez le processus que vous avez lancé.
5.  Ajoutez une règle (par exemple, un `PowerState` éteint sur un nœud censé tourner) avec son test.

**Critère de réussite.** `bash verify.sh` sort avec le code 0 et affiche `9 passed`, `worst=Critical action=drain`, `OK exit status 1 = drain advised`, puis `OK redfish-oob: client logic proven against a SIMULATED service (never against a real BMC)`. Le simulateur parle HTTP, par commodité : n'envoyez jamais d'identifiants réels sans HTTPS.

**Pour aller plus loin.** Remplacez le simulateur par l'émulateur de votre constructeur s'il en publie un, ou par un vrai BMC de test, avec HTTPS et un compte dédié en lecture seule.
:::

## Exercices {#ex}

Les chiffres des énoncés marqués « fictifs » sont inventés pour l'exercice. Les calculs des corrigés sont refaits par `bash labs/provisioning/exercise-calcs/verify.sh`.

::: exo
[Exercice 1 · ★★ — Le MTTF d'un gros job]{.tag} Kokolis et al. rapportent, sur leurs deux clusters de recherche, un MTTF de 47,7 jours pour les jobs de 8 GPU et de 7,9 h pour les jobs de 1 024 GPU. Si les pannes étaient indépendantes et de même taux par GPU, le MTTF d'un job de $N$ GPU vaudrait $\text{MTTF}(8)\times 8/N$.

(a) Calculez la prédiction pour 1 024 GPU. (b) Comparez-la à la mesure. (c) En supposant des pannes sans mémoire à la cadence de 7,9 h, combien d'interruptions attendez-vous pendant un job de 1 024 GPU de 72 h ? (d) Qu'en déduisez-vous pour la valeur d'une recette ?
:::

::: sol
(a) 47,7 jours valent $47{,}7\times 24 = 1\,144{,}8$ h, donc la prédiction est $1\,144{,}8\times 8/1024 = 8{,}94$ h.

(b) La mesure, 7,9 h, vaut 0,88 fois la prédiction : les pannes sont un peu plus fréquentes que ne le prévoit l'indépendance. Le rapport du nombre de GPU est 128, celui des MTTF 145 : même ordre de grandeur, donc le modèle en $1/N$ est une bonne approximation de premier ordre. Que l'écart vienne de pannes corrélées ou de composants partagés est une hypothèse que ces deux chiffres ne permettent pas de trancher.

(c) $72/7{,}9 = 9{,}1$ interruptions attendues en trois jours.

(d) À ce rythme, chaque nœud à défaut latent qu'on écarte avant le premier job supprime des interruptions, et chacune coûte la reprise depuis le dernier point de sauvegarde sur 1 024 GPU. Les points (a) et (b) se refont avec `calc.py mttf --ref-gpus 8 --ref-days 47.7 --gpus 1024 --measured-hours 7.9`.
:::

::: exo
[Exercice 2 · ★ — Ordre de démarrage et boucle]{.tag} Remettez dans l'ordre les six événements : (a) iPXE exécute un script, (b) le firmware demande une adresse DHCP, (c) le binaire iPXE est téléchargé par TFTP, (d) le DHCP renvoie l'URL d'un script, (e) le noyau et l'*initrd* sont téléchargés par HTTP, (f) Linux démarre.

Un nœud recharge iPXE en boucle sans jamais atteindre le noyau. Quelle est la cause la plus probable et quelle ligne de `dnsmasq.conf` du lab 6.2 la corrige-t-elle ?
:::

::: sol
L'ordre est (b), (c), puis iPXE refait un DHCP, (d), (a), (e), (f).

La cause est que le serveur DHCP répond à la **seconde** requête, celle d'iPXE, par le nom du binaire iPXE au lieu de l'URL d'un script : iPXE se recharge indéfiniment. C'est le cas décrit par la documentation d'iPXE.

La parade se lit dans `modules/fleet/templates/dnsmasq.conf.tftpl`. La ligne `dhcp-match=set:ipxe,175` marque les clients qui envoient l'option 175 (iPXE). Les lignes `dhcp-boot=tag:!ipxe,…` ne servent le binaire qu'aux autres clients, et `dhcp-boot=tag:ipxe,http://…/prod-boot.ipxe` donne à iPXE l'URL de son script. Si la ligne `tag:ipxe` manque, ou si les lignes du binaire n'ont pas `tag:!ipxe`, la boucle apparaît.
:::

::: exo
[Exercice 3 · ★★★ — Choisir un outil de provisionnement]{.tag} Pour chacun de ces trois contextes, recommandez MAAS, Warewulf, Base Command Manager ou « image générique plus Ansible », et justifiez par trois critères et par le coût caché du choix. (a) Un laboratoire, 32 nœuds HGX, deux administrateurs, Ubuntu, Slurm. (b) Une plateforme de 600 nœuds, six ingénieurs, images construites en intégration continue à partir de conteneurs. (c) Un déploiement de nœuds DGX pour lequel un support éditeur est exigé par contrat.

N'inventez aucun chiffre : vous disposez des faits du chapitre 2.
:::

::: sol
Il n'y a pas de réponse unique ; voici une réponse défendable, avec ce qu'il resterait à vérifier.

(a) **Image générique plus Ansible**, ou MAAS si l'équipe veut un inventaire matériel et une mise sous tension par le BMC. Critères : peu d'administrateurs donc peu d'outils à apprendre ; Ubuntu est déjà le système cible ; la flotte est assez petite pour qu'une dérive se corrige par `--check`. Coût caché : la discipline d'idempotence repose sur l'équipe.

(b) **Warewulf**. Critères : les images viennent déjà de l'intégration continue, et la documentation de Warewulf les décrit comme gérables avec des outils de conteneurs ; le sans-état rend le remplacement trivial ; l'échelle du parc justifie une chaîne d'image. Coût caché : l'état local se reconstruit à chaque démarrage, et le pilote GPU est figé dans l'image, donc toute montée de pilote est une nouvelle image.

(c) **Base Command Manager**. Critères : la contrainte de support éditeur domine ; l'outil est documenté pour le déploiement sur DGX ; il couvre provisionnement, charges et supervision. Coût caché : produit propriétaire dont il faut relire les conditions de licence le jour de l'achat, et dépendance à l'écosystème de l'éditeur.

Une bonne réponse nomme à chaque fois ce qu'elle abandonne, et ce qu'il faut tester avant de s'engager (le temps de reconstruction d'un nœud, par exemple).
:::

::: exo
[Exercice 4 · ★ — Lire un PLAY RECAP]{.tag} Voici la sortie **réelle** d'une seconde exécution du lab 6.1 avec `-e gpu_node_stamp=true` (extrait, 2026-10-24) :

~~~text
TASK [gpu_node : Raise per-process limits for training jobs] ****
 # revision unset
-# generated 2026-10-24 22:53:13.022874
+# generated 2026-10-24 22:53:19.423646
 * - memlock unlimited
changed: [gpu-n01]

gpu-n01 : ok=6 changed=1 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
~~~

(a) Quelle ligne explique `changed=1` ? (b) Pourquoi est-ce un défaut pour une flotte de 200 nœuds ? (c) Proposez deux corrections.
:::

::: sol
(a) La ligne `# generated …` : le gabarit y insère l'heure courante (`now()`), donc le contenu rendu diffère à chaque exécution et le module `template` signale un changement.

(b) La seconde exécution ne vaudra jamais `changed=0` : on ne peut plus distinguer une exécution à vide d'une vraie dérive. Une surveillance fondée sur `changed>0` alerte en permanence, ou on la désactive, et une dérive réelle passe inaperçue. La flotte n'est jamais « convergée ».

(c) Première correction : retirer l'horodatage du gabarit ; la révision de configuration (`gpu_node_config_revision`), constante entre deux exécutions, suffit à tracer la version. Seconde : si une date est utile, la consigner dans un journal que le rôle n'écrase pas, par exemple le journal d'actions, et non dans un fichier géré. Vérification : deux exécutions de suite donnent `changed=0`. L'étape G de `verify.sh` fait reproduire le défaut pour que vous le reconnaissiez.
:::

::: exo
[Exercice 5 · ★ — Lire un plan Terraform]{.tag} Après avoir retiré `cpu-n01` de la carte des nœuds de l'environnement `prod`, `terraform plan` affiche (extrait réel, Terraform 1.16.7) :

~~~text
  # module.fleet.local_file.ansible_inventory must be replaced
  # module.fleet.local_file.boot_ipxe must be replaced
  # module.fleet.local_file.dhcp_hosts must be replaced
  # module.fleet.local_file.slurm_nodes must be replaced
  # module.fleet.terraform_data.node["cpu-n01"] will be destroyed
  # (because key ["cpu-n01"] is not in for_each map)
Plan: 4 to add, 0 to change, 5 to destroy.
~~~

(a) Que détruit-on, et pourquoi 5 destructions pour 4 créations ? (b) Pourquoi le fichier `dnsmasq.conf` n'apparaît-il pas ? (c) Que changerait-il si les nœuds étaient des instances d'un nuage ? (d) Quelle garde mettez-vous en intégration continue ?
:::

::: sol
(a) On détruit l'enregistrement du nœud (`terraform_data.node["cpu-n01"]`) et on remplace quatre fichiers qui dépendent de la liste des nœuds : chaque remplacement compte une destruction et une création. Cinq destructions, quatre créations.

(b) `dnsmasq.conf` ne mentionne aucun nœud : son contenu ne change pas.

(c) Une destruction y serait **réelle** : l'instance et ses disques disparaîtraient. D'où la règle du chapitre 4 : relire le résumé `Plan:` et ne modéliser que des enregistrements pour les machines physiques.

(d) Exécuter `terraform plan -detailed-exitcode` ; le code 2 est normal, mais on refuse la fusion si le nombre de destructions dépasse ce que la demande annonce, ou on exige une approbation humaine dès qu'une ressource de type machine apparaît dans la liste. Rappelez-vous que `prevent_destroy` ne protège pas d'un retrait de la configuration.
:::

::: exo
[Exercice 6 · ★ — Compatibilité pilote et CUDA]{.tag} Quatre nœuds ont les pilotes 535, 550, 570 et 580. Trois images utilisent CUDA 11.8, 12.4 et 13.0. Avec la table de compatibilité du chapitre 5, dressez la matrice des paires acceptées.

Sur un HGX de troisième génération de NVSwitch, le pilote est en 580.0.1 et le paquet Fabric Manager en 575.0.1. Que prévoit la documentation ? Une équipe exige CUDA 13.0 sur le nœud en pilote 570 : donnez deux options.
:::

::: sol
Les minima sont 450 pour CUDA 11, 525 pour CUDA 12, 580 pour CUDA 13. Les pilotes 535, 550 et 570 acceptent CUDA 11.8 et 12.4 et refusent CUDA 13.0 ; le pilote 580 accepte les trois. Contrôle : `calc.py compat --driver 570 --cuda 13.0` répond `TOO OLD`, et `--driver 570 --cuda 12.9` répond `OK`.

Avant NVLink 5, la version de la bibliothèque doit correspondre à celle de Fabric Manager : avec 580.0.1 et 575.0.1, FM s'arrête et signale que la version de la bibliothèque n'est pas prise en charge. Il faut aligner les deux versions (le lab 6.3 rejette ce cas avec `fm_mismatch`).

Pour CUDA 13.0 sur le pilote 570 : (1) mettre le pilote à 580 ou plus, par une mise à jour progressive suivie de la recette ; (2) si le GPU est un GPU de centre de données, installer le paquet de compatibilité ascendante `cuda-compat` correspondant, que la documentation réserve à certains matériels. Dans les deux cas, testez sur un canari.
:::

::: exo
[Exercice 7 · ★★ — Lire la sortie d'une recette]{.tag} Voici le verdict **réel** de `acceptance.sh --fixtures fixtures/multi` (preuves synthétiques) :

~~~text
{ "findings": [
  { "message": "GPU 2: PCIe link gen5 x8 below gen5 x16", "severity": "reject" },
  { "message": "GPU 5: remap/retirement pending, takes effect at the next GPU reset: reset then retest", "severity": "retest" },
  { "message": "bus bandwidth 93.0 GB/s is 93% of the baseline: marginal, run again", "severity": "retest" } ],
  "verdict": "reject" }
~~~

(a) Pourquoi le verdict est-il *reject* alors que deux constats sont des *retest* ? (b) Dans quel ordre traitez-vous les trois constats ? (c) Peut-on conclure que le lien PCIe dégradé explique la bande passante ?
:::

::: sol
(a) Le verdict est le pire des constats : un seul rejet suffit, car on ne remet pas en production un nœud qui a une panne avérée, quels que soient les autres constats.

(b) D'abord le rejet : un lien PCIe négocié en x8 au lieu de x16 est une cause physique ou de configuration (carte mal enfichée, riser, réglage du BIOS) qu'une réinitialisation ne corrige pas ; vérifiez l'état du lien avec `lspci -vv`. Ensuite seulement, la réinitialisation du GPU 5 pour que le remappage en attente prenne effet, puis la **recette complète rejouée**, car le défaut corrigé peut avoir modifié les autres résultats.

(c) Non. Rien dans ces preuves ne l'établit : une collective NCCL entre GPU reliés en NVLink ne traverse pas le lien PCIe de la même façon. C'est une hypothèse à tester en rejouant : si la bande passante reste marginale après correction du lien, c'est une autre cause.
:::

::: exo
[Exercice 8 · ★★ — Bande passante de bus]{.tag} Rappel : pour un all-reduce sur $n$ rangs de $S$ octets en un temps $t$,

$$\text{algbw} = \frac{S}{t}, \qquad \text{busbw} = \text{algbw}\times\frac{2(n-1)}{n}$$

avec 1 GiB = $2^{30}$ octets et 1 GB = $10^{9}$ octets. La référence du site (nœud doré, valeur **fictive**) est de 200 GB/s de bande passante de bus. La politique du lab : accepter à 95 % ou plus, rejouer entre 90 % et 95 %, rejeter sous 90 %.

Un all-reduce de 4 GiB sur 8 GPU prend 36 ms sur un nœud et 41 ms sur un autre. Calculez algbw, busbw, le pourcentage de la référence et le verdict de chacun. Quel serait le facteur sur 16 rangs, et pourquoi compare-t-on le busbw plutôt que l'algbw ?
:::

::: sol
Pour 36 ms : $S = 4\times 2^{30} = 4{,}295\times 10^{9}$ octets, algbw $= 4{,}295\times 10^{9}/0{,}036 = 119{,}3$ GB/s. Le facteur vaut $2\times 7/8 = 1{,}75$, donc busbw $= 208{,}8$ GB/s, soit 104 % de la référence : *accept*.

Pour 41 ms : algbw $= 104{,}8$ GB/s, busbw $= 183{,}3$ GB/s, soit 92 % : entre 90 % et 95 %, donc *retest*.

Sur 16 rangs le facteur est $2\times 15/16 = 1{,}875$. On compare le busbw parce que l'algbw dépend du nombre de rangs : à matériel identique, il diminue quand $n$ augmente, alors que le busbw reflète l'usage des liens indépendamment de $n$ (documentation de nccl-tests). Les valeurs sortent de `calc.py busbw --ranks 8 --size-gib 4 --ms 36 --baseline 200` (et `--ms 41`).
:::

::: exo
[Exercice 9 · ★★★ — Un nœud intermittent]{.tag} Un nœud passe la recette cinq fois de suite avec ces bandes passantes de bus, en pourcentage de la référence : 98, 97, 91, 96, 89. Les autres nœuds de la flotte donnent 98 avec un écart-type d'environ 1 point (valeurs **fictives**). Le diagnostic DCGM de niveau 3 est propre et aucun Xid n'est apparu.

Qualifiez la situation, listez des hypothèses ordonnées, proposez pour chacune un test discriminant, et fixez une règle de décision. Précisez ce que cinq mesures ne permettent pas de conclure.
:::

::: sol
**Situation.** En écarts à 98 : 0, −1, −7, −2, −9 points, soit 0, 1, 7, 2 et 9 écarts-types de la flotte. Deux mesures sur cinq sont très loin du bruit habituel : ce n'est pas du bruit de mesure, et ce nœud n'est pas comme les autres. Cinq mesures ne suffisent pas pour estimer une fréquence de panne ni pour distinguer deux causes ; elles justifient seulement de ne pas accepter le nœud.

**Hypothèses (non démontrées), avec le test qui les départage.**

1.  Limitation thermique ou de puissance : lire les *Clocks Event Reasons* de `nvidia-smi -q -d PERFORMANCE` pendant une charge soutenue, comparer les températures à celles des voisins.
2.  Lien dégradé ou instable (PCIe, NVLink, réseau) : relire les compteurs d'erreurs et l'état des liens, mesurer par paires avec `nvbandwidth`.
3.  Interférence d'un autre processus sur le nœud : vérifier qu'aucun job ni service n'occupe les GPU pendant la recette.
4.  Défaut matériel intermittent : diagnostic de niveau 4 et gpu-burn prolongé, puis échanger les composants suspects de place pour voir si le défaut suit la pièce.

**Règle de décision.** Une règle écrite d'avance, de la forme « trois recettes complètes consécutives à 95 % ou plus avant remise en service ; au-delà de cinq essais, rejet et ouverture d'un dossier ». Les seuils sont un choix de site. Conservez les cinq mesures dans le registre d'événements du nœud : un nœud revenu deux fois pour le même motif est un candidat « citron ».
:::

::: exo
[Exercice 10 · ★★ — Dimensionner une mise à jour progressive]{.tag} Une flotte de 120 nœuds, des jobs de 48 h au plus, un redémarrage plus validation de 20 minutes (0,333 h) : valeurs **fictives**. Vous ne pouvez pas retirer plus de 10 % des nœuds à la fois. Formule du pire cas, avec $N$ nœuds et des lots de $b$ nœuds :

$$T = \left\lceil \frac{N}{b} \right\rceil \times \left( T_{\text{job}} + T_{\text{reboot}} \right)$$

(a) Calculez la taille de lot et la durée de pire cas. (b) Combien gagne-t-on en doublant le lot, et à quel prix ? (c) Proposez une manière de réduire le pire cas sans retirer plus de capacité.
:::

::: sol
(a) Le lot maximal est $b = 12$ nœuds (10 % de 120). Il y a $\lceil 120/12\rceil = 10$ lots de $48{,}333$ h, soit $483{,}3$ h $= 20{,}1$ jours.

(b) Avec $b = 24$, il y a 5 lots, soit $241{,}7$ h $= 10{,}1$ jours : la durée est divisée par deux, mais 20 % de la capacité est retirée à la fois. C'est un compromis de politique, pas un calcul.

(c) Le pire cas suppose que chaque lot attend un job de 48 h. On le réduit en limitant la durée maximale des jobs d'une partition le temps de la mise à jour, en planifiant les lots sur les nœuds dont les jobs se terminent le plus tôt, ou en réservant une fenêtre de maintenance annoncée aux utilisateurs. Les valeurs viennent de `calc.py rolling --nodes 120 --batch 12 --walltime-h 48 --reboot-h 0.3333` (et `--batch 24`).
:::

::: exo
[Exercice 11 · ★★★ — Remplacer un nœud et dimensionner le volant]{.tag} Dans une flotte de 256 nœuds, le client Redfish d'un nœud renvoie `Critical` et le journal du noyau contient une erreur Xid 79. Rédigez la procédure de remplacement sans interrompre la production : étapes ordonnées, qui agit, quelles preuves sont conservées, quel retour en arrière, et quelle recette précède la remise en service.

Dimensionnez ensuite le volant de nœuds de rechange pour un taux de 2,5 pannes pour 1 000 nœuds-jours et un délai de réparation de **21 jours** (RMA lent, valeur fictive), à 95 %. Comparez à 10 jours et expliquez ce que vous arbitrez.
:::

::: sol
**Procédure.**

1.  Drainer le nœud avec une raison lisible (`scontrol update … state=drain reason=…`) ; les jobs en cours finissent ou sont repris depuis leur point de sauvegarde. Responsable : l'automatisation, sur le signal du client Redfish et du journal Xid.
2.  Geler les preuves : rapport DCGM, journal Xid, valeur des drapeaux de remappage, numéros de série et identifiants des GPU, historique des drains du nœud.
3.  Substituer un nœud de rechange recetté, en l'ajoutant à la carte des nœuds (relue, plan lu), pour que Slurm voie la capacité revenir.
4.  Réinitialiser le GPU si le diagnostic l'autorise, puis recette complète. Si elle échoue ou si le défaut revient, ouvrir le dossier de remplacement avec les preuves de l'étape 2.
5.  À l'arrivée de la pièce, réparer, puis **recette complète** avant tout retour en service ; consigner l'événement dans le registre du nœud.
6.  Retour en arrière : tant que la recette échoue, le nœud reste drainé ; rien n'est supprimé de la carte avant le remplacement définitif.

**Volant.** Avec 10 jours, la moyenne de nœuds en réparation vaut $256\times 0{,}0025\times 10 = 6{,}4$ et 11 réserves couvrent 95 % des cas (probabilité cumulée 0,969). Avec 21 jours, la moyenne passe à 13,44 et il en faut 20 (probabilité 0,966) : 7,8 % de la flotte au lieu de 4,3 %.

**Arbitrage.** Chaque réserve est de la capacité payée et inactive ; raccourcir le délai de RMA (contrat, stock de pièces sur site) coûte aussi. La comparaison se fait en nœuds-équivalents : 9 réserves de plus contre un meilleur délai de réparation. Le prix de chaque option se lit sur la page du fournisseur le jour de la décision, pas ici. Calcul : `calc.py spares --nodes 256 --rate-per-1000-node-days 2.5 --repair-days 21 --quantile 0.95`.
:::

## Checkpoint de sortie {#exit}

Un checkpoint n'est pas un examen : c'est la liste de ce que vous devez pouvoir produire ou expliquer, avec la preuve attendue.

-   **Je peux décrire la chaîne de démarrage d'un nœud et la dépanner.** Preuve : le schéma du chapitre 2 refait de mémoire, avec la panne probable à chaque étape, et l'exercice 2.
-   **Je peux écrire un rôle Ansible dont la seconde exécution donne `changed=0`.** Preuve : le lab 6.1, avec votre propre tâche ajoutée et la récapitulation des deux passes.
-   **Je peux déployer un changement par lots et l'arrêter au premier échec.** Preuve : le lab 6.1, partie B, avec le canari en échec.
-   **Je peux décrire une flotte avec Terraform et lire un plan.** Preuve : le lab 6.2 et l'exercice 5 refaits sur un nouveau nœud.
-   **Je peux vérifier la cohérence de la pile GPU d'un nœud.** Preuve : `check_stack` complété au lab 6.3 et l'exercice 6.
-   **Je peux concevoir une recette à trois issues.** Preuve : `starter/decide.py` complété jusqu'à ce que les tests passent, et un scénario supplémentaire de votre cru.
-   **Je peux dimensionner une mise à jour et un volant de rechange.** Preuve : les exercices 10 et 11 refaits sur des chiffres de votre flotte.
-   **Je peux interroger un BMC par Redfish et en tirer une décision.** Preuve : le lab 6.4 et la règle ajoutée.

Trois questions d'entretien à traiter en deux minutes chacune.

1.  *Vous recevez 64 nœuds GPU neufs. Que faites-vous avant d'ouvrir la production ?* Réponse-type : inventaire d'identité (série, MAC, BMC), installation par image, convergence idempotente prouvée (`changed=0`), vérification de la pile (pilote, CUDA, Fabric Manager), recette complète (DCGM, burn-in, nccl-tests comparé à un nœud doré, journal des Xid), verdict à trois issues, remise en service progressive par un canari, et conservation des preuves.
2.  *Comment mettez-vous à jour le pilote de 500 nœuds pendant que les jobs tournent ?* Réponse-type : mise à jour progressive en lots bornés par la capacité acceptable, canari en premier, drain avec attente de la fin des jobs, redémarrage, recette rapide, remise en service, arrêt au premier échec ; estimation du pire cas ; fenêtre annoncée aux utilisateurs.
3.  *Un nœud tombe toutes les semaines puis « revient tout seul ». Que faites-vous ?* Réponse-type : ne pas se fier au retour spontané ; consulter le registre d'événements (drains, Xid, tickets) ; recette complète et plus longue ; comparer aux autres nœuds ; au-delà d'un seuil écrit d'avance, retrait et dossier de remplacement : c'est un candidat « nœud citron ».

## Lectures et références {#refs}

-   Dubey et al. [*The Llama 3 Herd of Models*](https://arxiv.org/abs/2407.21783), 2024, section 3.3.4 et tableau 5 : interruptions, causes et maintenance automatisée (chapitres 1 et 7).
-   Kokolis et al. [*Revisiting Reliability in Large-Scale Machine Learning Research Clusters*](https://arxiv.org/abs/2410.21680), 2024 : taux de pannes, MTTF selon la taille du job, nœuds citrons (chapitres 1 et 7).
-   NVIDIA. [*DCGM Diagnostics*](https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/dcgm-diagnostics.html), guide utilisateur de DCGM : niveaux, JSON, codes de sortie (chapitre 6).
-   NVIDIA. [*CUDA Compatibility*](https://docs.nvidia.com/deploy/cuda-compatibility/latest/) : compatibilité de version mineure et ascendante (chapitre 5).
-   NVIDIA. [*Fabric Manager User Guide*](https://docs.nvidia.com/datacenter/tesla/fabric-manager-user-guide/index.html) : démarrage, version, systèmes à NVSwitch (chapitre 5).
-   NVIDIA. [*GPU Memory Error Management*](https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/latest/index.html) : remappage de lignes, drapeaux et critères de RMA (chapitres 6 et 7).
-   NVIDIA. [*nccl-tests — performance metrics*](https://raw.githubusercontent.com/NVIDIA/nccl-tests/master/doc/PERFORMANCE.md) : algbw, busbw (chapitre 6).
-   Ansible. Sources de la documentation : [mode vérification](https://raw.githubusercontent.com/ansible/ansible-documentation/devel/docs/docsite/rst/playbook_guide/playbooks_checkmode.rst), [gestionnaires](https://raw.githubusercontent.com/ansible/ansible-documentation/devel/docs/docsite/rst/playbook_guide/playbooks_handlers.rst), [mises à jour progressives](https://raw.githubusercontent.com/ansible/ansible-documentation/devel/docs/docsite/rst/playbook_guide/guide_rolling_upgrade.rst) et [glossaire](https://raw.githubusercontent.com/ansible/ansible-documentation/devel/docs/docsite/rst/reference_appendices/glossary.rst) pour l'idempotence (chapitre 3).
-   HashiCorp. [*terraform plan*](https://developer.hashicorp.com/terraform/cli/commands/plan) et [*lifecycle*](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle) : codes de sortie, `prevent_destroy` (chapitre 4).
-   Projet iPXE. [*Chainloading iPXE*](https://ipxe.org/howto/chainloading) et [*Scripting*](https://ipxe.org/scripting) : boucle d'amorçage et scripts (chapitre 2).
-   Warewulf. [*The Provisioning Process*](https://warewulf.org/docs/main/getting-started/provisioning.html) et Canonical, [*MAAS : commissioning et déploiement*](https://canonical.com/maas/docs/stable/explanation/deploying-machines/) : deux chaînes de provisionnement documentées (chapitre 2).
-   DMTF. [*Redfish Specification DSP0266 1.22.0*](https://www.dmtf.org/sites/default/files/standards/documents/DSP0266_1.22.0.pdf), 2025 : racine, authentification, hypermédia (chapitre 8).
-   SchedMD. [*scontrol*](https://slurm.schedmd.com/scontrol.html) : `reboot`, `ASAP`, `nextstate` (chapitre 7).
-   LBNL. [*Node Health Check (NHC)*](https://raw.githubusercontent.com/mej/nhc/master/README.md) : contrôle de santé de référence pour Slurm (chapitres 6 et 7).

## Sources et portée {#sources}

**Documenté.** Les faits attribués à une source ont été relus sur la page indiquée le 24 octobre 2026 : chiffres de fiabilité de Llama 3 (466, 47, 419 interruptions sur 54 jours ; 78 % attribuées au matériel) et de Kokolis et al. (6,50 et 2,34 pannes pour 1 000 nœuds-jours sur RSC-1 et RSC-2, MTTF de 7,9 h à 1 024 GPU contre 47,7 jours à 8 GPU, 40 nœuds citrons, jusqu'à 50-75 % de bande passante perdue à la mise en service) ; niveaux et durées annoncées de `dcgmi diag`, option `-j`, codes de sortie 226 et 205 ; table de compatibilité CUDA (450, 525, 580) ; règles de version de Fabric Manager ; drapeaux et seuils de remappage de lignes ; formule du débit de bus et variable `NCCL_TESTS_MIN_BW` ; sémantique de `scontrol reboot` ; racine `/redfish/v1/`, authentification Basic et énumérations de santé du DMTF ; chaîne de démarrage de Warewulf, déploiement de MAAS, boucle d'iPXE, codes de sortie de `terraform plan`, limite de `prevent_destroy`. Les sorties citées viennent des labs, exécutés sur Python 3.13, ansible-core 2.21.5, ansible-lint 26.10.1, Terraform 1.16.7, `hashicorp/local` 2.9.1, dnsmasq 2.91 et ipmitool 1.8.19 (aide locale).

**Recommandé.** Les sept états du cycle de vie ; la recette en trois issues et ses seuils (90 % et 95 %) ; le nœud doré comme référence ; la règle « pas d'action automatique au-delà du drain » pour les signaux du BMC ; les répertoires plutôt que les espaces de travail Terraform ; la lecture humaine du résumé `Plan:` ; le registre d'événements par nœud ; l'usage du niveau 2 de DCGM à chaque démarrage et du niveau 3 à la réception ; les pratiques de sécurité du BMC. Ce sont des choix de ce parcours, pas des règles des outils.

**À vérifier.** (1) La liste des champs de `nvidia-smi --query-gpu` et l'enveloppe du JSON de `dcgmi diag` : la documentation ne montre qu'un fragment. (2) Les clés du JSON de nccl-tests, lues dans le code source de la branche principale : le format évolue. (3) Les valeurs de l'option DHCP 93 annoncées par vos firmwares UEFI (7 ou 9). (4) Le chemin PXE de bout en bout : aucune machine n'a démarré sur les fichiers générés. (5) Le client Redfish n'a jamais parlé à un vrai BMC. (6) Les pages de guidance sur la sécurité d'IPMI et des BMC (NSA, CISA, spécification Intel) ont refusé l'accès depuis le bac à sable : les pratiques de la section 8.4 ne sont donc pas sourcées. (7) Les limites attribuées à MAAS, Warewulf et BCM sont des déductions ; les conditions de licence de BCM sont à relire le jour de l'achat. (8) Les durées de DCGM sont des bornes mesurées par NVIDIA sur des systèmes Hopper. (9) Les critères de RMA couvrent les GPU listés par NVIDIA ; consultez le contrat de votre fournisseur. (10) Les pages de la documentation d'Ansible renvoyaient une erreur 429 : leurs sources ont été lues dans le dépôt `ansible-documentation`. (11) Le comportement de `hashicorp/local` face à un fichier modifié est une observation sur la version 2.9.1.

**Hors périmètre.** La configuration de Slurm elle-même ([module 5](../slurm/index.html)), le réseau d'interconnexion et NCCL en profondeur ([module 7](../networking/index.html)), la supervision continue des GPU ([module 14](../observability/index.html)), l'opérateur GPU de Kubernetes ([module 12](../kubernetes-gpu/index.html)), la construction d'images (Packer, intégration continue), les outils de mise à jour de firmware, le démarrage sécurisé et l'attestation, l'effacement sécurisé des disques, les API de provisionnement des nuages, OpenTofu, OpenCHAMI, OpenStack Ironic et xCAT (cités sans évaluation), et les partitions multi-locataires de NVSwitch.
