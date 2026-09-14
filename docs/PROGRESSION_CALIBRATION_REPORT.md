# Kitaba — rapport de calibration progression / résolution

Status: **PROPOSAL VALIDATION REPORT**. Les chiffres restent hors canon tant qu'ils ne sont pas promus dans le MASTER.

## Résolution d100 — bandes vérifiées exhaustivement

Le moteur teste chaque résultat 1–100, sans simulation aléatoire approximative.

Pour une cible de 40 :
- 4 % réussite exceptionnelle ;
- 36 % réussite normale ;
- 15 % réussite partielle ;
- 45 % échec.

Pour une cible de 55 :
- 5 % réussite exceptionnelle ;
- 50 % réussite normale ;
- 15 % réussite partielle ;
- 30 % échec.

Pour une cible de 75 :
- 7 % réussite exceptionnelle ;
- 68 % réussite normale ;
- 15 % réussite partielle ;
- 10 % échec.

La réussite partielle reste une bande stable de 15 points tant qu'elle est fictionnellement possible. Cela réduit la sensation binaire succès/échec sans transformer les actions difficiles en réussite automatique.

## Exemples de cibles

- non entraîné + tâche routinière : 55 ;
- compétent + tâche standard : 55 ;
- compétent + tâche difficile : 40 ;
- expert + tâche difficile : 60 ;
- maître + tâche extrême : 40 ;
- maître + tâche presque impossible : 25.

Le plancher 5 % et le plafond 95 % évitent à la fois l'impossibilité mathématique totale et la réussite absolument garantie lorsqu'une résolution est réellement nécessaire. Une action physiquement impossible n'est pas jetée : elle échoue avant la résolution.

## Progression — rythme de base vérifié

Seuils cachés proposés :
- Novice : 0–39 LP ;
- Apprenti : 40–119 ;
- Compétent : 120–299 ;
- Confirmé : 300–649 ;
- Expert : 650–1199 ;
- Maître : 1200+.

Avec une expérience `demanding` réussie à 4 LP :
- 10 événements formateurs distincts atteignent Apprenti ;
- 30 atteignent Compétent ;
- 75 atteignent Confirmé ;
- 163 environ atteignent Expert ;
- 300 atteignent Maître.

Avec des situations `severe` réellement formatrices à 10 LP :
- 4 atteignent Apprenti ;
- 12 atteignent Compétent ;
- 30 atteignent Confirmé ;
- 65 atteignent Expert ;
- 120 atteignent Maître.

Cela permet une amélioration visible assez tôt tout en réservant les hauts niveaux à une vraie histoire de pratique.

## Enseignement

Un défi difficile avec bon professeur vaut 9 LP au lieu de 7 dans le cas de base. Cinq sessions difficiles distinctes avec bon enseignement suffisent donc à faire passer une compétence neuve à Apprenti, sans permettre de sauter rapidement plusieurs niveaux.

## Anti-farming

Pour une même pratique difficile répétée sans nouveauté :
- première occurrence : 7 LP ;
- seconde : 4 LP ;
- troisième : 2 LP ;
- suivantes dans la même fenêtre/contextualité : 0 LP.

Total d'une série identique prolongée : 13 LP, donc toujours Novice.

Le farming répétitif ne permet donc pas de transformer mécaniquement le temps de jeu en maîtrise sans nouveaux problèmes, nouvelles contraintes, feedback ou progression réelle de l'entraînement.

## Échec et apprentissage

- échec instructif difficile : 6 LP ;
- échec peu instructif difficile : 2 LP ;
- réussite partielle difficile : 7 LP ;
- réussite exceptionnelle difficile : 8 LP.

Le système récompense ce qui est appris, pas seulement ce qui réussit. L'échec ne devient néanmoins pas une méthode d'XP supérieure à la réussite.

## Présentation au joueur

Les LP exacts restent cachés par défaut. Le Companion/MJ peut afficher :
- niveau qualitatif ;
- ce que la compétence permet réellement ;
- ressenti de progression : `début de palier`, `en progression`, `bien établi`, `proche d’un nouveau palier`.

La règle évite un comportement de grind piloté par une barre d'XP tout en conservant une mécanique reproductible pour le MJ.

## Verdict provisoire

Le modèle est suffisamment cohérent pour poursuivre le playtest comme **candidate mécanique**, mais il ne doit pas encore être déclaré LOCKED_CANON. Les points à observer pendant la partie réelle sont :
- sensation de progression sur plusieurs sessions ;
- fréquence réelle des événements qui méritent un gain ;
- risque de progression trop rapide via une succession artificielle de défis `severe` ;
- adéquation entre niveau qualitatif affiché et capacités fictionnelles ;
- interaction future avec magie, combat, blessures et entraînement long.
