from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_normal_player_views_surface_persisted_visual_bindings():
    gallery = source("src/components/VisualReferenceGallery.tsx")
    rpg = source("src/components/RpgViews.tsx")
    entity_list = source("src/components/EntityList.tsx")

    assert "listVisualAssetBindings" in gallery
    assert "readAssetDataUrl" in gallery
    assert 'binding.role !== "state_variant"' in gallery
    assert "normalize(binding.state) === currentState" in gallery

    assert "subjectEntityId={pcEntity.id}" in rpg
    assert "subjectEntityId={e.id}" in rpg
    assert "currentState={currentVisualState(e.data)}" in rpg

    assert '"place"' in entity_list
    assert '"settlement"' in entity_list
    assert "<VisualReferenceGallery" in entity_list


def test_visual_gallery_refreshes_after_binding_edits():
    gallery = source("src/components/VisualReferenceGallery.tsx")
    library = source("src/components/VisualLibrary.tsx")

    event_name = "kitaba-visual-bindings-changed"
    assert event_name in gallery
    assert event_name in library
    assert "dispatchEvent" in library
    assert "addEventListener" in gallery
    assert "refreshToken" in gallery


def test_visual_gallery_does_not_load_entity_or_gm_data():
    gallery = source("src/components/VisualReferenceGallery.tsx")

    assert "listEntities" not in gallery
    assert "listVisualAssetBindings" in gallery


def test_sidebar_portrait_uses_aspect_safe_crop_instead_of_stretching():
    sidebar = source("src/components/Sidebar.tsx")
    css = source("src/image-fit-hardening.css")

    assert 'className="portrait-frame"' in sidebar
    assert 'className="portrait-image"' in sidebar
    assert ".portrait-frame > .portrait-image" in css
    assert "object-fit: cover" in css
    assert "object-position: 50% 50%" in css
    assert "width: 100%" in css
    assert "height: 100%" in css
    assert "aspect-ratio: 1 / 1" in css
    assert "transform: none" in css
