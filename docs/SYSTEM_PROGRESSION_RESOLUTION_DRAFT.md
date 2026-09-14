# Kitaba — progression & résolution interne (DRAFT)

Status: **PROPOSAL / calibration candidate**. This document is deliberately not campaign canon yet. It defines a candidate mechanical baseline to be tested before being promoted into the MASTER SOURCE and MJ contract.

## Goals

- No global character level.
- Progress is granular: skills, masteries, magical control, knowledge and physical development evolve for different reasons and at different speeds.
- No XP reward merely for killing an enemy or completing a quest.
- Failure can teach; trivial repetition cannot be farmed indefinitely.
- Player-facing presentation remains qualitative. Exact learning points and resolution rolls are GM/internal data.
- Official Guild rank E→S remains a social/professional evaluation, not the hidden mechanical level of the character.
- No level scaling of the world around the protagonist.

## 1. Skill mastery ladder

A tracked skill may carry a hidden `learning_points` value while the player sees only a qualitative tier and, optionally, a qualitative progress feeling.

| Tier shown to player | Hidden cumulative learning points |
| --- | ---: |
| Novice | 0–39 |
| Apprenti | 40–119 |
| Compétent | 120–299 |
| Confirmé | 300–649 |
| Expert | 650–1199 |
| Maître | 1200+ |

No `skill` entity is required for something the character has never meaningfully learned or practiced.

These thresholds are intentionally nonlinear. Early competence should be perceptible during a campaign; expertise and mastery should require a substantial history.

## 2. Learning award per meaningful event

Only one coherent learning award is granted for one meaningful learning event. Do not award points per sentence, per dice roll or per repeated animation of the same action.

Base learning value:

| Relative learning challenge | Base LP |
| --- | ---: |
| Trivial / already automatic | 0 |
| Routine but still useful | 1 |
| Meaningful | 2 |
| Demanding | 4 |
| Hard | 7 |
| Severe | 10 |
| Breakthrough-level exposure | 14 |

Outcome multiplier:

- full success: ×1.00
- partial success / success with meaningful complication: ×1.00
- instructive failure with usable feedback: ×0.80
- failure with little new information: ×0.25
- exceptional execution: up to ×1.15, never a separate farmable bonus

Learning-context multiplier:

- appropriate skilled teacher / excellent feedback: up to ×1.25
- normal independent practice: ×1.00
- poor feedback / bad method: ×0.75

Round the final award to the nearest whole LP, minimum 0.

### Anti-farming rule

Repeated materially identical practice in the same short in-world window receives diminishing novelty multipliers: ×1.00 → ×0.50 → ×0.25 → ×0 until the context changes, meaningful rest occurs, difficulty rises, feedback changes or a genuinely new problem is introduced.

A dangerous action is not automatically educational. Repeating reckless danger without new learning does not become an XP engine.

## 3. Characteristics and resource growth

The seven main characteristics do **not** gain ordinary skill LP.

Strength, Agility, Endurance and similar underlying characteristics change more slowly through sustained training, maturation, adaptation, major injury/recovery or exceptional long-term conditions. Mana capacity behaves similarly: it is not a reward counter for spell casts.

Control, technique, spell handling, weapon use, languages, crafts, investigation and similar learned capabilities should normally be represented as skills/masteries and can progress through the LP system.

This separation prevents a character from increasing every underlying stat merely by repeating a favored action.

## 4. Hidden uncertainty resolution

When an action is genuinely uncertain and consequential, the GM performs **one hidden d100-equivalent draw**. The player does not set the outcome by phrasing an attempt as a success.

### 4.1 Base target

Start from 50 and modify it.

Skill/mastery modifier:

| Relevant mastery | Modifier |
| --- | ---: |
| Untrained | -25 |
| Novice | -15 |
| Apprenti | -5 |
| Compétent | +5 |
| Confirmé | +15 |
| Expert | +25 |
| Maître | +35 |

Supporting-characteristic modifier:

- clearly weak for the task: -10
- below expected: -5
- ordinary for the task: 0
- clearly strong: +5
- exceptional: +10

Task difficulty modifier:

| Objective task difficulty | Modifier |
| --- | ---: |
| Routine | +30 |
| Easy | +15 |
| Standard | 0 |
| Hard | -15 |
| Severe | -30 |
| Extreme | -45 |
| Nearly impossible | -60 |

Situational factors are then combined into a context modifier normally between -30 and +30. This includes preparation, tools, wounds, fatigue, visibility, time pressure, help, surprise, terrain, target cooperation, social incentives and other real circumstances.

Final success target is clamped to 5–95.

### 4.2 Outcome bands

For target `T` and hidden roll `R` from 1–100:

- `R <= max(1, floor(T × 0.10))`: exceptional success **only when an exceptional outcome is fictionally possible**.
- otherwise `R <= T`: full success.
- otherwise `R <= min(99, T + 15)`: partial success / success with meaningful cost or complication when fiction permits.
- otherwise: failure.

A roll of 100 may intensify an existing hazardous consequence, but it does not create arbitrary death or catastrophe when the attempted action had no such stakes.

The GM does not reroll because the result is inconvenient.

## 5. Opposed actions

For direct opposition, start from a standard task and shift the target by approximately 10 points per meaningful mastery tier difference between actor and opposition, then apply characteristics and context.

Do not reduce social interaction to a persuasion stat alone. NPC goals, trust, fear, leverage, culture, evidence and relationship history are situational factors and may make an attempted request easy, difficult or impossible regardless of eloquence.

## 6. Player-facing progression

The Companion should not expose raw `learning_points` by default.

Preferred visible information:

- qualitative mastery tier;
- short description of what the character can reliably do;
- optional qualitative progress feeling: `début de palier`, `en progression`, `bien établi`, `proche d’un nouveau palier`;
- notable learned techniques or breakthroughs.

Exact internal LP may remain GM-only so that the UI does not turn roleplay into repetitive optimization.

## 7. Update persistence

When a skill materially progresses, the MJ should persist it rather than relying on chat memory.

Suggested player entity data:

```json
{
  "name": "Nom de la compétence",
  "category": "Catégorie",
  "qualitative_level": "Apprenti",
  "qualitative_progress": "en progression",
  "description": "Ce que le personnage sait réellement faire"
}
```

Suggested GM companion entity or GM-only fields may track hidden learning points and recent repetition fingerprints. Do not copy hidden numeric learning data into PLAYER scope unless a future design decision explicitly makes exact XP visible.

## 8. Calibration targets for playtesting

The current candidate is considered healthy if playtests roughly produce these sensations:

- a new skill can visibly improve after several genuinely formative uses or focused training sessions;
- reaching `Compétent` requires repeated meaningful experience rather than one lucky scene;
- `Confirmé` represents a real accumulated history;
- `Expert` is uncommon and cannot be cheaply farmed;
- `Maître` is a long-term achievement and should normally carry narrative evidence in the campaign history;
- an untrained character can still succeed at ordinary tasks;
- a master can still fail under extreme conditions;
- difficult actions remain dangerous without making ordinary play frustrating.

## 9. Not covered by this draft

Still to calibrate separately:

- damage, armor, HP and injury severity;
- mana expenditure/recovery and overchanneling numbers;
- weapon and spell action economy;
- travel pace, fatigue and survival;
- economy/prices;
- crafting quality and material grades;
- reputation propagation;
- exact Guild evaluation procedures.

Those systems should be built on this resolution/progression foundation rather than inventing unrelated probability scales.
