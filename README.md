# Kitaba Companion

Kitaba Companion is the local persistence and campaign-state application for **Kitaba Solo**.

It is **not** the game engine. ChatGPT remains the GM, narrator, resolver, and world simulator. The Companion stores canonical state locally and exchanges versioned files with ChatGPT:

- `KITABA_UPDATE` — ChatGPT → Companion
- `KITABA_CONTEXT` — Companion → ChatGPT

## Current repository status

Version **0.1.3** uses the real React/Tauri/Rust source tree directly. The former Base64/materialization build path has been removed.

Implemented and covered by automated verification:

- campaign revisions and stale-update rejection
- update idempotency
- player/GM data separation
- atomic update application
- full/player context export
- Rest Points distinct from technical backups
- death rollback model preserving dead-timeline resolutions
- checksum-protected technical `.kitaba` backups
- campaign-scoped and full-backup restore protection
- managed campaign visual assets
- audit metadata and integrity diagnostics

The production Windows pipeline now runs the Python reference suite, reproducible frontend installation/build, Rust tests, Tauri packaging, PE GUI-subsystem verification, and artifact upload. A complete 0.1.3 Windows build has passed these gates on GitHub Actions.

## Core invariants

1. No real-time clock advances game time.
2. Companion never resolves gameplay.
3. GM secrets never enter player exports.
4. Updates are atomic and revision-checked.
5. Rest Points are gameplay checkpoints; technical backups are disaster recovery only.
6. Death rollback restores the canonical checkpoint state while preserving dead-timeline records.
7. A full `KITABA_CONTEXT` must be sufficient to continue the campaign in a new ChatGPT conversation.

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
