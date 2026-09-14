from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_interactive_map_is_zoomable_pannable_and_clickable():
    component = _read("src/components/InteractiveMap.tsx")
    app = _read("src/App.tsx")
    assert 'addEventListener("wheel", onWheel, { passive: false })' in component
    assert "event.preventDefault()" in component
    assert "event.stopPropagation()" in component
    assert "onPointerMove" in component
    assert "requestFullscreen" in component
    assert "setSelectedId" in component
    assert "InteractiveMap" in app
    assert '\"settlement\", \"state\", \"region\", \"route\", \"dungeon\"' in app


def test_map_remains_player_knowledge_gated():
    app = _read("src/App.tsx")
    sidebar = _read("src/components/Sidebar.tsx")
    assert "const mapEntities = entities.filter" in app
    assert "<InteractiveMap imageUrl={worldMapUrl" in app
    assert "entities={mapEntities}" in app
    assert 'map: ["place", "map_marker", "map", "current_location", "settlement", "state", "region", "route", "dungeon"]' in sidebar


def test_interactive_map_clamps_pan_and_prevents_black_borders():
    component = _read("src/components/InteractiveMap.tsx")
    assert "function clampPan" in component
    assert "geometry.viewportWidth - renderedWidth" in component
    assert "geometry.viewportHeight - renderedHeight" in component
    assert "fitPan" in component
    assert "fitScale" in component
    assert "ResizeObserver" in component
    assert "applyView(nextScale, panRef.current, next)" in component
    assert "marker.x * geometry.naturalWidth * scale" in component
    assert "marker.y * geometry.naturalHeight * scale" in component


def test_dense_atlas_has_layers_search_clustering_current_position_and_overlap_picker():
    component = _read("src/components/InteractiveMap.tsx")
    css = _read("src/interactive-map-mvp.css")
    assert "clusterMarkers" in component
    assert "map-layer-chip" in component
    assert "Rechercher un lieu…" in component
    assert "Ma position" in component
    assert "visibleAtScale" in component
    assert "map_importance" in component
    assert "interactive-map-cluster" in component
    assert "spiderClusterId" in component
    assert "SPIDER_RADIUS_PX" in component
    assert "interactive-map-spider-marker" in component
    assert "Lieux à cet endroit" in component
    assert "map-cluster-choice-list" in component
    assert "maxScale: 1" in component
    assert "map-search-results" in css
    assert "interactive-map-cluster" in css
    assert "interactive-map-spider-marker" in css
    assert "map-cluster-choice-list" in css


def test_map_raster_uses_dpr_canvas_and_native_resolution_ceiling():
    component = _read("src/components/InteractiveMap.tsx")
    css = _read("src/interactive-map-mvp.css")
    assert "canvasRef" in component
    assert "window.devicePixelRatio" in component
    assert "canvas.width = Math.round(g.viewportWidth * dpr)" in component
    assert "ctx.drawImage(image" in component
    assert "maxScale: 1" in component
    assert "100% natif" in component
    assert "interactive-map-raster-canvas" in component
    assert ".interactive-map-raster-canvas" in css
    assert "no automatic enlargement beyond native resolution" in css


def test_atlas_supports_routes_regions_and_approximate_positions_without_schema_change():
    component = _read("src/components/InteractiveMap.tsx")
    css = _read("src/interactive-map-mvp.css")
    assert "parseNormalizedPoints" in component
    assert 'entity.data.path ?? entity.data.points ?? entity.data.map_path' in component
    assert 'entity.data.polygon ?? entity.data.boundary ?? entity.data.map_polygon' in component
    assert 'feature.layer === "routes"' in component
    assert "ctx.lineTo" in component
    assert "ctx.ellipse" in component
    assert "location_precision" in component
    assert ".interactive-map-marker.approximate" in css


def test_visual_continuity_guidance_is_in_companion():
    app = _read("src/App.tsx")
    rpg = _read("src/components/RpgViews.tsx")
    assert "Continuité visuelle" in app
    assert "Variantes = même personnage, nouvel état" in app
    assert "Scènes de groupe = références déjà établies" in app
    assert "visualIdentitySummary" in rpg
    assert "Référence visuelle stable" in rpg
    assert "current_visual_state" in rpg


def test_exported_contract_carries_immersive_play_rules_in_both_engines():
    rust = _read("src-tauri/src/db.rs")
    py = _read("reference/engine.py")
    phrases = [
        "Prefer frequent playable beats over long passive narration",
        "When player input is brief or underspecified",
        "The player controls only the protagonist's attempted actions",
        "persist stable normalized map coordinates x/y in [0,1]",
        "Persist a stable textual visual_identity for important characters",
        "Treat adaptive music as scene-level ambience",
    ]
    for phrase in phrases:
        assert phrase in rust
        assert phrase in py
    map_types = '"map": ["place", "map_marker", "map", "current_location", "settlement", "state", "region", "route", "dungeon"]'
    assert map_types in rust
    assert map_types in py


def test_patch_does_not_change_database_schema():
    db = _read("src-tauri/src/db.rs")
    assert "CURRENT_SCHEMA_VERSION: i64 = 4" in db
    migrations = sorted((ROOT / "src-tauri" / "migrations").glob("*.sql"))
    assert [p.name for p in migrations] == [
        "0001_initial.sql",
        "0002_death_gate.sql",
        "0003_entity_protection.sql",
        "0004_sync_export_state.sql",
    ]


def test_companion_contract_requires_real_resolution_and_enriched_terse_actions():
    rust = _read("src-tauri/src/db.rs")
    ref = _read("reference/engine.py")
    for text in (rust, ref):
        assert "states a success or world outcome as an attempted action" in text
        assert "single hidden dice-like or equivalent random draw" in text
        assert "allow failure, partial success, complications or success" in text
        assert "do not reroll merely because the result is inconvenient" in text
        assert "When the player gives a terse action" in text
        assert "do not invent a materially different intention" in text


def test_release_version_is_016():
    assert '"version": "0.1.6"' in _read("package.json")
    assert '"version": "0.1.6"' in _read("src-tauri/tauri.conf.json")
    assert 'version = "0.1.6"' in _read("src-tauri/Cargo.toml")
    assert "kitaba-companion-windows-0.1.6" in _read(".github/workflows/build-windows.yml")
