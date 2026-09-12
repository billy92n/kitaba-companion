# Kitaba Companion

Kitaba Companion is the local persistence and campaign-state application for **Kitaba Solo**.

It is **not** the game engine. ChatGPT remains the GM, narrator, resolver, and world simulator. The Companion stores canonical state locally and exchanges versioned files with ChatGPT:

- `KITABA_UPDATE` — ChatGPT → Companion
- `KITABA_CONTEXT` — Companion → ChatGPT

## Current repository status

Version **0.1.5** uses the real React/Tauri/Rust source tree directly and remains on SQLite schema v4, with no new database migration from 0.1.4.

Implemented and covered by automated verification include campaign revision/idempotency rules, player/GM separation, atomic updates, full/player context export, Rest Points and death rollback, checksum-protected `.kitaba` backups, campaign visual assets, integrity diagnostics, generic character creation, discovery-gated navigation, a zoomable/pannable/clickable world map driven by PLAYER entities, visual-continuity guidance, concise enrichment of terse player actions, and hidden resolution of genuinely uncertain actions.

The 0.1.5 production Windows gate on `main` passed the Python reference suite (76 tests), reproducible frontend installation/build, Rust tests (7 tests), Tauri/NSIS packaging, PE GUI-subsystem verification, and artifact upload. See `docs/RELEASE_0.1.5.md` for the validated release metadata.

## Core invariants

1. No real-time clock advances game time.
2. Companion never resolves gameplay; ChatGPT does.
3. GM secrets never enter player exports.
4. Updates are atomic and revision-checked.
5. Rest Points are gameplay checkpoints; technical backups are disaster recovery only.
6. Death rollback restores the canonical checkpoint state while preserving dead-timeline records.
7. A full `KITABA_CONTEXT` must be sufficient to continue the campaign in a new ChatGPT conversation.
8. Existing campaign canon is not rewritten merely because the Companion or presentation rules are upgraded.

## Verification

Reference verification:

```bash
python -m pytest reference/tests -q
```

Production Rust verification:

```bash
cargo test --manifest-path src-tauri/Cargo.toml
```

Frontend production verification:

```bash
npm ci
npm run build
```

## Windows build

The production stack is Tauri 2 + React + TypeScript + SQLite. `.github/workflows/build-windows.yml` builds the x64 Windows application and NSIS installer from the committed direct source and lockfiles.

For a live 0.1.4 campaign, create a technical `.kitaba` backup before installing 0.1.5 over the existing installation. Do not recreate the campaign solely for this upgrade.
