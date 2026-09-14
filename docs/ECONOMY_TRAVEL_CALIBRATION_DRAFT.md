# Kitaba — économie & voyage (DRAFT de calibration)

Status: **PROPOSAL**. Ce document ne fixe encore ni monnaie canonique ni prix officiels dans le MASTER stable.

## Pourquoi une unité interne

Le MASTER v1.4 laisse volontairement OPEN les monnaies, salaires et niveaux de prix. Cela ne doit toutefois pas permettre au MJ de faire coûter un repas 3 unités un jour et l’équivalent d’une arme le lendemain.

Le MVP utilise donc une **unité de valeur interne** uniquement pour préserver les rapports économiques. Cette unité n’est pas un nom de monnaie du monde et n’est normalement pas affichée au joueur. Lorsqu’un État ou une région reçoit plus tard sa monnaie canonique, le Companion/MJ peut convertir ce référentiel vers les pièces réellement utilisées localement.

### Ancrages de départ candidats

Repères internes :

- repas simple : 15 ;
- rations d’une journée : 35 ;
- lit commun : 40 ;
- chambre sûre correcte : 75 ;
- journée de travail non qualifié : 100 ;
- journée de travail qualifié : 220 ;
- vêtements courants : 300 ;
- outil courant : 250 ;
- arme simple : 700 ;
- arme martiale : 1 200 ;
- armure basique : 2 200 ;
- cheval de selle : 8 000.

Ce sont des **relations de pouvoir d’achat candidates**, pas une reconstitution historique. Elles doivent être playtestées.

## Variation locale

Deux modificateurs suffisent au MVP :

- coût régional : ×0,5 à ×2,0 ;
- rareté/pénurie : ×0,7 à ×3,0.

Le prix de référence reste stable ; le contexte local explique la variation. Un siège, une mauvaise récolte ou l’isolement peuvent donc renchérir la nourriture sans réécrire tout le système économique.

Les ressources issues de monstres ou de donjons utilisent toujours le **réseau des Guildes** pour une transaction commerciale légale, conformément au canon verrouillé.

## Voyage

La carte interactive indique la géographie mais ses pixels ne deviennent pas automatiquement des kilomètres. Une route durable doit recevoir une distance fictionnelle cohérente (`distance_km` ou équivalent) lorsqu’elle devient pertinente.

Allures journalières candidates en bonnes conditions :

- à pied : 25 km/j ;
- monté : 40 km/j ;
- caravane : 24 km/j ;
- bateau fluvial : 65 km/j ;
- navire à voile : 120 km/j.

Le terrain puis la météo puis le rythme modifient cette base. Exemple à pied : route ×1,10 ; forêt ×0,75 ; montagne ×0,50 ; marais ×0,45. Une tempête vaut ×0,55 et une marche forcée ×1,25 mais augmente fortement la fatigue.

## Fatigue et camp

La vitesse supplémentaire n’est jamais gratuite. La marche forcée ajoute davantage de pression de fatigue ; neige, montagne, marais, tempête et conditions sévères s’additionnent.

La qualité réelle du camp doit ensuite alimenter le modèle de récupération : mauvais bivouac, repos normal, excellent repos ou soins médicaux ne rendent pas les mêmes HP.

## Rencontres de voyage

Le système ne force pas un combat aléatoire par tranche de kilomètres. Il produit seulement un petit nombre maximal de **checks de risque significatifs** selon durée et danger, plafonné pour éviter le spam de rencontres. Un check peut aboutir à : rien, découverte, problème logistique, événement social, météo, prédateur, banditisme ou autre conséquence cohérente.

Le monde ne scale pas avec le PJ : une route sûre reste généralement sûre ; traverser une zone extrême reste dangereux même pour un personnage faible ou fort.

## Avant promotion dans le MASTER

À valider en playtest :

1. pouvoir d’achat sur plusieurs profils sociaux ;
2. prix d’équipement et coût d’un voyage réel ;
3. économie de la Guilde pour les ressources de monstres/donjons ;
4. rythme d’un trajet de plusieurs jours sans surcharge de microgestion ;
5. interaction fatigue ↔ repos ↔ blessures ;
6. monnaies régionales seulement après définition politique/géographique suffisante.
