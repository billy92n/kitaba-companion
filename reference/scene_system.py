"""Reference helpers for Kitaba scene pacing and adaptive ambience.

This module is a PROPOSAL used for regression tests. It does not control audio
playback by itself and is not campaign canon until promoted into the MASTER/MJ
contract.
"""

from __future__ import annotations

from dataclasses import dataclass


MUSIC_INTENSITY = {
    "silence": 0,
    "home_warmth": 1,
    "peaceful_exploration": 1,
    "wonder": 2,
    "mystery": 2,
    "tension": 3,
    "danger": 4,
    "combat": 5,
    "sorrow": 2,
    "triumph": 3,
}

PACING_PROFILES = {
    "exploration": {"paragraphs": (1, 3), "return_control": "after_hook"},
    "dialogue": {"paragraphs": (1, 2), "return_control": "after_meaningful_reply"},
    "tension": {"paragraphs": (1, 2), "return_control": "after_immediate_consequence"},
    "combat": {"paragraphs": (1, 2), "return_control": "after_immediate_consequence"},
    "emotional": {"paragraphs": (1, 4), "return_control": "after_emotional_beat"},
}


@dataclass(frozen=True)
class AmbienceDecision:
    state: str
    changed: bool
    reason: str


def pacing_profile(scene_type: str) -> dict[str, object]:
    if scene_type not in PACING_PROFILES:
        raise ValueError(f"unknown scene type: {scene_type}")
    return dict(PACING_PROFILES[scene_type])


def decide_music_state(
    current: str,
    proposed: str,
    *,
    scene_changed: bool = False,
    candidate_beats: int = 1,
    force: bool = False,
) -> AmbienceDecision:
    """Decide whether a proposed ambience should replace the current one.

    Small tonal fluctuations require two consecutive beats before switching.
    Real scene changes and large intensity jumps may transition immediately.
    """

    if current not in MUSIC_INTENSITY:
        raise ValueError(f"unknown current music state: {current}")
    if proposed not in MUSIC_INTENSITY:
        raise ValueError(f"unknown proposed music state: {proposed}")
    if candidate_beats < 1:
        raise ValueError("candidate_beats must be >= 1")
    if current == proposed:
        return AmbienceDecision(current, False, "same_state")
    if force:
        return AmbienceDecision(proposed, True, "forced")
    if scene_changed:
        return AmbienceDecision(proposed, True, "scene_change")

    intensity_jump = abs(MUSIC_INTENSITY[proposed] - MUSIC_INTENSITY[current])
    if intensity_jump >= 2:
        return AmbienceDecision(proposed, True, "large_tonal_shift")

    if candidate_beats >= 2:
        return AmbienceDecision(proposed, True, "stable_candidate")

    return AmbienceDecision(current, False, "avoid_churn")
