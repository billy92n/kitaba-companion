import pytest

from reference.story_system import EditorialScene, can_merge_scenes, should_close_scene, validate_editorial_scene


def scene(**overrides):
    base = dict(
        scene_id="scene-1",
        title="Un matin à Lethrane",
        kind="dialogue",
        canon_revision_start=3,
        canon_revision_end=4,
        prose="Un court passage éditorial dérivé des faits canoniques.",
        source_event_ids=("event-1",),
        participant_entity_ids=("pc", "grandmother"),
        location_entity_id="home",
        illustration_asset_ids=(),
    )
    base.update(overrides)
    return EditorialScene(**base)


def test_editorial_scene_requires_traceable_canonical_sources():
    validate_editorial_scene(scene())
    with pytest.raises(ValueError):
        validate_editorial_scene(scene(source_event_ids=()))


def test_editorial_scene_revision_range_must_be_monotonic():
    with pytest.raises(ValueError):
        validate_editorial_scene(scene(canon_revision_start=5, canon_revision_end=4))


def test_scene_closes_only_on_meaningful_structural_transition():
    assert should_close_scene() is False
    assert should_close_scene(location_changed=True) is True
    assert should_close_scene(major_goal_resolved=True) is True
    assert should_close_scene(major_time_jump=True) is True
    assert should_close_scene(major_tonal_transition=True) is True


def test_adjacent_quiet_scenes_can_be_merged_editorially_without_rewriting_canon():
    left = scene(scene_id="a", canon_revision_start=3, canon_revision_end=4)
    right = scene(scene_id="b", canon_revision_start=5, canon_revision_end=5)
    assert can_merge_scenes(left, right) is True


def test_combat_and_location_change_create_hard_editorial_boundaries():
    left = scene(scene_id="a", canon_revision_start=3, canon_revision_end=4)
    moved = scene(scene_id="b", canon_revision_start=5, canon_revision_end=5, location_entity_id="forest")
    combat = scene(scene_id="c", kind="combat", canon_revision_start=5, canon_revision_end=6)
    assert can_merge_scenes(left, moved) is False
    assert can_merge_scenes(left, combat) is False
