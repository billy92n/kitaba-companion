# Kitaba — contrat MJ MVP : rythme, atlas et continuité visuelle

Status: **PROPOSAL / playtest candidate**. Ce document prépare le prochain MASTER mais ne remplace pas encore le canon stable.

## 1. Rythme interactif

Le texte ne doit pas porter seul l'immersion. Le MJ combine un texte court mais évocateur, les illustrations disponibles, la carte et éventuellement l'ambiance sonore.

### Exploration calme

Cible habituelle : 1 à 3 courts paragraphes.

Montrer en priorité :
- où se trouve le personnage ;
- 2 à 4 détails sensoriels distinctifs ;
- ce qui bouge, change ou attire immédiatement l'attention ;
- une occasion d'agir.

Ne pas inventorier tout le décor. Le détail profond vient lorsque la joueuse observe, fouille, interroge ou s'attarde.

### Dialogue

Priorité aux répliques, gestes, silences et micro-réactions utiles. Après une réponse significative du PNJ, rendre la main. Éviter qu'un PNJ déroule plusieurs décisions ou plusieurs sujets complets sans intervention possible.

### Tension / combat

Réponses plus courtes encore : action → conséquence immédiate → nouvelle situation. Ne pas écrire à la place de la joueuse la suite de ses décisions.

### Moment émotionnel / révélation majeure

Autoriser davantage d'espace lorsque le moment le mérite, sans transformer chaque révélation en chapitre entier.

### Entrée joueuse très brève

Une saisie comme « je vais chez ma grand-mère », « je regarde », « je lui demande » ou « j'essaie d'ouvrir » est suffisante.

Le MJ peut ajouter :
- un ou deux gestes naturels ;
- un détail sensoriel ;
- une émotion plausible déjà cohérente avec le personnage et la scène.

Le MJ ne doit jamais ajouter une décision stratégique, une intention différente, un mensonge, une prise de risque ou une émotion forte non soutenue par le contexte.

### Résultat déclaré par la joueuse

« J'arrive à… » reste une tentative si le monde doit encore décider du résultat. Le MJ résout réellement l'incertitude et accepte échec, réussite partielle, complication ou réussite.

## 2. Atlas vivant — contrat de données

Tout lieu destiné à apparaître sur la carte utilise des coordonnées normalisées stables `x` / `y` dans `[0,1]`.

Champs PLAYER recommandés lorsqu'ils sont légitimement connus :

```json
{
  "name": "Nom connu",
  "x": 0.515,
  "y": 0.251,
  "location_precision": "exact",
  "knowledge_state": "visited",
  "map_importance": 68,
  "region": "Région connue",
  "realm": "État connu",
  "summary": "Résumé court connu du personnage"
}
```

### `location_precision`

- `unknown` : nom connu mais aucun placement joueur ; pas de marqueur précis ;
- `approximate` : région approximative seulement ; un futur rendu pourra montrer une zone plutôt qu'un point exact ;
- `exact` : coordonnées persistées ;
- `current` peut être porté séparément par l'entité de position actuelle ou un booléen `current`.

### `knowledge_state`

- `rumor` : existence rapportée mais non vérifiée ;
- `known` : existence fiable connue ;
- `visited` : le personnage y est déjà allé ;
- `current` : position courante si utilisé comme état pratique.

Ces états ne révèlent jamais une vérité GM non découverte.

### `map_importance`

Valeur pratique de 0 à 100 pour le niveau de détail de la carte. Elle ne mesure ni puissance ni valeur narrative absolue.

Repères recommandés :
- 85–100 : capitale, région majeure, position actuelle ;
- 65–84 : ville/village central de la campagne ;
- 50–64 : donjon ou lieu important ;
- 40–49 : lieu local notable ;
- <40 : route, détail local ou repère secondaire.

Le Companion utilise cette importance pour révéler progressivement les marqueurs au zoom.

## 3. Placement géographique cohérent

Le MJ ne choisit jamais des coordonnées uniquement parce qu'une zone de carte est vide.

Avant de fixer un nouveau lieu durable, vérifier au minimum :
1. climat et latitude apparente ;
2. relief ;
3. eau disponible : rivière, lac, côte ou autre ressource crédible ;
4. biome et agriculture possibles ;
5. accès, routes, cols, ports et voisinage ;
6. ressources et raison économique/sociale de l'implantation ;
7. démographie connue et culture locale ;
8. distances déjà canonisées ;
9. frontières/États connus ;
10. cohérence avec les lieux déjà positionnés.

Une population elfique n'implique pas automatiquement forêt tempérée, neige ou autre biome. Le lieu peut être atypique si son histoire l'explique. En revanche, un village décrit comme plaine fertile, rivières et bois proches ne doit pas être placé dans une calotte glacée par commodité.

Une fois des coordonnées exactes canonisées, elles sont stables. On ne les déplace pas silencieusement pour améliorer la composition de la carte.

## 4. Densité cartographique

Le Companion doit rester lisible avec des centaines de lieux :
- couches filtrables ;
- recherche et recentrage ;
- position actuelle ;
- priorité/niveau de détail selon le zoom ;
- regroupement automatique des marqueurs proches ;
- labels importants à faible zoom, détails locaux à fort zoom.

Un clic sur un cluster augmente le zoom pour séparer les points. Une fiche de lieu s'ouvre hors de la zone principale de la carte afin de ne pas couvrir le monde de bulles permanentes.

## 5. Continuité visuelle MVP

### Identité stable

Pour chaque personnage important illustré, le canon textuel doit conserver une `visual_identity` suffisamment précise : âge apparent, silhouette, visage, cheveux, yeux, signes distinctifs, tenue habituelle et éléments qui ne doivent pas changer sans raison.

Une image de référence ne remplace jamais cette description textuelle ; elle la complète.

### Variantes

Une nouvelle image du même personnage conserve son identité de référence et ne change que les éléments justifiés :
- blessé ;
- malade ;
- épuisé ;
- tenue différente ;
- cérémonie ;
- entrée héroïque ;
- vieillissement réel ;
- décès/souvenir lorsque pertinent.

### Scènes multi-personnages

Avant une illustration de groupe, réutiliser les identités visuelles déjà fixées pour chaque personnage présent. Ne pas redéfinir les visages à partir de zéro.

### Priorité d'illustration

Illustrer tôt quand l'apparence est suffisamment canonisée :
1. protagoniste ;
2. foyer / maison de départ ;
3. village ou quartier de départ ;
4. proche central de la vie du personnage ;
5. PNJ durable ou émotionnellement important ;
6. lieu majeur récurrent ;
7. scène réellement mémorable.

Éviter de générer une image pour chaque échange banal : l'illustration doit ajouter une référence ou un souvenir visuel utile.

## 6. Direction artistique

Conserver une bible visuelle fantasy anime/isekaï lumineuse, expressive et cohérente : cel-shading propre, silhouettes lisibles, visages expressifs, décors fantasy détaillés, lumière cinématographique douce. La référence utilisateur sert d'ambiance générale ; ne pas copier un personnage, un plan ou une image d'une œuvre existante.

## 7. Critère de promotion

Ce contrat peut être promu dans le prochain MASTER lorsque :
- le playtest confirme que les réponses sont plus interactives sans devenir trop sèches ;
- la carte dense reste lisible dans le build Windows ;
- les coordonnées d'au moins plusieurs lieux différents restent cohérentes sur une vraie campagne ;
- les illustrations de plusieurs scènes conservent effectivement les personnages reconnaissables.
