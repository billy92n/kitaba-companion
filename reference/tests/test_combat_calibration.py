from math import ceil

import pytest

from reference.combat_resources import apply_harm, mana_cost, spend_mana
from reference.game_system import resolve_roll


def expected_harm_per_attempt(target: int, *, base_harm: int, protection: int = 0, resilience: int = 0) -> float:
    total = 0
    for roll in range(1, 101):
        result = resolve_roll(target, roll)
        if result.outcome == "failure":
            continue
        total += apply_harm(
            hp_current=100,
            hp_max=100,
            base_harm=base_harm,
            protection=protection,
            resilience=resilience,
            outcome=result.outcome,
        ).damage
    return total / 100


def test_representative_weapon_harm_has_useful_separation():
    weak = apply_harm(hp_current=100, hp_max=100, base_harm=12)
    standard = apply_harm(hp_current=100, hp_max=100, base_harm=25)
    heavy = apply_harm(hp_current=100, hp_max=100, base_harm=35)
    devastating = apply_harm(hp_current=100, hp_max=100, base_harm=50)

    assert (weak.damage, weak.injury_severity) == (12, "serious")
    assert (standard.damage, standard.injury_severity) == (25, "critical")
    assert (heavy.damage, heavy.injury_severity) == (35, "critical")
    assert (devastating.damage, devastating.injury_severity) == (50, "catastrophic")
    assert [ceil(100 / x.damage) for x in (weak, standard, heavy, devastating)] == [9, 4, 3, 2]


def test_fixed_protection_makes_armor_meaningful_without_level_scaling():
    assert apply_harm(hp_current=100, hp_max=100, base_harm=12, protection=8).damage == 4
    assert apply_harm(hp_current=100, hp_max=100, base_harm=25, protection=4).damage == 21
    assert apply_harm(hp_current=100, hp_max=100, base_harm=25, protection=8).damage == 17
    assert apply_harm(hp_current=100, hp_max=100, base_harm=25, protection=12).damage == 13
    assert apply_harm(hp_current=100, hp_max=100, base_harm=8, protection=8).damage == 0


def test_exceptional_hit_can_cross_an_injury_band_even_against_armor():
    normal = apply_harm(hp_current=100, hp_max=100, base_harm=25, protection=8, outcome="success")
    exceptional = apply_harm(hp_current=100, hp_max=100, base_harm=25, protection=8, outcome="exceptional_success")
    assert normal.damage == 17
    assert normal.injury_severity == "serious"
    assert exceptional.damage == 30
    assert exceptional.injury_severity == "critical"


def test_resolution_skill_changes_expected_harm_without_changing_enemy_hp():
    weaker = expected_harm_per_attempt(35, base_harm=25, protection=4)
    even = expected_harm_per_attempt(55, base_harm=25, protection=4)
    stronger = expected_harm_per_attempt(75, base_harm=25, protection=4)
    assert weaker == pytest.approx(9.54)
    assert even == pytest.approx(14.0)
    assert stronger == pytest.approx(18.46)
    assert weaker < even < stronger


def test_zero_hp_is_incapacitation_not_automatic_arbitrary_death():
    safe_source = apply_harm(hp_current=10, hp_max=100, base_harm=12, lethal_source=False)
    lethal_source = apply_harm(hp_current=10, hp_max=100, base_harm=12, lethal_source=True)
    assert safe_source.incapacitated is True
    assert safe_source.death_risk is False
    assert lethal_source.incapacitated is True
    assert lethal_source.death_risk is True


def test_mana_cost_bands_scale_with_capacity_but_do_not_reward_spam():
    assert [mana_cost(100, band) for band in ("trivial", "light", "moderate", "heavy", "major", "extreme")] == [1, 3, 7, 12, 20, 35]
    assert [mana_cost(40, band) for band in ("light", "moderate", "heavy", "major")] == [1, 3, 5, 8]


def test_overchannel_deficit_escalates_predictably():
    assert spend_mana(mana_current=10, mana_max=100, cost=15, allow_overchannel=True).overchannel_severity == "strain"
    assert spend_mana(mana_current=10, mana_max=100, cost=25, allow_overchannel=True).overchannel_severity == "injury_risk"
    assert spend_mana(mana_current=10, mana_max=100, cost=40, allow_overchannel=True).overchannel_severity == "severe_injury_risk"
    assert spend_mana(mana_current=10, mana_max=100, cost=60, allow_overchannel=True).overchannel_severity == "coma_risk"
    assert spend_mana(mana_current=10, mana_max=100, cost=70, allow_overchannel=True).overchannel_severity == "death_risk"
