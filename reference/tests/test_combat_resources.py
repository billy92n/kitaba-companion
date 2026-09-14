import pytest

from reference.combat_resources import (
    apply_harm,
    injury_severity_for_damage,
    mana_cost,
    overchannel_severity,
    recover_hp_after_safe_rest,
    recover_resource,
    spend_mana,
)


def test_injury_severity_scales_with_single_hit_fraction_not_character_level():
    assert injury_severity_for_damage(4, 100) == "negligible"
    assert injury_severity_for_damage(5, 100) == "minor"
    assert injury_severity_for_damage(12, 100) == "serious"
    assert injury_severity_for_damage(25, 100) == "critical"
    assert injury_severity_for_damage(40, 100) == "catastrophic"


def test_armor_and_resilience_reduce_harm_without_level_scaling():
    result = apply_harm(hp_current=100, hp_max=100, base_harm=22, protection=6, resilience=2)
    assert result.damage == 14
    assert result.hp_after == 86
    assert result.injury_severity == "serious"
    assert result.incapacitated is False


def test_partial_and_exceptional_attack_outcomes_change_harm_not_world_level():
    partial = apply_harm(hp_current=100, hp_max=100, base_harm=20, outcome="partial_success")
    normal = apply_harm(hp_current=100, hp_max=100, base_harm=20, outcome="success")
    exceptional = apply_harm(hp_current=100, hp_max=100, base_harm=20, outcome="exceptional_success")
    assert partial.damage == 13
    assert normal.damage == 20
    assert exceptional.damage == 30


def test_zero_hp_means_incapacitation_and_real_death_risk_when_source_is_lethal():
    nonlethal = apply_harm(hp_current=8, hp_max=100, base_harm=10, lethal_source=False)
    lethal = apply_harm(hp_current=8, hp_max=100, base_harm=10, lethal_source=True)
    assert nonlethal.hp_after == lethal.hp_after == 0
    assert nonlethal.incapacitated is True
    assert nonlethal.death_risk is False
    assert lethal.death_risk is True


def test_mana_cost_bands_scale_with_personal_reserve():
    assert mana_cost(100, "trivial") == 1
    assert mana_cost(100, "moderate") == 7
    assert mana_cost(100, "major") == 20
    assert mana_cost(200, "major") == 40


def test_normal_mana_spend_cannot_go_negative():
    result = spend_mana(mana_current=40, mana_max=100, cost=25)
    assert result.mana_after == 15
    assert result.deficit == 0
    assert result.overchannel_severity is None
    with pytest.raises(ValueError):
        spend_mana(mana_current=10, mana_max=100, cost=20)


def test_overchannel_deficit_escalates_from_strain_to_death_risk():
    assert overchannel_severity(0, 100) is None
    assert overchannel_severity(5, 100) == "strain"
    assert overchannel_severity(15, 100) == "injury_risk"
    assert overchannel_severity(30, 100) == "severe_injury_risk"
    assert overchannel_severity(50, 100) == "coma_risk"
    assert overchannel_severity(51, 100) == "death_risk"
    result = spend_mana(mana_current=10, mana_max=100, cost=45, allow_overchannel=True)
    assert result.mana_after == 0
    assert result.paid == 10
    assert result.deficit == 35
    assert result.overchannel_severity == "coma_risk"


def test_recovery_is_bounded_and_requires_fiction_to_choose_rate():
    assert recover_resource(20, 100, 0.25) == 45
    assert recover_resource(95, 100, 0.25) == 100
    with pytest.raises(ValueError):
        recover_resource(20, 100, 1.1)


def test_safe_rest_recovers_capacity_but_does_not_erase_persistent_injury():
    healthy = recover_hp_after_safe_rest(hp_current=20, hp_max=100, rest_quality="normal", injury_severity="none")
    serious = recover_hp_after_safe_rest(hp_current=20, hp_max=100, rest_quality="normal", injury_severity="serious")
    critical = recover_hp_after_safe_rest(hp_current=20, hp_max=100, rest_quality="normal", injury_severity="critical")

    assert healthy.hp_after == 35
    assert healthy.recovered == 15
    assert healthy.injury_persists is False
    assert serious.hp_after == 30
    assert serious.recovered == 10
    assert serious.injury_persists is True
    assert critical.hp_after == 25
    assert critical.recovered == 5
    assert critical.injury_persists is True


def test_better_rest_improves_recovery_without_instantly_curing_wounds():
    poor = recover_hp_after_safe_rest(hp_current=50, hp_max=100, rest_quality="poor", injury_severity="serious")
    medical = recover_hp_after_safe_rest(hp_current=50, hp_max=100, rest_quality="medical", injury_severity="serious")
    assert poor.recovered == 5
    assert medical.recovered == 23
    assert poor.injury_persists is medical.injury_persists is True


def test_recovery_inputs_are_validated():
    with pytest.raises(ValueError):
        recover_hp_after_safe_rest(hp_current=20, hp_max=100, rest_quality="magical_hotel", injury_severity="none")
    with pytest.raises(ValueError):
        recover_hp_after_safe_rest(hp_current=20, hp_max=100, rest_quality="normal", injury_severity="unknown")
