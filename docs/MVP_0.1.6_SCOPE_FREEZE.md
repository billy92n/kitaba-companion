# Kitaba Companion 0.1.6 — périmètre de freeze MVP

Status: **release-scope decision for 0.1.6 candidate**. Cette décision ne promeut aucun système mécanique PROPOSAL dans le MASTER.

## Inclus dans le MVP 0.1.6

Le candidat 0.1.6 doit démontrer et préserver :

- ouverture et continuité d'une campagne existante ;
- séparation PLAYER / GM et absence de fuite des secrets ;
- import atomique des `KITABA_UPDATE` ;
- sauvegarde/restauration `.kitaba` et diagnostic d'intégrité ;
- carte vivante : limites strictes, zoom, déplacement, plein écran, recherche, couches, clusters, position actuelle, régions/routes connues ;
- distinction visuelle entre lieu exact, rumeur et localisation approximative, avec zone d'incertitude pour `location_precision=approximate` ;
- distances de voyage provenant d'un champ fictionnel explicite `distance_km`, jamais des coordonnées normalisées de la carte ;
- continuité visuelle persistante : référence principale, variante correspondant à l'état visuel courant et références de scène liées aux entités PLAYER ;
- affichage direct des références principales/variantes courantes dans les vues normales Personnage, Relations et lieux connus ;
- contrat MJ d'interaction courte déjà en playtest ;
- version Windows 0.1.6 et migration depuis une COPIE d'une vraie sauvegarde 0.1.5 avant tout merge.

## Fondations conservées mais non promises dans la démonstration 0.1.6

### Livre / export HTML

Le modèle `EditorialScene` et le renderer HTML sûr restent dans la branche comme fondations testées. En revanche, la persistance éditoriale et le bouton utilisateur `Exporter mon histoire` sont explicitement **post-MVP 0.1.6**.

Raison : les ajouter au dernier moment introduirait une nouvelle surface de persistance et de gestion d'assets qui n'est pas nécessaire pour prouver la proposition centrale « le monde se souvient et se construit avec ta partie ». Il est préférable de valider d'abord migration, intégrité, atlas et continuité visuelle.

PDF/EPUB restent postérieurs au pipeline HTML validé.

### Musique adaptative

Le modèle de `music_state` et l'anti-churn restent des prototypes de direction d'ambiance. Aucune automatisation ChatGPT → lecteur n'est promise dans le MVP 0.1.6 tant qu'une surface de contrôle réelle et fiable n'a pas été validée.

Le lecteur musical natif complet reste post-MVP ; le jeu doit fonctionner intégralement sans musique automatisée.

## Mécaniques PROPOSAL

Progression cachée, résolution d'incertitude, combat/blessures, mana/récupération et économie/voyage restent des candidats de calibration. Un test vert ne les rend pas canoniques. Leur promotion nécessite une décision explicite ultérieure et une mise à jour du MASTER.

## Freeze technique

Après ce document et les corrections directement liées aux fonctionnalités MVP ci-dessus, le développement 0.1.6 passe en mode release-hardening :

1. aucun ajout de feature non nécessaire ;
2. CI Windows complète sur le HEAD définitif ;
3. vérification artefact/installateur 0.1.6 ;
4. migration sur COPIE d'une vraie sauvegarde 0.1.5 ;
5. smoke tests humains carte/visuels/update/restauration ;
6. correction des régressions uniquement ;
7. nouveau build complet si le code change ;
8. merge dans `main` seulement lorsque tous les gates sont verts.

La campagne live 0.1.5 reste intacte pendant toute cette phase.
