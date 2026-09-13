import pytest

from reference.world_systems import (
    encounter_check_count,
    estimate_travel,
    quote_price,
    relative_affordability,
    route_distance_km,
)


def test_price_baseline_preserves_relative_everyday_scale():
    meal = quote_price("simple_meal")
    bed = quote_price("common_bed")
    wage = quote_price("unskilled_day_wage")
    weapon = quote_price("simple_weapon")
    horse = quote_price("riding_horse")
    assert (meal.final_value, bed.final_value, wage.final_value, weapon.final_value, horse.final_value) == (15, 40, 100, 700, 8000)
    assert relative_affordability(weapon.final_value, wage.final_value) == 7
    assert relative_affordability(horse.final_value, wage.final_value) == 80


def test_region_and_scarcity_modify_prices_without_rewriting_baseline():
    normal = quote_price("day_rations")
    costly = quote_price("day_rations", regional_multiplier=1.4, scarcity_multiplier=1.5)
    cheap = quote_price("day_rations", regional_multiplier=.8, scarcity_multiplier=.8)
    assert normal.base_value == costly.base_value == cheap.base_value == 35
    assert costly.final_value == 74
    assert cheap.final_value == 22


def test_monster_and_dungeon_trade_uses_locked_guild_channel():
    assert quote_price("common_tool", origin="ordinary").legal_channel == "ordinary_market"
    assert quote_price("common_tool", origin="monster").legal_channel == "guild_network"
    assert quote_price("common_tool", origin="dungeon").legal_channel == "guild_network"


def test_route_distance_is_explicit_and_never_derived_from_map_coordinates():
    assert route_distance_km({"distance_km": 42.5, "x": .1, "y": .9}) == 42.5
    with pytest.raises(ValueError, match="explicit numeric distance_km"):
        route_distance_km({"x": .1, "y": .9, "path": [[.1, .9], [.8, .2]]})
    with pytest.raises(ValueError):
        route_distance_km({"distance_km": -1})


def test_travel_pace_is_terrain_weather_and_mode_sensitive():
    road = estimate_travel(100, mode="foot", terrain="road")
    open_land = estimate_travel(100, mode="foot", terrain="open")
    mountain = estimate_travel(100, mode="foot", terrain="mountain")
    mounted = estimate_travel(100, mode="mounted", terrain="open")
    assert road.km_per_day == pytest.approx(27.5)
    assert open_land.km_per_day == pytest.approx(25.0)
    assert mountain.km_per_day == pytest.approx(12.5)
    assert mounted.km_per_day == pytest.approx(40.0)
    assert road.days < open_land.days < mountain.days
    assert mounted.days < open_land.days


def test_forced_march_is_faster_but_has_real_fatigue_pressure():
    normal = estimate_travel(50, pace="normal")
    forced = estimate_travel(50, pace="forced")
    assert forced.days < normal.days
    assert forced.fatigue_pressure > normal.fatigue_pressure


def test_severe_conditions_stack_fatigue_and_reduce_distance():
    ordinary = estimate_travel(40, terrain="open", weather="normal")
    severe = estimate_travel(40, terrain="snow", weather="storm", pace="forced")
    assert severe.km_per_day < ordinary.km_per_day
    assert severe.fatigue_pressure >= 8


def test_encounter_checks_are_pressure_not_combat_spam():
    assert encounter_check_count(travel_days=10, danger="safe") == 0
    assert encounter_check_count(travel_days=1, danger="low") == 1
    assert encounter_check_count(travel_days=5, danger="moderate") == 1
    assert encounter_check_count(travel_days=5, danger="high") == 2
    assert encounter_check_count(travel_days=20, danger="extreme") == 3


def test_invalid_market_and_travel_inputs_fail_loudly():
    with pytest.raises(ValueError):
        quote_price("simple_meal", regional_multiplier=3)
    with pytest.raises(ValueError):
        estimate_travel(-1)
    with pytest.raises(ValueError):
        estimate_travel(10, terrain="teleport")
