from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def write(path, text):
    (ROOT / path).write_text(text, encoding="utf-8")


# --- App: interactive map + stronger visual continuity guidance ---
path = "src/App.tsx"
text = read(path)
text = text.replace(
    'import { AdventurerCardView, MagicView, SkillsView, TimelineView } from "./components/ProgressionViews";\n',
    'import { AdventurerCardView, MagicView, SkillsView, TimelineView } from "./components/ProgressionViews";\nimport { InteractiveMap } from "./components/InteractiveMap";\n',
)
text = text.replace(
    '  map: ["place", "map_marker", "map", "current_location"],',
    '  map: ["place", "map_marker", "map", "current_location", "settlement", "state", "region", "route", "dungeon"],',
)

start = text.index("  function renderMap() {")
end = text.index("\n  function navigateTo", start)
new_map = '''  function renderMap() {
    const mapEntities = entities.filter((e) => ["map_marker", "place", "current_location", "settlement", "state", "region", "route", "dungeon"].includes(e.entity_type));
    return <section className="panel"><div className="map-header"><div><h2>Carte du monde</h2><p className="muted">Carte vivante de la campagne : zoom, déplacement et lieux cliquables. Chaque KITABA_UPDATE peut révéler de nouveaux repères sans afficher les lieux encore inconnus du personnage.</p></div><button className="ghost small" onClick={() => importVisual("world_map")}>Remplacer la carte</button></div><InteractiveMap imageUrl={worldMapUrl ?? "/kitaba-world-map.png"} entities={mapEntities} /><div className="map-known"><h3>Lieux connus</h3><EntityList entities={mapEntities} empty="Aucun lieu connu n'est encore positionné sur la carte." /></div></section>;
  }
'''
text = text[:start] + new_map + text[end:]

media_start = text.index("  function renderMedia() {")
media_end = text.index("\n  function renderGmVault", media_start)
new_media = '''  function renderMedia() {
    return <div className="media-stack"><section className="panel visual-continuity"><div className="eyebrow">Continuité visuelle</div><h2>Références de campagne</h2><p>Les portraits et illustrations canoniques servent de références visuelles. Le MJ doit conserver les traits stables d'un personnage et créer des variantes cohérentes lorsque son état change : blessure, maladie, fatigue, nouvelle tenue, entrée héroïque ou autre moment marquant.</p><div className="visual-rule-grid"><span><b>1.</b> Identité visuelle textuelle fixée</span><span><b>2.</b> Image de référence importée</span><span><b>3.</b> Variantes = même personnage, nouvel état</span><span><b>4.</b> Scènes de groupe = références déjà établies</span></div></section><section className="panel"><h2>Médiathèque de campagne</h2><p className="muted">Portraits et illustrations conservés localement et inclus dans les sauvegardes. Une image ne crée jamais seule un fait canonique : le texte et l'état du personnage restent prioritaires.</p><div className="action-row"><button className="secondary" onClick={() => importVisual("npc_portrait")}>Ajouter un portrait PNJ</button><button className="secondary" onClick={() => importVisual("other_image")}>Ajouter une illustration</button><button className="ghost" onClick={() => importVisual("player_portrait")}>Portrait du personnage</button><button className="ghost" onClick={() => importVisual("world_map")}>Carte du monde</button></div>{assets.length === 0 ? <div className="empty-inline">Aucun visuel importé.</div> : <div className="audit-list">{assets.map((asset) => <div className="audit-row" key={asset.id}><div><strong>{asset.kind.replaceAll("_", " ")}</strong><span>{new Date(asset.created_at).toLocaleString("fr-FR")}</span></div><button className="ghost small" onClick={() => previewMediaAsset(asset)}>{mediaPreviewAssetId === asset.id ? "Actualiser" : "Voir"}</button></div>)}</div>}{mediaPreviewUrl && <div className="media-preview"><img src={mediaPreviewUrl} alt="Prévisualisation du visuel sélectionné" /></div>}</section></div>;
  }
'''
text = text[:media_start] + new_media + text[media_end:]

text = text.replace(
    '<section className="panel asset-panel"><h2>Visuels de campagne</h2><p className="muted">Les visuels importés sont copiés dans le stockage local de Kitaba et inclus dans les sauvegardes <code>.kitaba</code>.</p>',
    '<section className="panel asset-panel"><h2>Visuels de campagne</h2><p className="muted">Les visuels importés sont copiés dans le stockage local de Kitaba et inclus dans les sauvegardes <code>.kitaba</code>. Pour les personnages importants, conserve une image de référence et ajoute ensuite des variantes cohérentes plutôt que de réinventer leur apparence.</p>',
)
write(path, text)

# --- Sidebar: map unlocks for any positioned geographic canon ---
path = "src/components/Sidebar.tsx"
text = read(path)
text = text.replace(
    '  map: ["place", "map_marker", "map", "current_location"],',
    '  map: ["place", "map_marker", "map", "current_location", "settlement", "state", "region", "route", "dungeon"],',
)
write(path, text)

# --- Interactive map and visual continuity styles ---
path = "src/styles.css"
text = read(path)
append = r'''

/* 0.1.5 — interactive campaign map */
.interactive-map-shell { display: grid; gap: .8rem; }
.interactive-map-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
.interactive-map-toolbar > div:first-child { display: grid; gap: .15rem; }
.interactive-map-toolbar span { color: var(--muted); font-size: .82rem; }
.interactive-map-viewport { position: relative; overflow: hidden; width: 100%; aspect-ratio: 2 / 1; min-height: 320px; background: #0c0f10; border: 1px solid var(--border); border-radius: .8rem; cursor: grab; touch-action: none; user-select: none; }
.interactive-map-viewport:active { cursor: grabbing; }
.interactive-map-viewport:fullscreen { width: 100vw; height: 100vh; aspect-ratio: auto; border: 0; border-radius: 0; background: #050606; }
.interactive-map-stage { position: absolute; inset: 0; transform-origin: center center; transition: transform 120ms ease-out; }
.interactive-map-viewport:active .interactive-map-stage { transition: none; }
.interactive-map-stage > img { width: 100%; height: 100%; object-fit: contain; display: block; pointer-events: none; }
.interactive-map-marker { position: absolute; transform: translate(-50%, -50%) scale(calc(1 / var(--map-marker-scale, 1))); display: grid; justify-items: center; gap: .22rem; padding: 0; border: 0; background: transparent; color: #f2ead8; cursor: pointer; z-index: 3; min-width: 1.4rem; }
.interactive-map-marker .marker-dot { width: .72rem; height: .72rem; border-radius: 50%; background: #e2c36b; box-shadow: 0 0 0 .18rem rgba(13,15,15,.72), 0 0 .55rem rgba(226,195,107,.7); }
.interactive-map-marker.current .marker-dot { width: .9rem; height: .9rem; background: #f2f2e9; box-shadow: 0 0 0 .22rem rgba(138,45,36,.95), 0 0 .8rem rgba(242,242,233,.8); }
.interactive-map-marker b { max-width: 10rem; padding: .12rem .35rem; border-radius: .3rem; background: rgba(8,10,10,.82); font-size: .72rem; line-height: 1.15; text-align: center; white-space: nowrap; box-shadow: 0 1px 8px rgba(0,0,0,.35); }
.interactive-map-marker.selected b, .interactive-map-marker:hover b { background: rgba(55,44,27,.95); }
.interactive-map-details { display: grid; grid-template-columns: minmax(0, 1fr) minmax(14rem, .65fr) auto; gap: 1rem; align-items: start; padding: 1rem; border: 1px solid var(--border); border-radius: .7rem; background: rgba(255,255,255,.025); }
.interactive-map-details h3 { margin: .15rem 0 .4rem; font-size: 1.25rem; }
.interactive-map-details p { margin: 0; color: var(--muted); }
.interactive-map-details dl { display: grid; gap: .45rem; margin: 0; }
.interactive-map-details dl div { display: grid; grid-template-columns: 7rem 1fr; gap: .5rem; }
.interactive-map-details dt { color: var(--muted); }
.interactive-map-details dd { margin: 0; }
.interactive-map-hint { margin: 0; color: var(--muted); font-size: .82rem; }
.map-known { margin-top: .3rem; }
.map-known h3 { margin-bottom: .7rem; }
.media-stack { display: grid; gap: 1rem; }
.visual-continuity > p { max-width: 75ch; }
.visual-rule-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .6rem; margin-top: .9rem; }
.visual-rule-grid span { padding: .7rem .8rem; border: 1px solid var(--border); border-radius: .55rem; background: rgba(255,255,255,.025); }
.visual-rule-grid b { margin-right: .3rem; color: var(--accent); }
.media-preview { margin-top: 1rem; text-align: center; }
.media-preview img { max-width: 100%; max-height: 70vh; object-fit: contain; border-radius: .6rem; }
@media (max-width: 760px) {
  .interactive-map-viewport { min-height: 240px; }
  .interactive-map-details { grid-template-columns: 1fr; }
  .visual-rule-grid { grid-template-columns: 1fr; }
}
'''
if "0.1.5 — interactive campaign map" not in text:
    text += append
write(path, text)

# --- Version bump without database/schema migration: existing saves remain compatible ---
for path in ["package.json", "src-tauri/tauri.conf.json", "src-tauri/Cargo.toml"]:
    text = read(path)
    text = text.replace('"version": "0.1.4"', '"version": "0.1.5"')
    text = re.sub(r'(?m)^version = "0\.1\.4"$', 'version = "0.1.5"', text)
    write(path, text)

# package-lock root/package version only
path = "package-lock.json"
data = json.loads(read(path))
data["version"] = "0.1.5"
if "" in data.get("packages", {}):
    data["packages"][""]["version"] = "0.1.5"
write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")

# Build artifact name
path = ".github/workflows/build-windows.yml"
text = read(path).replace("kitaba-companion-windows-0.1.4", "kitaba-companion-windows-0.1.5")
write(path, text)

# Changelog
path = "CHANGELOG.md"
text = read(path)
entry = '''# Changelog\n\n## 0.1.5 — Immersion & interaction\n\n- carte du monde réellement interactive : zoom molette, déplacement par glisser, plein écran, marqueurs cliquables et fiche de lieu ;\n- révélation cartographique pilotée par les entités PLAYER des KITABA_UPDATE (`place`, `map_marker`, `current_location`, `settlement`, `state`, `region`, `route`, `dungeon`) ;\n- médiathèque clarifiée autour de la continuité visuelle : image de référence, variantes d'état et scènes multi-personnages ;\n- aucun changement de schéma SQLite : les campagnes 0.1.4 restent directement compatibles et aucune réinitialisation n'est requise ;\n- préparation du contrat MJ 0.1.5 : narration plus courte et interactive, coordonnées cartographiques persistées, identité visuelle persistante et musique adaptative de scène.\n\n'''
if not text.startswith("# Changelog"):
    raise SystemExit("Unexpected CHANGELOG header")
text = entry + text[len("# Changelog\n\n"):]
write(path, text)

print("immersive patch applied")
