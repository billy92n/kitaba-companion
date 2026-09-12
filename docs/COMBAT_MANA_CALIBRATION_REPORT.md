# Kitaba — calibration combat / mana (MVP candidate)

Status: **PROPOSAL / calibration candidate**. Ce rapport ne remplace pas le MASTER stable et n’altère aucune campagne existante.

## Objectif

Vérifier que la première base combat/ressources produit des écarts lisibles sans introduire de level scaling, de sacs à PV artificiels ou de mort arbitraire.

Référence de calibration : personnage à 100 HP. Les valeurs servent à comparer des ordres de grandeur ; elles ne signifient pas que tous les êtres du monde ont 100 HP.

## 1. Impact brut représentatif

Avec une réussite normale et sans protection :

| Impact de référence | Dégâts | Gravité par impact | Coups identiques pour épuiser 100 HP* |
| --- | ---: | --- | ---: |
| faible | 12 | serious | 9 |
| standard | 25 | critical | 4 |
| lourd | 35 | critical | 3 |
| dévastateur | 50 | catastrophic | 2 |

\* Ce nombre n’est **pas** une durée de combat garantie : esquive, échec, réussite partielle, localisation fictionnelle, fuite, état de choc, reddition et blessures peuvent arrêter un affrontement avant 0 HP.

### Lecture

Le modèle ne cherche pas à rendre chaque combat long. Un coup réellement lourd reste dangereux. À l’inverse, un impact faible n’élimine pas normalement une cible saine en un ou deux échanges.

## 2. Protection fixe

Exemple avec un impact standard de 25 :

- protection 0 → 25 dégâts ;
- protection 4 → 21 ;
- protection 8 → 17 ;
- protection 12 → 13.

Un impact faible de 8 contre protection 8 peut être entièrement absorbé.

Cette propriété est intentionnelle : une bonne armure doit réellement changer le type de menace crédible au lieu de fournir un simple petit bonus en pourcentage. En revanche, la protection ne doit s’appliquer que lorsque la fiction justifie que l’armure, le bouclier ou la défense couvre effectivement l’impact.

## 3. Maîtrise et résolution

La cible ne gagne pas artificiellement des HP parce que l’attaquant est plus puissant. La maîtrise modifie surtout la probabilité et la qualité de la résolution.

Pour un impact de base 25 contre protection 4 :

| Cible de réussite cachée | Dégâts moyens par tentative (échecs inclus) |
| ---: | ---: |
| 35 | 9,54 |
| 55 | 14,00 |
| 75 | 18,46 |

Le combattant plus compétent convertit donc davantage de tentatives en dégâts utiles sans que le monde soit recalibré autour de lui.

## 4. Réussite exceptionnelle

Un impact 25 contre protection 8 :

- réussite normale → 17 dégâts, blessure `serious` ;
- réussite exceptionnelle → 30 dégâts, blessure `critical`.

Une réussite exceptionnelle peut franchir un palier de gravité si la fiction permet effectivement un meilleur placement, une ouverture ou un impact supérieur. Elle ne crée pas automatiquement une décapitation ou une mort instantanée.

## 5. Zéro HP et mortalité

`0 HP` signifie d’abord **incapacitation** dans la référence candidate.

La mort n’est jamais déduite uniquement du chiffre. Un `death_risk` apparaît lorsque la source était réellement létale ou que la gravité de l’impact le justifie. Le MJ doit ensuite résoudre les conséquences selon la blessure, les soins possibles, le temps écoulé et la situation.

Ceci maintient ensemble :

- conséquences réelles ;
- absence de plot armor ;
- absence de mort arbitraire provoquée par un simple compteur.

## 6. Mana

Pour une réserve maximale de 100, les bandes candidates coûtent :

- trivial : 1 ;
- light : 3 ;
- moderate : 7 ;
- heavy : 12 ;
- major : 20 ;
- extreme : 35.

Pour une réserve maximale de 40 : light 1, moderate 3, heavy 5, major 8.

Le coût proportionnel représente l’effort relatif pour une réserve donnée. Il ne transforme pas le nombre de sorts lancés en XP : progression et dépense de mana restent deux systèmes différents.

## 7. Surcanalisation

Le déficit est mesuré relativement au mana maximal :

- jusqu’à 5 % → `strain` ;
- jusqu’à 15 % → `injury_risk` ;
- jusqu’à 30 % → `severe_injury_risk` ;
- jusqu’à 50 % → `coma_risk` ;
- au-delà → `death_risk`.

Le surcanalage n’est donc pas une réserve gratuite secondaire. Il permet de forcer une action au prix d’un risque corporel cohérent avec le canon Genesis.

## 8. Points encore ouverts avant promotion

La base est cohérente pour un MVP de simulation, mais ne doit pas encore être promue telle quelle sans les décisions suivantes :

1. relier les catégories d’impact aux armes, monstres, sorts et situations réelles ;
2. préciser quand la protection s’applique partiellement ou pas du tout ;
3. calibrer fatigue, saignement, stabilisation et récupération ;
4. définir les interactions entre blessures persistantes et HP récupérables ;
5. vérifier plusieurs profils corporels / espèces sans faire de niveau global ;
6. tester des affrontements complets incluant fuite, reddition et désengagement plutôt que seulement des échanges de dégâts.

## Conclusion de calibration

Aucun défaut structurel n’impose pour l’instant de remplacer la base :

- les écarts faible / standard / lourd sont perceptibles ;
- l’armure peut réellement neutraliser les petites menaces ;
- la maîtrise améliore les résultats sans level scaling ;
- les critiques augmentent le danger sans imposer une mort automatique ;
- le surcanalage possède une escalade de risque claire.

La prochaine calibration doit porter sur **récupération / blessures persistantes / rythme d’un affrontement complet** avant promotion dans le MASTER.
