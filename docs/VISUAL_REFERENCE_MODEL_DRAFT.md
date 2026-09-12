# Kitaba — modèle de continuité visuelle (DRAFT)

Status: **PROPOSAL**. Objectif : rendre les illustrations persistantes et réutilisables sans imposer immédiatement une migration SQLite.

## Principe

L'image n'est pas l'unique vérité. L'identité visuelle canonique est d'abord décrite en texte, puis une ou plusieurs images locales servent de références.

Le modèle doit permettre :
- un même personnage reconnaissable d'une image à l'autre ;
- plusieurs états du même personnage ;
- des scènes réunissant plusieurs personnages connus ;
- des lieux récurrents cohérents ;
- aucune fuite de secret GM par une image ou son metadata.

## Entité `visual_identity`

Créée par un `KITABA_UPDATE` une fois l'apparence suffisamment canonisée.

Exemple PLAYER :

```json
{
  "subject_entity_id": "uuid-du-pnj-ou-lieu",
  "subject_type": "npc",
  "stable_traits": {
    "apparent_age": "environ 70 ans",
    "build": "fine et droite",
    "hair": "longs cheveux argentés tressés",
    "eyes": "verts",
    "face": "pommettes hautes, rides fines",
    "distinctive_features": ["petite cicatrice sous l'œil gauche"]
  },
  "usual_clothing": "robe forestière vert sombre et châle crème",
  "art_direction": "campaign_default",
  "identity_status": "locked_reference"
}
```

Aucun trait secret ne doit être placé dans la version PLAYER. Une caractéristique cachée peut exister dans une entité GM séparée si nécessaire.

## Liaison au sujet

Utiliser un lien PLAYER :

`visual_identity --visual_identity_of--> npc/place/player_character`

Le lien permet au MJ de retrouver l'identité même si le nom public du personnage change.

## Images locales

Les fichiers restent dans la table `assets` existante.

Pour éviter une migration de base pendant le MVP, l'association future peut être portée par une petite entité PLAYER `visual_asset_binding` :

```json
{
  "visual_identity_id": "uuid",
  "asset_id": "uuid-local-companion",
  "role": "primary_reference",
  "state": "normal",
  "caption": "Référence principale"
}
```

Cette entité doit être créée par le Companion lors d'une future action « Associer à… », car ChatGPT ne connaît pas l'ID local d'un fichier importé.

## Variantes

Rôles proposés :
- `primary_reference` : référence neutre principale ;
- `state_variant` : blessé, malade, épuisé, cérémonie, etc. ;
- `scene_reference` : scène de groupe ou moment important ;
- `place_reference` : décor récurrent ;
- `historical_reference` : état ancien du personnage/lieu.

Un `state_variant` doit conserver l'identité de référence. L'état peut être :
`normal`, `wounded`, `severely_wounded`, `sick`, `exhausted`, `ceremonial`, `heroic`, `deceased`, ou une valeur contextuelle justifiée.

## Scènes multi-personnages

Une illustration de groupe possède un ensemble de références :

```json
{
  "scene_id": "uuid-event-or-journal",
  "subjects": [
    {"entity_id": "uuid-a", "visual_identity_id": "uuid-va"},
    {"entity_id": "uuid-b", "visual_identity_id": "uuid-vb"}
  ],
  "location_visual_identity_id": "uuid-place",
  "state": "conversation_at_home"
}
```

Le générateur d'image reçoit les références disponibles de chaque sujet. Si une identité n'est pas encore fixée, le MJ fixe d'abord sa description textuelle avant d'en faire une référence durable.

## Politique d'illustration MVP

Priorité forte :
1. protagoniste ;
2. proche central / tuteur / famille immédiatement présente ;
3. maison ou foyer ;
4. village/quartier de départ ;
5. PNJ durable ;
6. lieu majeur ;
7. scène émotionnelle ou spectaculaire réellement mémorable.

Ne pas générer mécaniquement une illustration à chaque tour.

## Sécurité et anti-spoiler

- une image PLAYER ne montre que ce que le personnage peut légitimement voir ou connaître ;
- ne jamais visualiser un mécanisme caché, une véritable identité secrète ou une caractéristique GM simplement pour « faire joli » ;
- les variantes futures ne rétroagissent pas sur le canon textuel ;
- une image incohérente doit être corrigée/remplacée, pas rationalisée comme twist.

## Chemin d'implémentation sans migration destructive

1. MJ persiste `visual_identity` dans les entités génériques existantes ;
2. Companion importe les images comme aujourd'hui ;
3. ajouter une action Companion « Associer à une identité visuelle » qui crée `visual_asset_binding` avec un asset local ;
4. Relations/Médiathèque/Lieux affichent la référence principale et les variantes ;
5. le contexte ChatGPT exporte la description visuelle textuelle et les rôles de références, mais pas les octets des images ;
6. pour une nouvelle génération, le chat réutilise les images de référence disponibles dans la conversation quand elles sont fournies/attachées.

Aucune colonne SQLite supplémentaire n'est nécessaire pour ce premier modèle : les tables génériques `entity_documents`, `entity_links` et `assets` suffisent.
