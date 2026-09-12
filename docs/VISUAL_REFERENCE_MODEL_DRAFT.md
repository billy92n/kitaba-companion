# Kitaba — modèle de continuité visuelle (DRAFT)

Status: **PROPOSAL / implementation-in-progress**. Objectif : rendre les illustrations persistantes et réutilisables sans migration SQLite destructive et sans fuite de secrets.

## Principe

L'image n'est jamais l'unique vérité. L'identité visuelle canonique est d'abord décrite en texte ; une ou plusieurs images locales servent ensuite de références visuelles.

Le système doit permettre :
- un même personnage reconnaissable d'une image à l'autre ;
- plusieurs états du même personnage ;
- des scènes réunissant plusieurs personnages connus ;
- des lieux récurrents cohérents ;
- aucune fuite de secret GM par une image ou ses métadonnées.

## Identité textuelle canonique

Le MJ peut persister une `visual_identity` PLAYER une fois l'apparence suffisamment canonisée, soit dans l'entité concernée, soit via une entité/lien générique stable selon le contrat final. Les traits PLAYER ne contiennent jamais de caractéristique secrète.

Exemple conceptuel :

```json
{
  "subject_entity_id": "uuid-du-pnj-ou-lieu",
  "stable_traits": {
    "apparent_age": "environ 70 ans",
    "build": "fine et droite",
    "hair": "longs cheveux argentés tressés",
    "eyes": "verts",
    "distinctive_features": ["petite cicatrice sous l'œil gauche"]
  },
  "usual_clothing": "robe forestière vert sombre et châle crème",
  "art_direction": "campaign_default",
  "identity_status": "locked_reference"
}
```

Une caractéristique cachée nécessaire au MJ reste dans une donnée GM séparée et n'est jamais dérivée de l'image PLAYER.

## Liaison locale des fichiers — implémentation MVP actuelle

Les fichiers restent dans la table `assets` existante (`player_portrait`, `npc_portrait`, `other_image`, etc.). ChatGPT ne connaît pas l'ID local d'un fichier importé ; l'association est donc créée par le Companion.

Pour éviter une migration SQLite 0005, l'implémentation MVP stocke les associations dans un petit sidecar JSON géré par le backend et enregistré comme asset technique `visual_bindings_meta`. Il est :
- checksum-protected comme les autres assets ;
- inclus dans les sauvegardes `.kitaba` ;
- filtré des listes d'images ordinaires ;
- limité à des sujets PLAYER existants ;
- manipulé uniquement par les commandes Companion dédiées.

Schéma logique d'une association :

```json
{
  "asset_id": "uuid-local-companion",
  "subject_entity_id": "uuid-pnj-ou-lieu",
  "role": "primary_reference",
  "state": "normal",
  "caption": "Référence principale"
}
```

Cette métadonnée visuelle locale ne fait pas avancer la révision canonique et ne transforme pas une image en fait narratif.

## Variantes

Rôles supportés/ciblés :
- `primary_reference` : référence neutre principale ;
- `state_variant` : blessé, malade, épuisé, cérémonie, etc. ;
- `scene_reference` : scène de groupe ou moment important ;
- `place_reference` : décor récurrent ;
- `historical_reference` : état ancien du personnage/lieu.

États fréquents : `normal`, `wounded`, `severely_wounded`, `sick`, `exhausted`, `ceremonial`, `heroic`, `deceased`, ou une valeur contextuelle justifiée.

Une variante ne doit jamais réinventer les traits stables de l'identité principale.

## Scènes multi-personnages

Une illustration de groupe peut être liée comme `scene_reference` au journal/événement et réutiliser plusieurs références connues. Conceptuellement :

```json
{
  "scene_id": "uuid-event-or-journal",
  "subjects": [
    {"entity_id": "uuid-a", "reference_asset_id": "asset-a"},
    {"entity_id": "uuid-b", "reference_asset_id": "asset-b"}
  ],
  "location_reference_asset_id": "asset-place",
  "state": "conversation_at_home"
}
```

Le générateur d'image doit recevoir les références disponibles de chaque sujet. Si une identité n'est pas encore fixée, le MJ fixe d'abord sa description textuelle avant d'en faire une référence durable.

## Politique d'illustration MVP

Priorité forte :
1. protagoniste ;
2. proche central / tuteur / famille immédiatement présente ;
3. maison ou foyer ;
4. village/quartier de départ ;
5. PNJ durable ;
6. lieu majeur ;
7. scène émotionnelle ou spectaculaire réellement mémorable.

Le but est d'aider à visualiser, pas de déclencher une image à chaque tour.

## Direction artistique

La campagne conserve une bible visuelle cohérente : fantasy anime/isekaï lumineuse et expressive, avec possibilité de tons graves selon les scènes, sans copier le design exact d'une œuvre existante. Personnages, lieux, lumière, rendu, proportions et niveau de détail doivent rester cohérents entre générations.

## Sécurité et anti-spoiler

- une image PLAYER ne montre que ce que le personnage peut légitimement voir ou connaître ;
- ne jamais visualiser une aptitude cachée, une identité secrète ou une vérité GM simplement pour « faire joli » ;
- les variantes ne rétroagissent pas sur le canon textuel ;
- une image incohérente est corrigée/remplacée, jamais rationalisée comme twist ;
- le backend refuse d'associer une référence PLAYER à un sujet exclusivement GM.

## Ce qui est réellement implémenté dans le Companion MVP

- import et sauvegarde locale des images ;
- sidecar d'associations visuelles backup-safe sans migration de schéma ;
- création/modification/suppression d'associations vers des sujets PLAYER ;
- rôles/états/légendes ;
- interface de bibliothèque/références visuelles ;
- continuité textuelle visible dans les vues lorsque les données `visual_identity` existent.

## Gap encore ouvert : continuité ChatGPT

Le sidecar local permet au **Companion** de savoir quelle image appartient à qui. Il ne donne pas, à lui seul, les octets de l'image au chat ChatGPT. Le GM_FULL actuel transporte le canon textuel mais l'export des associations locales doit encore être formalisé si l'on veut qu'un nouveau chat sache qu'un asset local précis est la référence principale d'un personnage.

Avant de considérer la continuité visuelle « complète », il faut donc :
1. exposer dans le contexte exporté un manifeste PLAYER-safe des associations locales (IDs/rôles/états, jamais les secrets ni les octets) **ou** documenter explicitement une autre voie fiable ;
2. définir comment les images de référence réelles sont remises à disposition de la génération lorsqu'elles ne sont plus présentes dans la conversation ;
3. tester un changement de chat avec un PNJ possédant référence principale + variante et vérifier qu'aucune nouvelle génération ne réinvente son identité.

Tant que ce chemin n'est pas validé end-to-end, ne pas prétendre que ChatGPT « se souvient automatiquement » des pixels d'une image locale du Companion.
