"""Executable reference for Kitaba's candidate progression/resolution model.

This module is a PROPOSAL used for calibration and regression tests. It is not
campaign canon until the corresponding rules are promoted into the MASTER
SOURCE / MJ contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor


MASTERY_MODIFIERS = {
    "untrained": -25,
    "novice": -15,
    "apprenti": -5,
    "competent": 5,
    "confirme": 15,
    "expert": 25,
    "maitre": 35,
}

DIFFICULTY_MODIFIERS = {
    "routine": 30,
    "easy": 15,
    "standard": 0,
    "hard": -15,
    "severe": -30,
    "extreme": -45,
    "nearly_impossible": -60,
}

LEARNING_BASE = {
    "trivial": 0,
    "routine": 1,
    "meaningful": 2,
    "demanding": 4,
    "hard": 7,
    "severe": 10,
    "breakthrough": 14,
}

OUTCOME_MULTIPLIERS = {
    "success": 1.0,
    "partial": 1.0,
    "instructive_failure": 0.8,
    "uninstructive_failure": 0.25,
    "exceptional": 1.15,
}

FEEDBACK_MULTIPLIERS = {
    "poor": 0.75,
    "normal": 1.0,
    "teacher": 1.25,
}

REPETITION_MULTIPLIERS = (1.0, 0.5, 0.25, 0.0)

MASTERY_THRESHOLDS = (
    (1200, "Maître"),
    (650, "Expert"),
    (300, "Confirmé"),
    (120, "Compétent"),
    (40, "Apprenti"),
    (0, "Novice"),
)


@dataclass(frozen=True)
class ResolutionResult:
    target: int
    roll: int
    outcome: str
    hazard_escalation_possible: bool = False


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def mastery_tier(learning_points: int) -> str:
    if learning_points < 0:
        raise ValueError("learning_points must be non-negative")
    for threshold, tier in MASTERY_THRESHOLDS:
        if learning_points >= threshold:
            return tier
    raise AssertionError("unreachable")


def success_target(
    mastery: str,
    difficulty: str,
    *,
    characteristic_modifier: int = 0,
    context_modifier: int = 0,
) -> int:
    if mastery not in MASTERY_MODIFIERS:
        raise ValueError(f"unknown mastery: {mastery}")
    if difficulty not in DIFFICULTY_MODIFIERS:
        raise ValueError(f"unknown difficulty: {difficulty}")
    if characteristic_modifier not in {-10, -5, 0, 5, 10}:
        raise ValueError("characteristic_modifier must be one of -10,-5,0,5,10")
    if not -30 <= context_modifier <= 30:
        raise ValueError("context_modifier must be within -30..30")

    raw = (
        50
        + MASTERY_MODIFIERS[mastery]
        + DIFFICULTY_MODIFIERS[difficulty]
        + characteristic_modifier
        + context_modifier
    )
    return clamp(raw, 5, 95)


def resolve_roll(
    target: int,
    roll: int,
    *,
    exceptional_possible: bool = True,
    partial_possible: bool = True,
    hazardous: bool = False,
) -> ResolutionResult:
    if not 5 <= target <= 95:
        raise ValueError("target must be within 5..95")
    if not 1 <= roll <= 100:
        raise ValueError("roll must be within 1..100")

    exceptional_ceiling = max(1, floor(target * 0.10))
    if exceptional_possible and roll <= exceptional_ceiling:
        outcome = "exceptional_success"
    elif roll <= target:
        outcome = "success"
    elif partial_possible and roll <= min(99, target + 15):
        outcome = "partial_success"
    else:
        outcome = "failure"

    return ResolutionResult(
        target=target,
        roll=roll,
        outcome=outcome,
        hazard_escalation_possible=bool(hazardous and roll == 100 and outcome == "failure"),
    )


def learning_award(
    challenge: str,
    outcome: str,
    *,
    feedback: str = "normal",
    repetition_index: int = 0,
) -> int:
    if challenge not in LEARNING_BASE:
        raise ValueError(f"unknown challenge: {challenge}")
    if outcome not in OUTCOME_MULTIPLIERS:
        raise ValueError(f"unknown outcome: {outcome}")
    if feedback not in FEEDBACK_MULTIPLIERS:
        raise ValueError(f"unknown feedback: {feedback}")
    if repetition_index < 0:
        raise ValueError("repetition_index must be non-negative")

    repetition_multiplier = REPETITION_MULTIPLIERS[min(repetition_index, len(REPETITION_MULTIPLIERS) - 1)]
    raw = (
        LEARNING_BASE[challenge]
        * OUTCOME_MULTIPLIERS[outcome]
        * FEEDBACK_MULTIPLIERS[feedback]
        * repetition_multiplier
    )
    return max(0, int(floor(raw + 0.5)))
