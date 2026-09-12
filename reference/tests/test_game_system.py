import pytest

from reference.game_system import (
    learning_award,
    mastery_tier,
    resolve_roll,
    success_target,
)


def test_mastery_thresholds_are_nonlinear_and_stable():
    assert mastery_tier(0) == "Novice"
    assert mastery_tier(39) == "Novice"
    assert mastery_tier(40) == "Apprenti"
    assert mastery_tier(119) == "Apprenti"
    assert mastery_tier(120) == "Compétent"
    assert mastery_tier(299) == "Compétent"
    assert mastery_tier(300) == "Confirmé"
    assert mastery_tier(649) == "Confirmé"
    assert mastery_tier(650) == "Expert"
    assert mastery_tier(1199) == "Expert"
    assert mastery_tier(1200) == "Maître"


def test_progression_rewards_meaningful_learning_not_farming():
    assert learning_award("trivial", "success") == 0
    assert learning_award("demanding", "success") == 4
    assert learning_award("hard", "instructive_failure") == 6
    assert learning_award("hard", "success", feedback="teacher") == 9
    assert learning_award("hard", "success", repetition_index=1) == 4
    assert learning_award("hard", "success", repetition_index=2) == 2
    assert learning_award("hard", "success", repetition_index=3) == 0
    assert learning_award("hard", "success", repetition_index=20) == 0


def test_resolution_baseline_is_playable_but_not_automatic():
    assert success_target("untrained", "routine") == 55
    assert success_target("competent", "standard") == 55
    assert success_target("competent", "hard") == 40
    assert success_target("expert", "hard") == 60
    assert success_target("maitre", "extreme") == 40
    assert success_target("maitre", "nearly_impossible") == 25


def test_resolution_is_clamped_but_context_still_matters():
    assert success_target("maitre", "routine", characteristic_modifier=10, context_modifier=30) == 95
    assert success_target("untrained", "nearly_impossible", characteristic_modifier=-10, context_modifier=-30) == 5
    assert success_target("competent", "standard", characteristic_modifier=10, context_modifier=20) == 85


def test_outcome_bands_include_partial_success_without_reroll_logic():
    target = 55
    assert resolve_roll(target, 5).outcome == "exceptional_success"
    assert resolve_roll(target, 6).outcome == "success"
    assert resolve_roll(target, 55).outcome == "success"
    assert resolve_roll(target, 56).outcome == "partial_success"
    assert resolve_roll(target, 70).outcome == "partial_success"
    assert resolve_roll(target, 71).outcome == "failure"


def test_roll_100_only_flags_existing_hazard_instead_of_inventing_catastrophe():
    safe = resolve_roll(50, 100, hazardous=False)
    dangerous = resolve_roll(50, 100, hazardous=True)
    assert safe.outcome == dangerous.outcome == "failure"
    assert safe.hazard_escalation_possible is False
    assert dangerous.hazard_escalation_possible is True


def test_invalid_reference_inputs_are_rejected():
    with pytest.raises(ValueError):
        mastery_tier(-1)
    with pytest.raises(ValueError):
        success_target("unknown", "standard")
    with pytest.raises(ValueError):
        success_target("novice", "unknown")
    with pytest.raises(ValueError):
        success_target("novice", "standard", context_modifier=31)
    with pytest.raises(ValueError):
        resolve_roll(50, 0)
