# Changelog

## 0.1.3 — campaign launch hardening

- Added explicit persistent World State entity categories for factions, organizations, settlements, states, markets, economy, conflicts, world events, environment, resources, infrastructure, laws and politics.
- Added a player-facing World section while keeping unknown/off-screen world truth in GM scope.
- Hardened ChatGPT update import so file-loaded raw JSON is hidden by default; manual raw-paste mode now carries an explicit spoiler warning.
- Added a campaign media library entry point for NPC portraits and other illustrations, backed by the existing checksum-protected asset store and `.kitaba` backups.
- Campaign integrity diagnostics now refresh automatically with campaign data.
- Reduced search re-serialization work by precomputing searchable entity text only when campaign entities change.
- Added regression tests for hidden World State persistence and raw-update anti-spoiler UI.


## 0.1.2 — hardened direct-source Windows build

- Replaced the legacy Base64/materialization build path with the committed React/Tauri/Rust source tree.
- Added reproducible npm and Rust lockfiles; production CI now uses `npm ci`.
- Hardened campaign-scoped restore so database and campaign assets are swapped with rollback protection.
- Hardened full-backup restore so database and all managed assets recover together if restoration fails.
- Added production Rust restore regression coverage, including multi-campaign and asset preservation checks.
- Updated the Windows CI pipeline to current official GitHub Actions runtimes, added per-branch concurrency/cancellation, and removed obsolete one-shot mutation workflows that generated misleading failures.
- Windows CI verifies the executable Python reference suite, frontend production build, Rust tests, Tauri packaging, Windows GUI PE subsystem, and artifact upload.
- Verified production artifact contains both `kitaba-companion.exe` and `Kitaba Companion_0.1.2_x64-setup.exe`.

## 0.1.0-foundation

- Added SQLite schema and migration tracking.
- Added versioned KITABA_UPDATE and KITABA_CONTEXT JSON schemas.
- Added executable Python reference core for revision checking, atomic updates, player/GM separation, reveal semantics, context export, Rest Points, death rollback, dead-timeline resolution persistence, and technical backups.
- Added React/Tauri application shell with Import from ChatGPT / Export to ChatGPT actions.
- Added Rust/Tauri persistence/synchronization scaffold mirroring the reference core.
- Added Windows GitHub Actions build workflow.
- Added 16 passing reference tests.

## Unreleased — playable-build work

- Added dedicated RPG views for character state, characteristics, Awakening, inventory/equipment, relations/NPCs, knowledge, journal, and missions.
- Added persistent ChatGPT synchronization tracking (`last_gm_export_revision`, player/full export timestamps) with a visible "context to re-export" state.
- Added schema migration v4 for export synchronization metadata.
- Aligned the Rust technical backup format with the specified/reference `.kitaba` ZIP container (`manifest.json` + checksum-protected `campaign.sqlite`) instead of a raw SQLite file.
- Added defensive backup manifest/schema/checksum validation.
- Corrected a false-positive automated test for the "elapsed time requires explicit game_time.set" invariant.
- Added dedicated Skills, Magic, known-history Timeline, and Adventurer Card views.
- Fixed sidebar rendering so numeric zero (including 0 HP) is displayed instead of being mistaken for an unknown value.
- Tightened the Rust protocol model so the required `operations` and `gm_operations` arrays cannot be silently omitted.
- Rest Point selection now follows canonical snapshot revision first, not wall-clock metadata, preventing rollback ambiguity if timestamps are skewed.
- Fixed Rust `KITABA_CONTEXT.continuity_metadata.schema_version` to use the actual current schema version instead of a stale hard-coded value.
- Added schema round-trip and Rest Point ordering regression tests.
- Fixed a multi-campaign backup isolation flaw: a campaign-scoped `.kitaba` no longer silently contains other campaigns.
- Added merge-style campaign restoration so restoring one campaign does not erase unrelated campaigns already present in the Companion.
- Added regression tests for campaign backup isolation and merge restoration.
- Reference verification increased to 37 passing tests.

- Added managed campaign visual assets for world map and player portrait, with image signature validation and local checksum verification.
- Campaign `.kitaba` backups now include registered visual assets and restore them without overwriting unrelated campaigns.
- Added regression tests for asset validation, singleton portrait replacement, backup asset round-trip, and multi-campaign asset isolation.
- Added runtime UI controls to import/replace the world map and Sully portrait; the bundled canonical map remains the fallback.
- Added Windows bundle icons and explicit Tauri icon configuration to reduce packaging surprises.
- Reference verification increased to 41 passing tests.
- GM context dead-timeline resolution exports now preserve source timeline provenance, source update, and creation timestamp for stronger anti-save-scum continuity across ChatGPT conversations.
- Windows build workflow now runs the executable Python reference suite before frontend/Rust/Tauri build gates.
- Reference verification increased to 42 passing tests.
- Added audited manual entity corrections for both player-visible and GM-only records; every correction creates a pre-change technical backup, advances canonical revision, enforces entity-version concurrency, and respects immutable protection.
- GM manual correction audit entries intentionally omit secret entity identifiers, types, reasons, and patch contents from player-visible audit summaries.
- Added a dedicated hidden GM map layer inside the explicitly unlocked GM Vault; the normal world map still receives player-visible entities only.
- Added manual-correction UI with strong confirmations and automatic sync-dirty behavior after corrections.
- Static TypeScript verification uncovered and fixed a real strict-mode build issue in recursive display helpers (`text` now has an explicit string return type).
- Reference verification increased to 46 passing tests.

## 0.1.0-foundation — campaign safety pass

- Added campaign archive/restore management and guarded permanent deletion.
- Permanent deletion now creates an automatic pre-delete technical backup first.
- Added non-spoiler campaign integrity diagnostics (SQLite integrity, foreign keys, active timeline, revision bounds, Rest Point hashes, dead timeline hashes, asset integrity, visibility domain).
- Added path-containment guards so registered assets cannot escape their campaign directory.
- Re-locks the GM Vault when navigating away to reduce accidental spoilers.
- Changed ChatGPT context export filenames to standard `.json` for maximum upload compatibility.
- Reference verification suite increased to 52 passing tests.

- Added production Rust unit tests for campaign/update round-trip, GM/player separation, duplicate update rejection, archive/restore integrity, and asset path containment.
- Added cross-layer parity tests to prevent drift between reference SQL migrations and production Rust migrations, protocol versions, frontend invoke names, Tauri command registration, Windows bundle configuration, and release workflow gates.
- Corrected first-campaign onboarding so the user is explicitly directed to export the full MJ context to ChatGPT rather than only the player context.
- Removed unreachable dead code in the reference engine manual-correction path.
- Reworked responsive navigation into a true mobile drawer with backdrop and hamburger trigger, matching the intended PC persistent-sidebar / mobile-drawer interaction model.
- Reference verification increased to 61 passing tests.
