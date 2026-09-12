from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_reference_and_rust_migrations_are_identical():
    pairs = [
        ("reference/schema.sql", "src-tauri/migrations/0001_initial.sql"),
        ("reference/migration_v2.sql", "src-tauri/migrations/0002_death_gate.sql"),
        ("reference/migration_v3.sql", "src-tauri/migrations/0003_entity_protection.sql"),
        ("reference/migration_v4.sql", "src-tauri/migrations/0004_sync_export_state.sql"),
    ]
    for reference_path, rust_path in pairs:
        assert _read(reference_path) == _read(rust_path), f"Migration drift: {reference_path} != {rust_path}"


def test_schema_version_constants_match():
    py = _read("reference/engine.py")
    rust = _read("src-tauri/src/db.rs")
    py_version = int(re.search(r"^SCHEMA_VERSION\s*=\s*(\d+)", py, re.M).group(1))
    rust_version = int(re.search(r"CURRENT_SCHEMA_VERSION:\s*i64\s*=\s*(\d+)", rust).group(1))
    assert py_version == rust_version


def test_protocol_version_is_consistent_across_schemas_reference_and_rust():
    update_schema = json.loads(_read("protocols/kitaba_update.schema.json"))
    context_schema = json.loads(_read("protocols/kitaba_context.schema.json"))
    assert update_schema["properties"]["protocol_version"]["const"] == 1
    assert context_schema["properties"]["protocol_version"]["const"] == 1

    py = _read("reference/engine.py")
    rust = _read("src-tauri/src/db.rs")
    assert 'update["protocol_version"] != 1' in py or "protocol_version" in py
    assert "update.protocol_version != 1" in rust


def test_frontend_backend_invokes_are_registered_tauri_commands():
    backend = _read("src/lib/backend.ts")
    lib_rs = _read("src-tauri/src/lib.rs")

    invoked = set(re.findall(r'invoke(?:<[^>]+>)?\("([a-z0-9_]+)"', backend))
    handler_match = re.search(r"tauri::generate_handler!\[(.*?)\]\)", lib_rs, re.S)
    assert handler_match, "Tauri generate_handler! list not found"
    registered = {item.strip() for item in handler_match.group(1).split(",") if item.strip()}

    missing = invoked - registered
    assert not missing, f"Frontend invokes unregistered Tauri commands: {sorted(missing)}"


def test_required_sync_commands_exist_in_frontend_backend():
    backend = _read("src/lib/backend.ts")
    required = {
        "preview_kitaba_update",
        "import_kitaba_update",
        "export_kitaba_context",
        "save_kitaba_context",
        "record_context_export",
        "rollback_death",
        "create_technical_backup",
        "restore_technical_backup",
    }
    invoked = set(re.findall(r'invoke(?:<[^>]+>)?\("([a-z0-9_]+)"', backend))
    assert required <= invoked


def test_public_world_map_exists_and_is_nonempty():
    path = ROOT / "public" / "kitaba-world-map.png"
    assert path.is_file()
    assert path.stat().st_size > 10_000


def test_tauri_bundle_is_configured_for_windows_nsis_and_has_icon():
    config = json.loads(_read("src-tauri/tauri.conf.json"))
    assert "nsis" in config["bundle"]["targets"]
    icon_paths = config["bundle"]["icon"]
    assert "icons/icon.ico" in icon_paths
    assert (ROOT / "src-tauri" / "icons" / "icon.ico").is_file()


def test_windows_workflow_runs_all_release_gates_before_bundle():
    workflow = _read(".github/workflows/build-windows.yml")
    expected_order = [
        "Run executable reference suite",
        "Run frontend type/build checks",
        "Run Rust tests/checks",
        "Build Tauri Windows installer",
        "Upload Windows bundles",
    ]
    positions = [workflow.index(name) for name in expected_order]
    assert positions == sorted(positions)


def test_mobile_navigation_uses_drawer_not_static_top_sidebar():
    app = _read("src/App.tsx")
    sidebar = _read("src/components/Sidebar.tsx")
    css = _read("src/styles.css")
    assert "mobileNavOpen" in app
    assert "mobile-menu-button" in app
    assert "mobile-backdrop" in app
    assert "mobileOpen" in sidebar
    assert ".sidebar.mobile-open" in css
    assert "transform: translateX(-105%)" in css


def test_sync_ui_masks_raw_update_payload_by_default():
    app = _read("src/App.tsx")
    assert "rawUpdateVisible" in app
    assert "Payload chargé — contenu brut masqué" in app
    assert "Collage manuel (avancé)" in app
    assert "Mode collage manuel" in app


def test_world_state_has_dedicated_player_ui_and_contract():
    app = _read("src/App.tsx")
    sidebar = _read("src/components/Sidebar.tsx")
    rust = _read("src-tauri/src/db.rs")
    py = _read("reference/engine.py")
    assert '["world", "Monde"]' in sidebar
    assert 'world: ["faction", "organization", "settlement"' in app
    assert '"world": ["faction", "organization", "settlement"' in rust
    assert '"world": ["faction", "organization", "settlement"' in py


def test_fresh_campaign_ui_is_generic_and_requires_character_creation_before_play():
    app = _read("src/App.tsx")
    sidebar = _read("src/components/Sidebar.tsx")
    assert "Nouvelle campagne Kitaba Solo" in app
    assert "Créer la campagne vierge" in app
    assert "Création du personnage avant la scène 1" in app
    assert "createSullyCampaign" not in app
    assert 'backend.createCampaign("Sully — Kitaba Solo")' not in app
    assert '"Personnage non créé"' in app
    assert '"Personnage à créer"' in sidebar
    assert 'const preCreationNav' in sidebar
    assert 'const discoveryTypes' in sidebar
    assert 'pcEntity ? nav.filter' in sidebar
    assert 'portraitInitial = firstName ? firstName.slice(0, 1).toUpperCase() : "?"' in sidebar


def test_player_knowledge_ui_hides_undiscovered_resource_and_lore_surfaces():
    sidebar = _read("src/components/Sidebar.tsx")
    rpg = _read("src/components/RpgViews.tsx")
    progression = _read("src/components/ProgressionViews.tsx")
    main = _read("src/main.tsx")
    hardening_css = _read("src/player-knowledge-hardening.css")
    assert '["overview", "Vue d\'ensemble"],\n  ["sync", "Synchronisation"]' in sidebar
    assert 'discoveryTypes' in sidebar
    assert 'awakening && <section' in rpg
    assert 'hasMana && <Resource label="Mana"' in rpg
    assert 'Aucune information magique connue ou enregistrée.' in progression
    assert 'import "./player-knowledge-hardening.css"' in main
    assert 'main:has(.onboarding-panel)' in hardening_css


def test_companion_contract_teaches_onboarding_and_player_knowledge_discipline():
    rust = _read("src-tauri/src/db.rs")
    py = _read("reference/engine.py")
    phrases = [
        "complete character creation and starting-world anchoring before the first narrated gameplay scene",
        "Never assume the human player knows developer or world terminology",
        "initial campaign update must persist the player_character",
        "appearance has been canonically fixed",
    ]
    for phrase in phrases:
        assert phrase in rust
        assert phrase in py


def test_frontend_has_no_sully_specific_runtime_copy():
    frontend_files = [
        path for path in (ROOT / "src").rglob("*")
        if path.is_file() and path.suffix in {".ts", ".tsx"}
    ]
    frontend_text = "\n".join(path.read_text(encoding="utf-8") for path in frontend_files)
    assert "Sully" not in frontend_text


def test_existing_campaign_can_create_an_independent_new_campaign():
    app = _read("src/App.tsx")
    assert "async function createAnotherCampaign()" in app
    assert ">Nouvelle campagne</button>" in app
    assert "Nouvelle campagne vierge créée" in app
