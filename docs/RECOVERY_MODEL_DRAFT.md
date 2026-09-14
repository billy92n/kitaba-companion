# Kitaba — récupération HP et blessures persistantes (DRAFT)

Status: **PROPOSAL**. Cette couche ne remplace pas le MASTER stable.

## Principe

Les HP représentent surtout la capacité immédiate à continuer à agir et encaisser. Les blessures graves restent des entités séparées et persistantes.

Un repos peut donc rendre une partie des HP sans faire disparaître une fracture, une plaie profonde ou une séquelle. Cela évite à la fois :

- le « sommeil magique » qui annule toute conséquence ;
- l’obligation de rester plusieurs semaines à 3 HP alors que le personnage est stabilisé ;
- la confusion entre fatigue de combat et dommage corporel durable.

## Qualité du repos

Fraction de HP max récupérable par repos long sûr avant effet des blessures :

- `poor` : 8 % ;
- `normal` : 15 % ;
- `excellent` : 25 % ;
- `medical` : 35 %.

`medical` signifie un vrai contexte de soins pertinent, pas simplement dormir dans une chambre chère.

## Frein des blessures

Multiplicateur appliqué au repos :

- aucune / négligeable : ×1,00 ;
- mineure : ×0,90 ;
- sérieuse : ×0,65 ;
- critique : ×0,35 ;
- catastrophique : ×0,10.

Exemple à 100 HP max, 20 HP actuels, repos normal :

- aucune blessure persistante → +15 HP ;
- blessure sérieuse → +10 HP ;
- blessure critique → +5 HP.

La blessure reste enregistrée jusqu’à ce que le temps, les soins, la magie de guérison autorisée et la fiction justifient son évolution.

## Stabilisation et mort

Cette fonction de récupération ne s’applique qu’après stabilisation et repos sûr. Elle ne sauve pas automatiquement un personnage en train de saigner, inconscient dans une zone hostile ou soumis à un `death_risk`.

La stabilisation reste une résolution distincte basée sur :

- gravité ;
- délai avant traitement ;
- compétence du soignant ;
- matériel ;
- magie disponible ;
- environnement ;
- nouvelles blessures éventuelles.

## Conséquences longues

Une blessure peut produire indépendamment des HP :

- pénalité contextuelle ;
- incapacité temporaire ;
- besoin d’attelle, repos ou chirurgie ;
- cicatrice ;
- séquelle permanente lorsque la fiction et la gravité le justifient.

Aucune de ces conséquences ne doit être supprimée parce que la barre HP est remontée.

## Cible de rythme

Pour une campagne solo interactive, l’objectif est :

- récupération perceptible après un vrai repos ;
- impossibilité de remettre immédiatement à neuf un personnage gravement blessé ;
- possibilité de poursuivre l’histoire avec des blessures qui influencent les choix ;
- absence de grind de repos arbitraire.

Ce modèle devra être testé avec le futur système de voyage, car bivouac, météo, sécurité, nourriture et soins disponibles déterminent la qualité réelle du repos.
