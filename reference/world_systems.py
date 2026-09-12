"""Candidate economy and travel helpers for Kitaba.

PROPOSAL only. Values are internal calibration units, not named world currency.
They exist to prevent arbitrary price/travel drift while geography and regional
currencies remain open in the stable world canon.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor


# Internal purchasing-value anchors. A region may later express these in its own
# canonical coins/notes/tokens. The values themselves are not player-facing lore.
BASE_VALUE_UNITS = {
    "simple_meal": 15,
    "day_rations": 35,
    "common_bed": 40,
    "safe_inn_room": 75,
    "unskilled_day_wage": 100,
    "skilled_day_wage": 220,
    "common_clothing": 300,
    "common_tool": 250,
    "simple_weapon": 700,
    "martial_weapon": 1200,
    "basic_armor": 2200,
    "riding_horse": 8000,
}

TRAVEL_BASE_KM_PER_DAY = {
    "foot": 25.0,
    "mounted": 40.0,
    "caravan": 24.0,
    "river_boat": 65.0,
    "sailing_ship": 120.0,
}

TERRAIN_MULTIPLIER = {
    "road": 1.10,
    "open": 1.00,
    "trail": 0.90,
    "forest": 0.75,
    "rough": 0.65,
    "snow": 0.55,
    "mountain": 0.50,
    "swamp": 0.45,
}

WEATHER_MULTIPLIER = {
    "favorable": 1.05,
    "normal": 1.00,
    "bad": 0.80,
    "storm": 0.55,
    "severe": 0.35,
}

PACE_MULTIPLIER = {
    "cautious": 0.80,
    "normal": 1.00,
    "forced": 1.25,
}

DANGER_PRESSURE = {
    "safe": 0,
    "low": 8,
    "moderate": 20,
    "high": 40,
    "severe": 65,
    "extreme": 85,
}


@dataclass(frozen=True)
class PriceQuote:
    base_value: int
    final_value: int
    regional_multiplier: float
    scarcity_multiplier: float
    legal_channel: str


@dataclass(frozen=True)
class TravelEstimate:
    distance_km: float
    km_per_day: float
    days: float
    whole_travel_days: int
    fatigue_pressure: int


def quote_price(
    category: str,
    *,
    regional_multiplier: float = 1.0,
    scarcity_multiplier: float = 1.0,
    origin: str = "ordinary",
) -> PriceQuote:
    if category not in BASE_VALUE_UNITS:
        raise ValueError(f"unknown price category: {category}")
    if not 0.5 <= regional_multiplier <= 2.0:
        raise ValueError("regional_multiplier must be within 0.5..2.0")
    if not 0.7 <= scarcity_multiplier <= 3.0:
        raise ValueError("scarcity_multiplier must be within 0.7..3.0")
    if origin not in {"ordinary", "dungeon", "monster"}:
        raise ValueError("origin must be ordinary, dungeon or monster")

    base = BASE_VALUE_UNITS[category]
    final = max(1, floor(base * regional_multiplier * scarcity_multiplier + 0.5))
    legal_channel = "guild_network" if origin in {"dungeon", "monster"} else "ordinary_market"
    return PriceQuote(base, final, regional_multiplier, scarcity_multiplier, legal_channel)


def relative_affordability(item_value: int, daily_income: int) -> float:
    if item_value < 0:
        raise ValueError("item_value must be non-negative")
    if daily_income <= 0:
        raise ValueError("daily_income must be positive")
    return item_value / daily_income


def estimate_travel(
    distance_km: float,
    *,
    mode: str = "foot",
    terrain: str = "open",
    weather: str = "normal",
    pace: str = "normal",
) -> TravelEstimate:
    if distance_km < 0:
        raise ValueError("distance_km must be non-negative")
    if mode not in TRAVEL_BASE_KM_PER_DAY:
        raise ValueError(f"unknown travel mode: {mode}")
    if terrain not in TERRAIN_MULTIPLIER:
        raise ValueError(f"unknown terrain: {terrain}")
    if weather not in WEATHER_MULTIPLIER:
        raise ValueError(f"unknown weather: {weather}")
    if pace not in PACE_MULTIPLIER:
        raise ValueError(f"unknown pace: {pace}")

    speed = TRAVEL_BASE_KM_PER_DAY[mode] * TERRAIN_MULTIPLIER[terrain] * WEATHER_MULTIPLIER[weather] * PACE_MULTIPLIER[pace]
    days = 0.0 if distance_km == 0 else distance_km / speed
    fatigue = {"cautious": 0, "normal": 1, "forced": 4}[pace]
    if weather in {"storm", "severe"}: fatigue += 2
    if terrain in {"mountain", "swamp", "snow"}: fatigue += 2
    return TravelEstimate(
        distance_km=distance_km,
        km_per_day=round(speed, 2),
        days=round(days, 2),
        whole_travel_days=0 if distance_km == 0 else ceil(days),
        fatigue_pressure=fatigue,
    )


def encounter_check_count(*, travel_days: float, danger: str) -> int:
    """Return a maximum number of meaningful risk checks, not forced encounters.

    A check can resolve to no encounter. The function deliberately caps repeated
    checking so travel does not become random-combat spam.
    """
    if travel_days < 0:
        raise ValueError("travel_days must be non-negative")
    if danger not in DANGER_PRESSURE:
        raise ValueError(f"unknown danger tier: {danger}")
    pressure = DANGER_PRESSURE[danger]
    if pressure == 0 or travel_days == 0:
        return 0
    return min(3, ceil(travel_days * pressure / 100))
