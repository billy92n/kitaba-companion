# Kitaba — MVP de présentation studio

Status: working presentation target for the 0.1.6 development branch.

## Proposition de valeur

**Kitaba — l’art de façonner votre propre histoire.**

Le MVP doit démontrer qu’une campagne solo assistée par IA peut rester cohérente au-delà d’une conversation, grâce à un Companion qui conserve le canon, sépare les secrets, structure la mémoire du monde et rend cette continuité visible au joueur.

Pour une présentation studio, le message central n’est pas « voici une application D&D ». Le prototype doit montrer une **couche de continuité RPG adaptable** à d’autres univers, moteurs narratifs, règles et interfaces.

## Ce qui doit être réellement montrable

### 1. Continuité de campagne
- création d’une campagne vierge sans personnage préfabriqué ;
- import atomique des `KITABA_UPDATE` ;
- séparation PLAYER / GM ;
- révisions et timeline persistantes ;
- sauvegarde/restauration `.kitaba` avec contrôle d’intégrité ;
- reprise d’une campagne existante après mise à jour de l’application ;
- continuité indépendante de la durée de vie d’un chat particulier.

### 2. Jeu interactif et liberté guidée
- réponses MJ courtes et jouables plutôt que murs de texte ;
- enrichissement léger des actions brèves du joueur sans lui voler ses décisions ;
- réactions des PNJ et résultats du monde restent sous contrôle de l’autorité narrative ;
- action incertaine = résolution réelle en privé, avec possibilité d’échec, réussite partielle ou réussite ;
- lorsqu’une nouvelle décision est attendue, trois pistes contextuelles peuvent orienter le joueur sans fermer l’espace d’action ;
- une quatrième voie libre reste toujours disponible pour écrire, modifier, combiner ou ignorer les suggestions ;
- une suggestion affichée n’est jamais un choix canonique tant que le joueur ne l’a pas réellement adoptée.

Le principe à vendre n’est pas « choix multiples ». C’est **liberté totale avec réduction de l’effet page blanche**.

### 3. Personnage, nature et progression
- fiche personnage, caractéristiques, blessures, ressources et relations visibles quand elles sont connues ;
- possibilité d’un ancrage initial de caractère très léger, ou de laisser explicitement ce champ OPEN ;
- nature du protagoniste qui émerge surtout de choix répétés, décisions coûteuses, habitudes et contradictions ;
- distinction entre nature réelle, image de soi et réputation publique ;
- aucun trait observé ne peut décider une action volontaire à la place du joueur ;
- compétences présentées qualitativement ;
- progression cachée non linéaire en cours de calibration ;
- rang officiel E→S clairement séparé de la puissance/maîtrise réelle ;
- mécanique de progression toujours identifiée comme **PROPOSAL** tant qu’elle n’est pas promue dans le MASTER.

### 4. Carte vivante
- carte du monde zoomable et déplaçable sans jamais sortir des limites physiques de l’image ;
- coordonnées normalisées stables ;
- lieux révélés/repositionnés par les updates ;
- marqueur de position actuelle ;
- recherche de lieux ;
- couches filtrables ;
- densité gérée par niveaux de détail et regroupement automatique des marqueurs ;
- clic sur un groupe = zoom pour séparer les lieux ;
- seuls les lieux connus du joueur apparaissent côté PLAYER ;
- localisation exacte, rumeur et zone approximative restent visuellement distinctes ;
- distances de voyage explicites, jamais déduites silencieusement de pixels/coordonnées normalisées.

### 5. Continuité visuelle
- portrait du protagoniste et médiathèque de campagne ;
- références principales persistantes pour personnages/lieux connus ;
- variantes liées à l’état courant (blessé, malade, fatigué, etc.) ;
- références de scène multi-personnages ;
- références visibles directement dans les vues normales, pas seulement dans un outil technique séparé ;
- cadrage centré sans étirement dans les emplacements fixes ;
- règle « canon avant image » : un visuel ne crée jamais seul une apparence non établie.

### 6. Encyclopédie / Codex du joueur
- vue-livre dédiée qui rassemble uniquement les connaissances PLAYER réellement acquises ;
- catégories : Colonies & lieux, Figures & relations, Relations & lignées, Bestiaire & troupes, Royaumes & factions, Concepts & savoirs, Monde & histoire, Autres découvertes ;
- recherche interne et enrichissement progressif des fiches existantes ;
- une rumeur reste identifiée comme rumeur et une croyance comme croyance ;
- aucun secret GM n’est interrogé ou rendu pour construire le Codex ;
- les PNJ nommés/durablement pertinents sont mémorisés sans remplir le livre de passants anonymes ;
- les forces/faiblesses de monstres, informations politiques, liens familiaux, etc. n’apparaissent que lorsqu’ils sont réellement connus ;
- le Codex réutilise les entités canoniques existantes au lieu de créer une seconde base de vérité ;
- aucune nouvelle migration SQLite n’est nécessaire.

### 7. Mémoire et histoire
- journal des événements significatifs plutôt qu’une copie brute du chat ;
- chronologie connue ;
- monde, relations, missions et connaissances durables consultables ;
- architecture compatible avec un futur export de campagne sous forme de récit illustré.

### 8. Adaptabilité studio
La démonstration doit permettre d’expliquer clairement :
- que ChatGPT est l’autorité narrative du prototype actuel, pas une dépendance conceptuelle obligatoire ;
- que le studio peut substituer son propre orchestrateur IA, moteur de règles ou runtime ;
- que SQLite/Tauri/React sont les implémentations actuelles, pas des contraintes commerciales obligatoires ;
- que les invariants à conserver sont surtout identité, révision, timeline, visibilité, mutation atomique, contexte, sauvegarde et provenance ;
- que le guidage 3+1 est une couche de présentation portable, pas une limitation du moteur d’actions ;
- que l’Encyclopédie est une projection du savoir canonique PLAYER et peut donc être reskinnée en codex, journal, bestiaire, wiki ou interface diégétique ;
- que la couche peut être reskinnée ou intégrée à un client de jeu sans perdre le modèle de continuité.

## Ce qui peut rester hors du MVP sans bloquer la démonstration

- lecteur musical natif complet ;
- économie mondiale totalement chiffrée ;
- crafting complet ;
- simulation détaillée du voyage ;
- export final PDF/EPUB du « livre » ;
- arbre généalogique/graphique relationnel interactif complet (la catégorie Relations & lignées et les identités persistantes préparent cette extension) ;
- application mobile native ;
- SDK Unity/Unreal prêt à livrer ;
- cloud/multijoueur de production ;
- abstraction multi-fournisseur IA déjà implémentée en code ;
- interface 3+1 native cliquable dans le Companion 0.1.6 (le contrat existe côté jeu, l’intégration UI est post-MVP/API).

Ces éléments sont des extensions après preuve du cœur produit.

## Critères de sortie MVP

Un build peut être qualifié **MVP présentable** seulement si :

1. tous les tests Python/TypeScript/Rust passent ;
2. l’installateur Windows est construit et vérifié ;
3. une sauvegarde 0.1.5 réelle peut être ouverte/restaurée sur une **copie** sans migration destructive ;
4. le diagnostic d’intégrité reste vert après mise à niveau ;
5. la carte ne révèle jamais de fond noir en déplacement/zoom/fullscreen ;
6. une carte chargée de nombreux marqueurs reste navigable grâce aux couches, au niveau de détail, aux clusters et à la recherche ;
7. aucun secret GM n’apparaît côté PLAYER ;
8. les références visuelles importantes survivent au cycle liaison → sauvegarde → restauration ;
9. les visuels fixes ne sont ni étirés ni déformés ;
10. l’Encyclopédie n’affiche que les entités PLAYER, distingue les connaissances incertaines et se met à jour à partir du même canon sans migration dédiée ;
11. les modèles de progression/résolution/combat restent explicitement PROPOSAL tant qu’ils ne sont pas promus dans le MASTER ;
12. une démonstration de 10–15 minutes peut montrer : campagne → personnage → relation/visuel → encyclopédie → carte → journal → update → changement du monde → intégrité/sauvegarde ;
13. le présentateur peut expliquer en moins d’une minute quelles parties sont spécifiques au prototype et quelles parties constituent le concept adaptable.

## Démonstration cible 10–15 minutes

Scénario recommandé : partir d’une campagne déjà vécue. Montrer le personnage et un proche important, une référence visuelle persistante et le journal. Ouvrir ensuite brièvement l’Encyclopédie pour montrer qu’un PNJ, une colonie et une connaissance du monde existent comme mémoire lisible, puis rappeler qu’une rumeur reste signalée comme telle. Montrer brièvement que le joueur n’est pas enfermé dans un menu : trois pistes peuvent l’orienter, mais une action libre reste toujours possible. Ouvrir la carte, recentrer la position actuelle, rechercher un lieu et afficher les couches. Appliquer ensuite un update préparé qui révèle ou repositionne un lieu, constater son apparition dans les surfaces normales et dans le Codex si pertinent, puis afficher révision/timeline et diagnostic d’intégrité. Une sauvegarde/restauration sur copie peut être montrée si le timing le permet.

La démonstration doit vendre la sensation : **« le modèle peut changer, le chat peut se terminer, l’application peut redémarrer — le monde sait toujours ce qui est vrai. »**

Le MVP doit éviter de se présenter comme une accumulation de menus techniques ou comme un simple wrapper ChatGPT. `docs/STUDIO_ADAPTATION_GUIDE.md` détaille la frontière d’intégration à expliquer à un partenaire.