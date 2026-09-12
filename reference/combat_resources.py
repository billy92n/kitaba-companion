"""Candidate combat, injury and mana resource helpers for Kitaba.

PROPOSAL only. The functions are intentionally small and testable so damage,
armor, injury, recovery and overchanneling can be calibrated before being
promoted into campaign canon.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor


OUTCOME_HARM_MULTIPLIER = {
    "partial_success": 0.65,
    "success": 1.0,
    "exceptional_success": 1.5,
}

MANA_COST_FRACTION = {
    "trivial": 0.01,
    "light": 0.03,
    "moderate": 0.07,
    "heavy": 0.12,
    "major": 0.20,
    "extreme": 0.35,
}

REST_RECOVERY_FRACTION = {
    "poor": 0.08,
    "normal": 0.15,
    "excellent": 0.25,
    "medical": 0.35,
}

INJURY_RECOVERY_MULTIPLIER = {
    "none": 1.0,
    "negligible": 1.0,
    "minor": 0.90,
    "serious": 0.65,
    "critical": 0.35,
    "catastrophic": 0.10,
}


@dataclass(frozen=True)
class HarmResult:
    damage: int
    hp_after: int
    injury_severity: str
    incapacitated: bool
    death_risk: bool


@dataclass(frozen=True)
class ManaSpendResult:
    mana_after: int
    paid: int
    deficit: int
    overchannel_severity: str | None


@dataclass(frozen=True)
class RecoveryResult:
    hp_after: int
    recovered: int
    injury_persists: bool


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def injury_severity_for_damage(damage: int, hp_max: int) -> str:
    if hp_max <= 0:
        raise ValueError("hp_max must be positive")
    if damage < 0:
        raise ValueError("damage must be non-negative")
    ratio = damage / hp_max
    if ratio < 0.05:
        return "negligible"
    if ratio < 0.12:
        return "minor"
    if ratio < 0.25:
        return "serious"
    if ratio < 0.40:
        return "critical"
    return "catastrophic"


def apply_harm(
    *,
    hp_current: int,
    hp_max: int,
    base_harm: int,
    protection: int = 0,
    resilience: int = 0,
    outcome: str = "success",
    lethal_source: bool = False,
) -> HarmResult:
    if hp_max <= 0:
        raise ValueError("hp_max must be positive")
    if not 0 <= hp_current <= hp_max:
        raise ValueError("hp_current must be within 0..hp_max")
    if base_harm < 0 or protection < 0:
        raise ValueError("base_harm and protection must be non-negative")
    if not -10 <= resilience <= 10:
        raise ValueError("resilience must be within -10..10")
    if outcome not in OUTCOME_HARM_MULTIPLIER:
        raise ValueError(f"unsupported harm outcome: {outcome}")

    scaled = floor(base_harm * OUTCOME_HARM_MULTIPLIER[outcome] + 0.5)
    damage = max(0, scaled - protection - resilience)
    hp_after = clamp(hp_current - damage, 0, hp_max)
    severity = injury_severity_for_damage(damage, hp_max)
    incapacitated = hp_after == 0
    death_risk = incapacitated and (lethal_source or severity in {"critical", "catastrophic"})
    return HarmResult(damage, hp_after, severity, incapacitated, death_risk)


def mana_cost(mana_max: int, intensity: str) -> int:
    if mana_max <= 0:
        raise ValueError("mana_max must be positive")
    if intensity not in MANA_COST_FRACTION:
        raise ValueError(f"unknown mana intensity: {intensity}")
    return max(1, floor(mana_max * MANA_COST_FRACTION[intensity] + 0.5))


def overchannel_severity(deficit: int, mana_max: int) -> str | None:
    if mana_max <= 0:
        raise ValueError("mana_max must be positive")
    if deficit < 0:
        raise ValueError("deficit must be non-negative")
    if deficit == 0:
        return None
    ratio = deficit / mana_max
    if ratio <= 0.05:
        return "strain"
    if ratio <= 0.15:
        return "injury_risk"
    if ratio <= 0.30:
        return "severe_injury_risk"
    if ratio <= 0.50:
        return "coma_risk"
    return "death_risk"


def spend_mana(*, mana_current: int, mana_max: int, cost: int, allow_overchannel: bool = False) -> ManaSpendResult:
    if mana_max <= 0:
        raise ValueError("mana_max must be positive")
    if not 0 <= mana_current <= mana_max:
        raise ValueError("mana_current must be within 0..mana_max")
    if cost < 0:
        raise ValueError("cost must be non-negative")
    if cost <= mana_current:
        return ManaSpendResult(mana_current - cost, cost, 0, None)
    if not allow_overchannel:
        raise ValueError("insufficient mana without overchannel permission")

    deficit = cost - mana_current
    return ManaSpendResult(0, mana_current, deficit, overchannel_severity(deficit, mana_max))


def recover_resource(current: int, maximum: int, fraction: float) -> int:
    """Generic bounded recovery helper; the fiction chooses the recovery fraction."""
    if maximum <= 0:
        raise ValueError("maximum must be positive")
    if not 0 <= current <= maximum:
        raise ValueError("current must be within 0..maximum")
    if not 0 <= fraction <= 1:
        raise ValueError("fraction must be within 0..1")
    recovered = floor(maximum * fraction + 0.5)
    return min(maximum, current + recovered)


def recover_hp_after_safe_rest(
    *,
    hp_current: int,
    hp_max: int,
    rest_quality: str = "normal",
    injury_severity: str = "none",
) -> RecoveryResult:
    """Candidate long-rest recovery that does not erase persistent injuries.

    HP represents recoverable fighting capacity. Injury entities remain separate
    canon and must be treated/healed on their own timeline.
    """
    if hp_max <= 0:
        raise ValueError("hp_max must be positive")
    if not 0 <= hp_current <= hp_max:
        raise ValueError("hp_current must be within 0..hp_max")
    if rest_quality not in REST_RECOVERY_FRACTION:
        raise ValueError(f"unknown rest quality: {rest_quality}")
    if injury_severity not in INJURY_RECOVERY_MULTIPLIER:
        raise ValueError(f"unknown injury severity: {injury_severity}")

    fraction = REST_RECOVERY_FRACTION[rest_quality] * INJURY_RECOVERY_MULTIPLIER[injury_severity]
    recovered = floor(hp_max * fraction + 0.5)
    hp_after = min(hp_max, hp_current + recovered)
    actual_recovered = hp_after - hp_current
    persists = injury_severity not in {"none", "negligible"}
    return RecoveryResult(hp_after, actual_recovered, persists)
