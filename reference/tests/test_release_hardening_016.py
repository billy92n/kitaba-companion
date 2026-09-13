import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_image_slots_preserve_expected_aspect_behavior():
    main = _read("src/main.tsx")
    css = _read("src/image-fit-hardening.css")
    sidebar = _read("src/components/Sidebar.tsx")
    assert 'import "./image-fit-hardening.css"' in main
    # Sidebar portrait must show the complete source image, reduced without square stretching/cropping.
    assert 'className="portrait-frame"' not in sidebar
    assert ".sidebar > .portrait-image" in css
    sidebar_rule = css.split(".sidebar > .portrait-image", 1)[1].split("}", 1)[0]
    assert "width: 78px" in sidebar_rule
    assert "height: auto" in sidebar_rule
    assert "object-fit: contain" in sidebar_rule
    assert "object-fit: cover" not in sidebar_rule
    # Fixed reference cards may still crop consistently; large previews/maps keep their source ratio.
    assert ".visual-reference-card img" in css
    assert "object-position: 50% 50%" in css
    assert ".media-preview img" in css
    assert "object-fit: contain" in css
    assert ".interactive-map-stage > img" in css


def test_shared_mvp_theme_tokens_are_defined_before_feature_css_uses_them():
    main = _read("src/main.tsx")
    theme = _read("src/mvp-theme-hardening.css")
    assert 'import "./mvp-theme-hardening.css"' in main
    assert "--border:" in theme
    assert "--muted:" in theme
    assert "--accent:" in theme


def test_visual_dock_keeps_canon_before_image_gate():
    dock = _read("src/components/VisualReferenceDock.tsx")
    assert 'entity.entity_type === "player_character"' in dock
    assert 'kind !== "world_map" && !characterInitialized' in dock
    assert "une image ne doit jamais inventer une apparence indécidée" in dock
    assert "setEntities([])" in dock
    assert "setAssets([])" in dock


def test_visual_reference_launcher_only_lives_in_portraits_and_images_flow():
    dock = _read("src/components/VisualReferenceDock.tsx")
    css = _read("src/visual-reference-dock.css")
    assert 'createPortal' in dock
    assert 'document.querySelector<HTMLElement>(".media-stack .visual-continuity")' in dock
    assert "Ouvrir les portraits & images" in dock
    assert ".visual-reference-launcher{display:inline-flex" in css
    assert ".visual-reference-launcher{position:fixed" not in css


def test_inline_visuals_refresh_when_campaign_selection_changes():
    gallery = _read("src/components/VisualReferenceGallery.tsx")
    assert 'document.addEventListener("change", refreshOnCampaignChange)' in gallery
    assert 'target.classList.contains("campaign-select")' in gallery
    assert 'document.removeEventListener("change", refreshOnCampaignChange)' in gallery
    assert "bindingCache = null" in gallery


def test_map_drag_relies_on_clamping_even_at_cover_minimum_zoom():
    component = _read("src/components/InteractiveMap.tsx")
    assert 'if (!drag || drag.pointerId !== event.pointerId) return;' in component
    assert 'if (!drag || drag.pointerId !== event.pointerId || zoom <= minimumZoom) return;' not in component
    assert "clampPanToWorld(next, zoomRef.current, geometryRef.current)" in component


def test_016_keeps_015_persistence_schema_and_backup_contract():
    db = _read("src-tauri/src/db.rs")
    migrations = sorted((ROOT / "src-tauri" / "migrations").glob("*.sql"))

    # 0.1.6 deliberately keeps the production 0.1.5 persistence schema.
    # Visual-reference bindings are additive backup-managed assets/metadata, not a DB migration.
    assert "pub const CURRENT_SCHEMA_VERSION: i64 = 4;" in db
    assert [path.name for path in migrations] == [
        "0001_initial.sql",
        "0002_death_gate.sql",
        "0003_entity_protection.sql",
        "0004_sync_export_state.sql",
    ]
    assert 'include_str!("../migrations/0005_' not in db
    assert "pub fn create_technical_backup(" in db
    assert "pub fn restore_technical_backup(" in db
    assert "pub fn integrity_report(" in db


def test_all_release_metadata_identifies_016():
    package = json.loads(_read("package.json"))
    package_lock = json.loads(_read("package-lock.json"))
    tauri = json.loads(_read("src-tauri/tauri.conf.json"))
    cargo_toml = _read("src-tauri/Cargo.toml")
    cargo_lock = _read("src-tauri/Cargo.lock")
    workflow = _read(".github/workflows/build-windows.yml")

    assert package["version"] == "0.1.6"
    assert package_lock["version"] == "0.1.6"
    assert package_lock["packages"][""]["version"] == "0.1.6"
    assert tauri["version"] == "0.1.6"
    assert re.search(r'(?m)^version = "0\.1\.6"$', cargo_toml)
    assert re.search(r'\[\[package\]\]\s+name = "kitaba-companion"\s+version = "0\.1\.6"', cargo_lock)
    assert "kitaba-companion-windows-0.1.6" in workflow
