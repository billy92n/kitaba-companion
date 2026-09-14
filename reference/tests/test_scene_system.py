import pytest

from reference.scene_system import decide_music_state, pacing_profile


def test_pacing_profiles_keep_player_interaction_frequent():
    assert pacing_profile("exploration")["paragraphs"] == (1, 3)
    assert pacing_profile("dialogue")["return_control"] == "after_meaningful_reply"
    assert pacing_profile("combat")["paragraphs"] == (1, 2)
    assert pacing_profile("emotional")["paragraphs"] == (1, 4)


def test_music_does_not_switch_on_every_small_tonal_fluctuation():
    result = decide_music_state("home_warmth", "wonder", candidate_beats=1)
    assert result.changed is False
    assert result.state == "home_warmth"
    assert result.reason == "avoid_churn"


def test_music_switches_after_small_change_is_stable_for_two_beats():
    result = decide_music_state("home_warmth", "wonder", candidate_beats=2)
    assert result.changed is True
    assert result.state == "wonder"
    assert result.reason == "stable_candidate"


def test_music_switches_immediately_for_real_scene_change():
    result = decide_music_state("mystery", "home_warmth", scene_changed=True)
    assert result.changed is True
    assert result.state == "home_warmth"
    assert result.reason == "scene_change"


def test_music_switches_immediately_for_large_tonal_jump():
    result = decide_music_state("peaceful_exploration", "combat")
    assert result.changed is True
    assert result.state == "combat"
    assert result.reason == "large_tonal_shift"


def test_same_state_never_restarts_track_needlessly():
    result = decide_music_state("tension", "tension", candidate_beats=99)
    assert result.changed is False
    assert result.reason == "same_state"


def test_invalid_scene_and_music_inputs_are_rejected():
    with pytest.raises(ValueError):
        pacing_profile("monologue")
    with pytest.raises(ValueError):
        decide_music_state("unknown", "combat")
    with pytest.raises(ValueError):
        decide_music_state("combat", "unknown")
    with pytest.raises(ValueError):
        decide_music_state("combat", "danger", candidate_beats=0)
