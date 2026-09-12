# Kitaba Companion

Kitaba Companion is the local persistence and campaign-state application for **Kitaba Solo**.

It is **not** the game engine. ChatGPT remains the GM, narrator, resolver, and world simulator. The Companion stores canonical state locally and exchanges versioned files with ChatGPT:

- `KITABA_UPDATE` — ChatGPT → Companion
- `KITABA_CONTEXT` — Companion → ChatGPT

## Current repository status

This repository starts with the persistence/synchronization core first, before UI polish.

Implemented as executable specification in `reference/` and mirrored in the Tauri/Rust architecture:

- campaign revisions and stale-update rejection
- update idempotency
- player/GM data separation
- atomic update application
- full/player context export
- Rest Points distinct from technical backups
- death rollback model preserving dead-timeline resolutions
- technical `.kitaba` backup format
- audit metadata

The React/Tauri shell is included, but the Rust/Tauri build is **not claimed as compiled in this environment** because Rust and the Windows toolchain are unavailable here.

## Core invariants

1. No real-time clock advances game time.
2. Companion never resolves gameplay.
3. GM secrets never enter player exports.
4. Updates are atomic and revision-checked.
5. Rest Points are gameplay checkpoints; technical backups are disaster recovery only.
6. Death rollback restores the canonical checkpoint state while preserving dead-timeline records.
7. A full `KITABA_CONTEXT` must be sufficient to continue the campaign in a new ChatGPT conversation.

## Local verification

The reference core is dependency-light and can be tested with:

```bash
python -m pytest reference/tests -q
```

## Future Windows build

The intended production stack is Tauri 2 + React + TypeScript + SQLite. A GitHub Actions Windows workflow is included as the eventual build path.
