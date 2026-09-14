# Kitaba — couche éditoriale « livre de campagne » (DRAFT)

Status: **PROPOSAL**. Cette couche est dérivée du canon mais ne doit jamais devenir canon par simple reformulation.

## Objectif

Pendant la partie, Kitaba privilégie l'interaction : réponses courtes, actions fréquentes, dialogues vivants. Le livre final ne doit donc pas être obtenu en concaténant le chat brut.

La solution est une couche éditoriale séparée : après une scène suffisamment complète, le système peut produire un passage narratif propre, traçable vers les événements canoniques qui l'ont inspiré.

## Séparation stricte

Trois objets différents :

1. **Canon de campagne** : faits persistants utilisés par le MJ pour continuer la partie.
2. **Journal joueur** : résumé fonctionnel de ce qui s'est réellement passé.
3. **Couche éditoriale** : prose lisible comme un récit, dérivée de faits déjà canoniques.

Une belle phrase, une émotion supposée ou un détail ajouté dans la prose ne crée jamais un nouveau fait de campagne.

## Unité de capture : `EditorialScene`

Chaque scène éditoriale possède :
- identifiant stable ;
- titre ;
- type de scène ;
- plage de révisions canoniques source ;
- texte éditorial ;
- identifiants des événements/journaux sources ;
- participants connus ;
- lieu ;
- illustrations associées éventuelles.

L'implémentation de référence est dans `reference/story_system.py`.

## Quand fermer une scène

Une scène n'est pas découpée par nombre de messages. On ferme lorsqu'un changement structurel survient :
- changement significatif de lieu ;
- objectif immédiat résolu ;
- saut temporel important ;
- transition tonale majeure ;
- fin de scène explicitement reconnue.

Cela évite de produire un « chapitre » toutes les trois réponses.

## Fusion éditoriale

Deux petites scènes consécutives peuvent être réunies pour la lecture si :
- leur ordre canonique est continu ;
- elles se passent dans le même contexte ;
- elles ne cassent pas une scène d'action majeure ;
- aucun fait n'est déplacé ou réécrit.

La fusion modifie seulement la présentation du livre, jamais les révisions sources.

## Illustrations

Une scène éditoriale peut référencer les assets déjà connus : portrait, lieu ou illustration de scène. Les images réutilisent les identités visuelles établies.

Le livre final pourra ainsi alterner :
- texte ;
- illustrations ;
- cartes ou extraits de carte ;
- interludes/chapitres.

## Export futur

Ordre de priorité proposé :
1. HTML autonome lisible ;
2. PDF correctement paginé ;
3. EPUB si la structure de chapitres est suffisamment stable.

L'export n'est pas requis pour le MVP de démonstration immédiat. En revanche, la structure éditoriale doit être définie dès maintenant pour éviter que le futur livre dépende du transcript brut des chats.

## Critère de sécurité narrative

Toute scène éditoriale doit pouvoir répondre à : « de quels événements canoniques ce passage provient-il ? »

Si aucune source canonique n'est identifiable, le passage ne doit pas être traité comme un souvenir fiable de la campagne.
