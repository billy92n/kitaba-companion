from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_encyclopedia_is_player_only_projection_without_schema_change():
    dock = read("src/components/EncyclopediaDock.tsx")
    view = read("src/components/EncyclopediaView.tsx")
    db = read("src-tauri/src/db.rs")

    assert "backend.listEntities(campaign.id, false)" in dock
    assert "includeGm" not in dock
    assert "GM" not in view
    assert "CURRENT_SCHEMA_VERSION: i64 = 4" in db


def test_encyclopedia_has_requested_discovery_categories_and_epistemic_labels():
    view = read("src/components/EncyclopediaView.tsx")
    for label in [
        "Lieux & localités",
        "Figures & relations",
        "Relations & lignées",
        "Bestiaire & troupes",
        "Royaumes & factions",
        "Concepts & savoirs",
        "Monde & histoire",
        "Autres découvertes",
    ]:
        assert label in view
    assert 'entity.entity_type === "rumor"' in view
    assert 'entity.entity_type === "belief"' in view
    assert "epistemic_status" in view
    assert "known_strengths" not in view  # generic data rendering preserves fields without inventing special truth


def test_encyclopedia_is_normal_memory_navigation_not_floating_obstruction():
    main = read("src/main.tsx")
    sidebar = read("src/components/Sidebar.tsx")
    dock = read("src/components/EncyclopediaDock.tsx")
    css = read("src/encyclopedia.css")

    assert 'import { EncyclopediaDock } from "./components/EncyclopediaDock"' in main
    assert 'import "./encyclopedia.css"' in main
    assert 'className="encyclopedia-nav-slot"' in sidebar
    assert 'document.querySelector<HTMLElement>(".encyclopedia-nav-slot")' in dock
    assert "encyclopedia-nav-item" in dock
    assert "position:fixed" not in css.replace(" ", "")
    assert "body.encyclopedia-open" in css


def test_encyclopedia_uses_existing_entities_and_supports_explicit_category_override():
    view = read("src/components/EncyclopediaView.tsx")
    assert "encyclopedia_category" in view
    assert "encyclopedia_include" in view
    assert "entity.entity_version" not in view  # player book should not foreground technical version numbers
    assert "VisualReferenceGallery" in view
