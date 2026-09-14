# Kitaba 0.1.6 — contrat de données de carte MVP

Status: **implementation contract / MVP candidate**. Ce document précise le format attendu par le Companion sans promouvoir de nouvelles mécaniques PROPOSAL dans le MASTER.

## Coordonnées d'affichage

`x` et `y` sont des coordonnées normalisées dans `[0,1]` sur la carte physique 2:1. Elles servent exclusivement au rendu, au recentrage et aux tracés de l'atlas.

Elles ne représentent jamais automatiquement une distance, une durée de voyage ou une échelle métrique.

## Position exacte

```json
{
  "name": "Lieu connu",
  "x": 0.515,
  "y": 0.251,
  "location_precision": "exact"
}
```

Une position exacte persistée reste stable sauf correction canonique explicite.

## Position approximative

Une connaissance approximative utilise un centre d'affichage et une zone d'incertitude, sans prétendre que ce centre est la position réelle exacte :

```json
{
  "name": "Ruines signalées",
  "x": 0.515,
  "y": 0.251,
  "location_precision": "approximate",
  "uncertainty_radius_x": 0.045,
  "uncertainty_radius_y": 0.030,
  "knowledge_state": "rumor"
}
```

Les rayons sont eux aussi normalisés par rapport à la carte et servent à la représentation visuelle de l'incertitude. Ils ne sont pas des kilomètres.

Si une entité `approximate` possède `x`/`y` mais aucun rayon, le Companion affiche une ellipse visuelle par défaut afin de ne pas transformer une information vague en point exact. Cette ellipse par défaut est une convention d'interface, pas une nouvelle précision canonique.

Champs acceptés par le rendu MVP :
- `uncertainty_radius_x` / `uncertainty_radius_y` pour une ellipse explicite ;
- `uncertainty_radius` pour un rayon partagé ;
- alias de compatibilité `map_uncertainty_x`, `map_uncertainty_y`, `map_uncertainty_radius`.

## Lieu connu mais non localisé

Un lieu dont la position n'est pas assez connue reste sans `x`/`y`. Le Companion peut le compter comme connu non localisé, mais ne doit pas fabriquer un marqueur.

## Routes et distances

Une route peut utiliser `path` (ou les alias de rendu existants) pour son tracé visuel normalisé. La distance fictionnelle utilisée par les systèmes de voyage doit être persistée séparément :

```json
{
  "name": "Route du col",
  "path": [[0.42, 0.31], [0.47, 0.29], [0.51, 0.25]],
  "distance_km": 68.0
}
```

Le moteur de calibration de voyage exige `distance_km` comme nombre fini positif ou nul. Il refuse une route sans distance explicite au lieu de calculer des kilomètres depuis `x`, `y`, `path`, la résolution de l'image ou la longueur en pixels.

Une route peut donc être visible avant que sa longueur soit canoniquement établie ; dans ce cas, elle reste non calibrée pour les calculs de voyage.

## Visibilité

Toutes les règles PLAYER/GM existantes restent prioritaires. Une coordonnée ou une zone d'incertitude MJ ne devient jamais visible côté joueur simplement parce qu'elle existe dans la base.
