# Kitaba — MVP de présentation

Status: working presentation target for the post-0.1.5 development branch.

## Proposition de valeur

**Kitaba — l’art de façonner votre propre histoire.**

Le MVP doit démontrer qu’une campagne solo peut rester cohérente entre ChatGPT et un Companion local, tout en offrant une expérience de récit interactif, illustré et géographiquement vivant.

## Ce qui doit être réellement montrable

### 1. Continuité de campagne
- création d’une campagne vierge sans personnage préfabriqué ;
- import atomique des `KITABA_UPDATE` ;
- séparation PLAYER / GM ;
- révisions et timeline persistantes ;
- sauvegarde/restauration `.kitaba` avec contrôle d’intégrité ;
- reprise d’une campagne existante après mise à jour de l’application.

### 2. Jeu interactif
- réponses MJ courtes et jouables plutôt que murs de texte ;
- enrichissement léger des actions brèves de la joueuse sans lui voler ses décisions ;
- réactions des PNJ et résultats du monde restent sous contrôle du MJ ;
- action incertaine = résolution réelle en privé, avec possibilité d’échec, réussite partielle ou réussite.

### 3. Personnage et progression
- fiche personnage, caractéristiques, blessures, ressources et relations visibles quand elles sont connues ;
- compétences présentées qualitativement ;
- progression cachée non linéaire en cours de calibration ;
- rang officiel E→S clairement séparé de la puissance/maîtrise réelle.

### 4. Carte vivante
- carte du monde zoomable et déplaçable sans jamais sortir des limites physiques de l’image ;
- coordonnées normalisées stables ;
- lieux révélés par les updates ;
- marqueur de position actuelle ;
- recherche de lieux ;
- couches filtrables ;
- densité gérée par niveaux de détail et regroupement automatique des marqueurs ;
- clic sur un groupe = zoom pour séparer les lieux ;
- seuls les lieux connus du joueur apparaissent côté PLAYER.

### 5. Continuité visuelle
- portrait du protagoniste et médiathèque de campagne ;
- contrat de bible visuelle commune ;
- identité visuelle textuelle persistante prévue pour les personnages/lieux importants ;
- variantes et scènes multi-personnages prévues dans le prochain sous-lot, sans prétendre qu’elles sont déjà totalement automatisées.

### 6. Mémoire et histoire
- journal des événements significatifs plutôt qu’une copie brute du chat ;
- chronologie connue ;
- monde, relations, missions et connaissances durables consultables ;
- architecture compatible avec un futur export de campagne sous forme de récit illustré.

## Ce qui peut rester hors du MVP sans bloquer la démonstration

- lecteur musical natif complet ;
- génération automatique et liaison avancée de toutes les variantes d’illustrations ;
- économie mondiale totalement chiffrée ;
- crafting complet ;
- simulation détaillée du voyage ;
- export final PDF/EPUB du « livre » ;
- polygones politiques/biomes/routes complexes sur la carte ;
- application mobile native.

Ces éléments sont des extensions après preuve du cœur produit.

## Critères de sortie MVP

Un build peut être qualifié **MVP présentable** seulement si :

1. tous les tests Python/TypeScript/Rust passent ;
2. l’installateur Windows est construit et vérifié ;
3. une sauvegarde 0.1.5 réelle peut être ouverte sans migration destructive ;
4. le diagnostic d’intégrité reste vert après mise à niveau ;
5. la carte ne révèle jamais de fond noir en déplacement/zoom ;
6. une carte chargée de nombreux marqueurs reste navigable grâce aux couches, au niveau de détail, aux clusters et à la recherche ;
7. aucun secret GM n’apparaît côté PLAYER ;
8. le modèle de progression/résolution a des tests de calibration mais reste explicitement PROPOSAL tant qu’il n’est pas promu dans le MASTER ;
9. une démonstration de 10–15 minutes peut montrer : campagne → personnage → carte → relations/journal → update → nouveau lieu révélé → sauvegarde/intégrité.

## Démonstration cible

Scénario recommandé : partir d’une campagne déjà amorcée, ouvrir la fiche du personnage, montrer un proche important et le journal, ouvrir la carte et recentrer sur la position actuelle, rechercher un lieu, filtrer les couches, importer un update de démonstration qui révèle un nouveau lieu, constater son apparition sur la carte, puis afficher l’état de synchronisation et l’intégrité.

Le MVP doit vendre la sensation de **monde qui se souvient et se construit avec la partie**, pas une accumulation de menus techniques.
