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
    assert "<NpcPortraitControl subjectEntityId={e.id}" in rpg
    assert "currentState={visualState}" in rpg

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


def test_sidebar_portrait_shows_complete_source_without_crop_or_stretch():
    sidebar = source("src/components/Sidebar.tsx")
    css = source("src/image-fit-hardening.css")

    assert 'className="portrait-frame"' not in sidebar
    assert 'className="portrait-image"' in sidebar
    assert ".sidebar > .portrait-image" in css
    rule = css.split(".sidebar > .portrait-image", 1)[1].split("}", 1)[0]
    assert "width: 78px" in rule
    assert "height: auto" in rule
    assert "object-fit: contain" in rule
    assert "object-fit: cover" not in rule
    assert "transform: none" in rule


def test_relations_can_assign_a_primary_npc_portrait_directly():
    control = source("src/components/NpcPortraitControl.tsx")
    rpg = source("src/components/RpgViews.tsx")

    assert "NpcPortraitControl" in rpg
    assert 'importCampaignAsset(campaignId, "npc_portrait", path)' in control
    assert '"primary_reference"' in control
    assert "bindVisualAsset" in control
    assert 'hasPortrait ? "Changer" : "Ajouter un portrait"' in control
    assert "kitaba-visual-bindings-changed" in control
    assert 'className="npc-avatar-image"' in control


def test_relations_can_reuse_unbound_npc_portraits_imported_before_bindings_existed():
    control = source("src/components/NpcPortraitControl.tsx")

    assert "backend.listAssets(campaignId)" in control
    assert 'asset.kind === "npc_portrait"' in control
    assert "boundElsewhere" in control
    assert "readAssetDataUrl" in control
    assert "Choisis une image déjà importée" in control
    assert "chooseExisting(asset.id)" in control


def test_relation_avatar_prefers_matching_current_state_variant_then_primary_portrait():
    control = source("src/components/NpcPortraitControl.tsx")

    assert "function displayedPortrait" in control
    assert 'row.role === "state_variant"' in control
    assert "normalize(row.state) === normalizedState" in control
    assert 'row.role === "primary_reference"' in control
