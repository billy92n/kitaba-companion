# Kitaba — ambiance musicale adaptative (DRAFT)

Status: **PROPOSAL**. Ce document définit le comportement attendu du MJ et du futur lecteur musical. Il ne garantit pas encore une intégration de lecture automatique dans ChatGPT ou le Companion.

## Objectif

La musique doit créer une ambiance continue, pas commenter chaque phrase. Le MJ maintient un `music_state` de scène et ne le change que lorsqu'un vrai changement de ton le justifie.

## États MVP proposés

- `silence` : aucun accompagnement souhaité ;
- `home_warmth` : foyer, famille, sécurité, quotidien chaleureux ;
- `peaceful_exploration` : marche, découverte calme, voyage léger ;
- `wonder` : émerveillement, révélation positive, lieu extraordinaire ;
- `mystery` : énigme, doute, secret, étrangeté ;
- `tension` : menace latente, poursuite prudente, conflit verbal ;
- `danger` : menace immédiate avant ou hors combat ;
- `combat` : affrontement actif ;
- `sorrow` : deuil, perte, tristesse lourde ;
- `triumph` : victoire, accomplissement ou résolution forte.

Ces états décrivent une **fonction émotionnelle**, pas un morceau précis. Le lecteur peut donc changer de piste ou réutiliser une ambiance cohérente sans modifier le canon.

## Anti-churn

Le MJ ne change pas la musique à chaque message.

- même état proposé : conserver la piste ;
- véritable changement de scène : transition immédiate autorisée ;
- saut tonal important, par exemple calme → combat : transition immédiate autorisée ;
- petite fluctuation, par exemple chaleureux → émerveillement : attendre que le nouvel état reste pertinent au moins deux beats de scène ;
- retour très bref à un ton précédent : éviter de redémarrer une piste inutilement.

L'implémentation de référence est dans `reference/scene_system.py`.

## Transition

Quand le lecteur le permet, préférer un fondu court à un arrêt brutal. Le volume doit rester secondaire par rapport à la lecture et ne jamais rendre les dialogues difficiles à suivre.

Le MJ ne doit jamais annoncer techniquement le changement de musique dans le récit. `music_state` est une donnée d'ambiance hors narration.

## Persistance

Une future entité `scene_ambience` ou un champ de scène peut contenir :

```json
{
  "music_state": "mystery",
  "intensity": 2,
  "reason": "un inconnu révèle une information inquiétante",
  "started_at": "temps en jeu ou identifiant de scène"
}
```

Le PLAYER peut connaître l'ambiance sélectionnée sans que cela révèle une vérité GM. En revanche, la raison textuelle ne doit jamais contenir de secret non découvert.

## Lecture réelle

Deux chemins restent possibles :

1. intégration compatible ChatGPT lorsqu'un lecteur musical adapté est disponible dans le chat ;
2. lecteur natif du Companion recevant seulement le `music_state` et gérant lui-même boucle, piste, volume et transition.

Le contrat reste volontairement indépendant du fournisseur audio afin que la campagne ne dépende pas d'un service unique.

## Critères MVP

La fonctionnalité est considérée suffisamment mûre pour une démonstration lorsque :

- les transitions ne surviennent pas à chaque tour ;
- combat, tension, foyer et découverte produisent des ambiances clairement distinctes ;
- le changement d'état ne modifie jamais le canon ;
- l'absence de lecteur disponible ne bloque jamais la partie ;
- le système peut être désactivé sans effet secondaire.
