# Kitaba Companion

Kitaba Companion is the local persistence and campaign-state prototype for **Kitaba Solo**.

The current prototype uses ChatGPT as GM/narrator/resolver and the Companion as the canonical local state layer. The product boundary is deliberately protocol-based: a studio adaptation can replace the current AI/gameplay side while retaining the persistence, visibility, timeline, backup, atlas, encyclopedia and visual-continuity concepts.

Current exchange model:

- `KITABA_UPDATE` — narrator/gameplay side → Companion
- `KITABA_CONTEXT` — Companion → narrator/gameplay side

## Current repository status

Stable production remains **0.1.5** on `main`.

Branch `next-system-pass` contains the **0.1.6 MVP candidate**. It remains isolated until migration-copy and final human smoke gates are complete. SQLite stays on schema v4; the 0.1.6 MVP adds no destructive schema migration.

The 0.1.6 candidate adds and hardens:

- living atlas with strict bounds, current location, search, layers, clustering, regions/routes and approximate-location uncertainty areas;
- a player Encyclopedia/Codex that organizes persistent PLAYER knowledge into settlements/places, figures/relations, lineages, bestiary/troops, kingdoms/factions, concepts and world/history without creating a second truth store;
- persistent visual-reference bindings for player-visible characters/places, state variants and scene references;
- direct display of current visual references in ordinary character/relation/place and encyclopedia surfaces where relevant;
- image-fit hardening so fixed portrait slots center-crop without stretching while previews/maps preserve the full image;
- concise interactive narration contract inherited from the 0.1.5 playtest;
- versioned Windows packaging as 0.1.6;
- tested foundations for progression/resolution, combat/resources, economy/travel, ambience and editorial story capture. These gameplay models remain **PROPOSAL** until explicitly promoted into the campaign MASTER.

The latest client-smoke correction moves the visual-reference launcher into the Media/visual-continuity page so it never floats above unrelated content.

## Product concept

The Companion is not intended to replace a game engine. It demonstrates a reusable continuity layer for long-form AI-assisted RPG experiences:

1. canonical state persists independently of a chat session;
2. player-visible and hidden GM data are separated at the backend boundary;
3. updates are atomic, revision-checked and timeline-aware;
4. maps, relationships, journal, encyclopedia knowledge and visual references evolve with play;
5. backups and integrity diagnostics make long campaigns recoverable;
6. the presentation layer can be reskinned or embedded while the state/protocol concepts remain reusable.

For the current prototype, ChatGPT performs narration, dialogue, action resolution, world evolution, NPC decisions, time advancement and gameplay consequences. A studio integration may substitute its own model orchestration, rules engine or authored runtime behind the same conceptual boundary.

The long-term Kitaba product direction is to put the complete player loop inside the Companion through a controlled narrative API/runtime adapter. Model output still does not write directly to the save: canonical mutations remain validated by the Companion state layer.

## Core invariants

1. No real-time clock advances game time.
2. Companion never silently invents or resolves gameplay canon outside the authorized narrative/gameplay runtime.
3. GM secrets never enter player exports or ordinary player reads.
4. Updates are atomic and revision-checked.
5. Rest Points are gameplay checkpoints; technical backups are disaster recovery only.
6. Death rollback restores the canonical checkpoint state while preserving dead-timeline records.
7. A full context export must be sufficient to continue a campaign in a fresh narrator session.
8. Existing campaign canon is not rewritten merely because the Companion, renderer or presentation rules are upgraded.
9. The Encyclopedia is a PLAYER projection of canonical entities, never an independent lore database and never a path to hidden GM truth.

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

The current 0.1.6 candidate has passed the full Windows pipeline on its release-hardening branch; final promotion remains gated by real-save migration/smoke validation and must not modify the live 0.1.5 campaign as its first migration test.

## Adaptation and presentation docs

- `docs/ARCHITECTURE.md` — current responsibilities and reusable seams;
- `docs/STUDIO_ADAPTATION_GUIDE.md` — what a studio can substitute and what the prototype actually proves;
- `docs/API_INTEGRATION_TARGET.md` — target architecture for playing entirely inside the Companion through a controlled runtime/API;
- `docs/PLAYER_ENCYCLOPEDIA_CONTRACT.md` — player-only Codex authority, categories and future graph/API direction;
- `docs/MVP_PRESENTATION_SCOPE.md` — studio-facing MVP claims and boundaries;
- `docs/STUDIO_DEMO_RUNBOOK.md` — deterministic 10–15 minute demonstration flow.