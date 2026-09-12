# Architecture

## Separation of responsibilities

### ChatGPT
- narration and dialogue
- action resolution
- world evolution
- NPC decisions
- time advancement
- gameplay consequences

### Kitaba Companion
- canonical local persistence
- anti-spoiler player/GM separation
- synchronization state
- Rest Points and rollback storage
- dead-timeline persistence
- import/export
- UI only

## Data strategy

The persistence core uses SQLite. Stable entities are stored as versioned documents (`entity_documents`) with:

- stable UUID
- `campaign_id`
- `entity_type`
- visibility scope (`PLAYER` or `GM`)
- entity version
- JSON payload
- archive state
- update provenance

This deliberately keeps the protocol extensible without requiring a database migration for every new RPG field. Critical infrastructure (campaigns, timelines, applied updates, Rest Points, dead timelines, backups, audit log, assets) remains in typed SQL tables.

## Anti-spoiler rule

Player reads are server/backend-side filtered. The frontend never receives GM rows in player mode.

`reveal` does **not** flip a GM secret into player visibility. It creates or updates a separate player-facing record using only the explicitly revealed payload supplied by ChatGPT. The original GM record remains hidden.

## Timeline model

Every campaign has:

- monotonically increasing `current_revision`
- active `current_timeline_id`

A normal update must match both.

After death rollback:

1. current timeline state is archived as a dead-timeline snapshot;
2. dead-timeline resolutions are preserved;
3. the last authorized Rest Point state is restored;
4. a new timeline id is created;
5. revision increases rather than going backward.

This prevents stale updates from a dead branch being applied later.
