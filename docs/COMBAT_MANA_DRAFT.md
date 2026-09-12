# Kitaba — combat, blessures et mana (DRAFT)

Status: **PROPOSAL / calibration candidate**. Ce modèle n'est pas encore promu dans le MASTER et ne modifie pas la campagne en cours.

## Principes

- pas de level scaling : le monde ne devient pas artificiellement plus fort avec le protagoniste ;
- HP numériques possibles dans l'interface, mais les blessures restent des états séparés et narrativement importants ;
- une attaque réussie ne signifie pas automatiquement une blessure grave : arme, protection, résilience et qualité du résultat comptent ;
- atteindre 0 HP signifie incapacité ; le risque de mort dépend aussi de la nature de la blessure/source et doit rester réel ;
- la magie dépense la réserve personnelle de mana ; le surcanalage peut provoquer blessure, coma ou mort ;
- aucune récupération n'est gratuite ou instantanée par défaut : le contexte détermine la vitesse.

L'implémentation de référence se trouve dans `reference/combat_resources.py`.

## Dommages

Un impact possède un `base_harm` propre à l'attaque réelle. Il est ensuite modulé par la qualité de la réussite :

- réussite partielle : environ 65 % de l'impact nominal ;
- réussite normale : 100 % ;
- réussite exceptionnelle : jusqu'à 150 % lorsque fictionnellement possible.

La protection et la résilience réduisent ensuite le dommage. Une bonne armure peut donc annuler un impact faible sans rendre le porteur invulnérable aux attaques lourdes.

## Blessures par impact

La gravité d'une blessure dépend de la fraction de la réserve maximale perdue en **un seul impact**, pas du niveau global du personnage :

- <5 % : négligeable ;
- 5–11 % : mineure ;
- 12–24 % : sérieuse ;
- 25–39 % : critique ;
- ≥40 % : catastrophique.

Ces catégories doivent ensuite produire des conséquences adaptées au type réel de blessure : saignement, mobilité, douleur, perte de conscience, cicatrice, etc. Elles ne remplacent pas la description fictionnelle.

## 0 HP et mort

0 HP = personnage hors d'état de continuer normalement.

La mort n'est ni automatiquement évitée ni automatiquement imposée par une abstraction. Une source réellement létale ou une blessure critique/catastrophique à 0 HP crée un `death_risk`. La résolution suivante dépend de la situation : nature de la blessure, délai de secours, soins disponibles, etc.

Aucun plot armor ne doit annuler un risque de mort établi.

## Mana

Le coût d'une technique est défini relativement à la réserve personnelle :

- trivial : ~1 % ;
- léger : ~3 % ;
- modéré : ~7 % ;
- lourd : ~12 % ;
- majeur : ~20 % ;
- extrême : ~35 %.

Ces bandes sont des outils de calibration, pas des prix universels de sorts. Une technique donnée peut recevoir un coût fixe cohérent après apprentissage/calibration.

## Surcanalage

Si le coût dépasse le mana restant, l'action est impossible sauf si le personnage tente réellement un surcanalage autorisé par le système.

Déficit par rapport au mana maximum :

- ≤5 % : strain ;
- ≤15 % : risque de blessure ;
- ≤30 % : risque de blessure sévère ;
- ≤50 % : risque de coma ;
- >50 % : risque de mort.

Le surcanalage n'ajoute pas de mana gratuit : il transforme un déficit énergétique en risque corporel réel.

## Récupération

La fonction de référence ne fixe volontairement pas une vitesse universelle. Elle applique seulement une fraction décidée par la fiction et bornée par le maximum.

La vitesse finale doit tenir compte du repos, de l'alimentation, des blessures, de l'environnement, de l'entraînement et d'éventuels soins. Les valeurs définitives seront calibrées avec les règles de voyage/repos.

## À valider avant promotion

- tester plusieurs profils de combattants et protections ;
- vérifier qu'un combat ordinaire n'est ni une loterie mortelle permanente ni une attrition sans conséquence ;
- tester créatures beaucoup plus fortes/faibles sans level scaling ;
- calibrer soins, stabilisation et durée des blessures ;
- relier les coûts de mana aux techniques réelles du jeu ;
- tester surcanalage, coma et mort sans transformer cela en mécanique exploitable.
