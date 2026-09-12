from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_interactive_map_is_zoomable_pannable_and_clickable():
    component = _read("src/components/InteractiveMap.tsx")
    app = _read("src/App.tsx")
    assert "onWheel" in component
    assert "onPointerMove" in component
    assert "requestFullscreen" in component
    assert "setSelectedId" in component
    assert "InteractiveMap" in app
    assert '"settlement", "state", "region", "route", "dungeon"' in app


def test_map_remains_player_knowledge_gated():
    component = _read("src/components/InteractiveMap.tsx")
    sidebar = _read("src/components/Sidebar.tsx")
    assert "La carte révèle uniquement les lieux présents dans le canon joueur" in component
    assert 'map: ["place", "map_marker", "map", "current_location", "settlement", "state", "region", "route", "dungeon"]' in sidebar


def test_visual_continuity_guidance_is_in_companion():
    app = _read("src/App.tsx")
    assert "Continuité visuelle" in app
    assert "Variantes = même personnage, nouvel état" in app
    assert "Scènes de groupe = références déjà établies" in app


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
        assert "perform the resolution privately" in text
        assert "allow failure, partial success, complications or success" in text
        assert "When the player gives a terse action" in text
        assert "do not invent a materially different intention" in text


def test_release_version_is_015():
    assert '"version": "0.1.5"' in _read("package.json")
    assert '"version": "0.1.5"' in _read("src-tauri/tauri.conf.json")
    assert 'version = "0.1.5"' in _read("src-tauri/Cargo.toml")
