# Kitaba Companion — cible d'intégration API

Status: **PARTIAL DESIGN TARGET / post-MVP product direction**. This document does not mean an API provider is already integrated in 0.1.6.

## Product direction

The long-term target is that a player can perform the entire Kitaba loop from the Companion itself:

1. open a campaign;
2. type/speak an action in the app;
3. receive streamed narration/dialogue in the app;
4. receive three contextual action suggestions plus a permanently available free-input path when a player decision is expected;
5. let the narrative/gameplay authority read the required campaign context through a controlled backend interface;
6. receive a structured canonical update;
7. validate/apply that update atomically;
8. refresh character, relations, journal, map and visual continuity without manual export/import.

The current ChatGPT + file/clipboard workflow remains a valid prototype/fallback path. The API target exists to remove friction, not to invalidate existing campaigns.

## Architectural rule

Do not fuse "AI text generation" and "canonical persistence" into one uncontrolled process.

The future in-app runtime should still preserve two roles:

- **Narrative/gameplay authority**: model/rules/orchestrator decides prose, NPC behavior, uncertainty outcomes and proposed world changes.
- **Companion state authority**: validates revision/timeline/visibility and applies only valid canonical mutations.

The UI may host both inside one application, but the boundary must remain explicit so a malformed model response cannot silently rewrite the save.

## Proposed runtime layers

### 1. Conversation surface

Player input, streamed answer, optional voice and scene presentation.

This layer never writes canonical state directly.

When the authority genuinely hands control back to the player, the presentation layer should support the Kitaba **3+1 guidance contract**:

- three short, context-aware suggestions with meaningfully different intentions where possible;
- one always-available free input path (`Autre` / custom action);
- suggestions are examples, never exhaustive legal moves;
- the player may rewrite, combine or ignore them;
- unselected suggestions are never persisted as player decisions;
- suggestions must not leak hidden information, identify an optimal answer or promise success.

This contract should be represented separately from narration text so a future UI can render quick-action buttons without parsing prose.

Conceptual response shape may therefore include a player-safe presentation object such as:

- `narration`;
- `decision_expected`;
- `suggested_actions[0..3]`;
- `free_input_allowed=true`.

The exact transport schema remains post-MVP and provider-neutral.

### 2. Narrative Runtime Adapter

Provider-neutral interface between Kitaba and the selected narrative engine.

Conceptual operations:

- `prepare_turn(campaign_id)` — obtain the minimum context projection needed for the next turn;
- `submit_player_action(campaign_id, text, client_turn_id)` — send player intent;
- `stream_narration(...)` — return prose/dialogue incrementally;
- `propose_choices(...)` — return up to three player-safe contextual suggestions when a decision is expected;
- `propose_update(...)` — return structured state mutations separate from prose;
- `request_visual_intent(...)` — optional future visual-generation request derived from already-canonical identity/state;
- `health/capabilities` — report which optional runtime features are available.

The first implementation can target one provider, but internal application code should depend on this adapter rather than provider-specific calls scattered through the UI.

### 3. Canonical Update Gate

All proposed mutations pass through the existing Kitaba validation model:

- campaign id;
- base revision;
- timeline id;
- visibility;
- entity/version constraints;
- atomicity;
- anti-spoiler rules;
- audit/provenance.

Only after validation does the Companion advance canonical state.

A generated suggestion never enters canonical state merely because it was displayed. Only an actual player action and validated durable consequences may be persisted.

### 4. Context Projector

Do not send the entire database blindly on every turn.

The projector should build context from:

- immutable Genesis snapshot/version;
- current player character state;
- current place/scene;
- relevant relations, missions, knowledge and recent events;
- necessary hidden GM state for the authority only;
- compact continuity summaries;
- references to persistent visual identities when supported;
- optional initial character anchor if the player explicitly created one;
- durable character-development observations only when they are narratively established.

Large historical material remains queryable rather than recopied into every request.

## Protagonist nature and character development

The future API runtime must not reduce the protagonist to a fixed personality label or moral alignment.

Kitaba distinguishes:

- an optional light **initial character anchor** chosen by the player;
- the character that emerges through repeated choices, costly decisions, habits and contradictions;
- public reputation, which depends only on what NPCs/world actors can actually know.

The runtime may use established character-development context to improve continuity, but it must never turn an inferred trait into an automatic player action. Player agency remains authoritative over the protagonist's voluntary decisions.

If no initial anchor exists, the runtime must treat that field as OPEN rather than inventing one retroactively.

## API-provider policy

The architecture should permit provider replacement. A studio may use:

- OpenAI API;
- another LLM provider;
- a local model;
- a deterministic rules/narrative service;
- a hybrid authored + AI runtime.

Kitaba should not promise provider parity before it exists, but it should avoid making one provider's request/response schema the campaign data model.

## Secret and credential handling

A production API integration must never store provider credentials in:

- `.kitaba` campaign backups;
- Project Sources;
- exported PLAYER or GM contexts;
- audit event bodies;
- repository files.

Credentials belong in platform-appropriate secure storage and must be removable independently of campaign data.

## Player/GM privacy boundary

Even when the model runs through the Companion, player-facing UI must not receive hidden GM documents merely because the runtime needs them.

Preferred flow:

1. backend creates authority-only context;
2. adapter sends it directly to the narrative runtime;
3. runtime returns player prose + player-safe suggestions + structured update proposal;
4. backend validates/applies;
5. frontend receives only player-safe rendered output and player-safe refreshed entities.

## Failure behavior

The campaign must remain recoverable if the network/provider fails.

- failed generation does not advance canonical revision;
- partial streamed prose does not imply a committed update;
- update validation failure leaves the previous state intact;
- retry uses a stable `client_turn_id`/idempotency key where supported;
- manual export/import mode remains a fallback during transition.

## Migration path from current 0.1.6 workflow

### Phase A — 0.1.6 MVP

- prove persistence, atlas, visual continuity, update safety and real-campaign compatibility;
- keep ChatGPT/file exchange as current play loop.

### Phase B — API bridge prototype

- add provider settings/secure credential storage;
- implement one `NarrativeRuntimeAdapter`;
- send a controlled context projection;
- receive narration + 3+1 presentation data + a structured update proposal;
- require the same validation gate as imported `KITABA_UPDATE`.

### Phase C — in-app play loop

- integrated chat/streaming UI;
- quick-action rendering for the three suggested choices plus permanent free input;
- automatic validated update application or explicit player confirmation according to chosen UX;
- automatic refresh of all Companion surfaces;
- recovery/retry/session continuity.

### Phase D — studio integration surface

- formal SDK/service contract;
- provider/runtime adapters;
- embedding hooks for game clients;
- telemetry/operations only after privacy/product requirements are defined.

## MVP impact now

0.1.6 does **not** need a live API integration to be a valid MVP. It does need to avoid architectural decisions that would make the future bridge destructive.

For the studio pitch, this direction is useful because the current Companion demonstrates the hard part first: trustworthy continuity. The API layer then removes manual friction without changing the core canon model.
