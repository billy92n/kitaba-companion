"""Reference model for Kitaba's future readable campaign-book layer.

Editorial captures are derived from canon but never become canon merely because
they are written well. This module is a PROPOSAL for MVP/post-MVP validation.
"""

from __future__ import annotations

from dataclasses import dataclass


ALLOWED_SCENE_KINDS = {
    "exploration",
    "dialogue",
    "conflict",
    "combat",
    "travel",
    "rest",
    "revelation",
    "emotional",
}


@dataclass(frozen=True)
class EditorialScene:
    scene_id: str
    title: str
    kind: str
    canon_revision_start: int
    canon_revision_end: int
    prose: str
    source_event_ids: tuple[str, ...]
    participant_entity_ids: tuple[str, ...] = ()
    location_entity_id: str | None = None
    illustration_asset_ids: tuple[str, ...] = ()


def validate_editorial_scene(scene: EditorialScene) -> None:
    if not scene.scene_id.strip():
        raise ValueError("scene_id is required")
    if not scene.title.strip():
        raise ValueError("title is required")
    if scene.kind not in ALLOWED_SCENE_KINDS:
        raise ValueError(f"unknown scene kind: {scene.kind}")
    if scene.canon_revision_start < 0:
        raise ValueError("canon_revision_start must be non-negative")
    if scene.canon_revision_end < scene.canon_revision_start:
        raise ValueError("canon revision range is invalid")
    if not scene.prose.strip():
        raise ValueError("editorial prose is required")
    if not scene.source_event_ids:
        raise ValueError("at least one canonical source event is required")


def should_close_scene(
    *,
    location_changed: bool = False,
    major_goal_resolved: bool = False,
    major_time_jump: bool = False,
    major_tonal_transition: bool = False,
    explicit_scene_end: bool = False,
) -> bool:
    """Close a scene only on a meaningful structural transition."""

    return any((location_changed, major_goal_resolved, major_time_jump, major_tonal_transition, explicit_scene_end))


def can_merge_scenes(left: EditorialScene, right: EditorialScene) -> bool:
    """Allow editorial merging only when chronology and context remain continuous."""

    validate_editorial_scene(left)
    validate_editorial_scene(right)
    if left.canon_revision_end > right.canon_revision_start:
        return False
    if left.location_entity_id != right.location_entity_id:
        return False
    if left.kind == "combat" or right.kind == "combat":
        return False
    return right.canon_revision_start - left.canon_revision_end <= 1
