# Architecture

## Separation of responsibilities

### Current prototype: ChatGPT side
- narration and dialogue;
- action resolution;
- world evolution;
- NPC decisions;
- time advancement;
- gameplay consequences;
- production of versioned `KITABA_UPDATE` payloads and consumption of exported context.

### Kitaba Companion
- canonical local persistence;
- anti-spoiler PLAYER / GM separation;
- synchronization state;
- Rest Points and rollback storage;
- dead-timeline persistence;
- backup/restore and integrity diagnostics;
- media/visual-reference persistence;
- living-atlas presentation from player-visible world data;
- import/export protocol surface;
- player-facing UI.

The Companion does **not** need to know how prose was generated or which model/rules engine selected an outcome. It needs a validated state transition and a defined visibility scope.

## Studio adaptation boundary

The 0.1.6 prototype is ChatGPT-driven, but the reusable product concept is the boundary between a **narrative/gameplay authority** and a **persistent continuity client**.

A studio can replace the current ChatGPT workflow with, for example:

- an in-house LLM orchestration layer;
- a deterministic or hybrid rules engine;
- authored quests plus AI dialogue;
- a server-authoritative multiplayer/single-player backend;
- a proprietary game runtime that emits the same categories of state changes.

Those integrations are not claimed as implemented in the current build. The architectural goal is that they should not require rewriting the persistence model merely because the narrative provider changes.

### Reusable seams

1. **Update seam** — external authority sends atomic, revision-checked state mutations.
2. **Context seam** — Companion exports the known canonical state needed by the authority to continue coherently.
3. **Visibility seam** — PLAYER and GM/private data are separated before player-facing serialization.
4. **Presentation seam** — React/Tauri is the current client, but map, journal, relations, knowledge and visual-reference data are represented independently from a specific visual skin.
5. **Storage seam** — SQLite is the current local implementation; versioned entity documents keep most RPG-specific fields extensible.

## Data strategy

The persistence core uses SQLite. Stable entities are stored as versioned documents (`entity_documents`) with:

- stable UUID;
- `campaign_id`;
- `entity_type`;
- visibility scope (`PLAYER` or `GM`);
- entity version;
- JSON payload;
- archive state;
- update provenance.

This deliberately keeps the protocol extensible without requiring a database migration for every new RPG field. Critical infrastructure (campaigns, timelines, applied updates, Rest Points, dead timelines, backups, audit log, assets) remains in typed SQL tables.

Visual-reference bindings are persisted beside campaign assets and included in technical backups without requiring a new SQLite schema version for the 0.1.6 candidate.

## Anti-spoiler rule

Player reads are backend-side filtered. The frontend never receives GM rows in player mode.

`reveal` does **not** flip a GM secret into player visibility. It creates or updates a separate player-facing record using only the explicitly revealed payload supplied by the narrative/gameplay authority. The original GM record remains hidden.

This rule is product-critical for any adaptation where an AI or simulation knows more than the player should see.

## Timeline model

Every campaign has:

- monotonically increasing `current_revision`;
- active `current_timeline_id`.

A normal update must match both.

After death rollback:

1. current timeline state is archived as a dead-timeline snapshot;
2. dead-timeline resolutions are preserved;
3. the last authorized Rest Point state is restored;
4. a new timeline id is created;
5. revision increases rather than going backward.

This prevents stale updates from a dead branch being applied later.

## MVP proof versus future product

The MVP proves the continuity architecture with a local Windows Companion and ChatGPT-mediated gameplay. It does not yet claim production-scale cloud sync, studio SDKs, multiplayer concurrency, console/mobile clients, model-provider abstraction code, telemetry or live-service operations.

Those are adaptation/productization layers that should be designed with a partner only after the core continuity proposition has been validated.