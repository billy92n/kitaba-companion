# Kitaba Companion — studio adaptation guide

Status: **technical positioning for the 0.1.6 MVP candidate**. This document is intentionally non-commercial: it describes what the prototype proves and what a studio would need to adapt. It is not a pricing, licensing or negotiation document.

## What the prototype is meant to prove

Kitaba Companion is a proof that a long-form AI-assisted RPG can preserve a trustworthy campaign state outside the conversational model while still feeling like one evolving world.

The value is not a single UI screen. It is the combination of:

- persistent canon independent from one chat/session;
- hidden/player-visible state separation;
- atomic versioned updates;
- recoverable timelines and backups;
- living world presentation (map, relations, journal, knowledge);
- persistent visual references tied to known entities;
- a short interactive narration contract instead of passive text walls.

## What is prototype-specific today

The current build assumes:

- Windows desktop via Tauri;
- React UI;
- Rust backend;
- SQLite local persistence;
- ChatGPT as the current narrative/gameplay authority;
- file/clipboard-oriented context and update exchange during development/playtest.

These choices make the concept testable. They are not all requirements of a commercial adaptation.

## What a studio can substitute

### Narrative / gameplay authority

Current: ChatGPT produces narration, outcomes and `KITABA_UPDATE` state changes.

Possible adaptation: studio LLM stack, deterministic RPG rules, authored quest system, hybrid AI/runtime or existing game server.

The Companion concept only requires that the authority emits validated mutations with provenance, revision and visibility intent.

### Persistence

Current: local SQLite.

Possible adaptation: encrypted local profile, cloud save, account service, console save container or server-authoritative state.

The important invariant is versioned canonical state and recoverable transitions, not SQLite itself.

### Client

Current: Tauri/React desktop Companion.

Possible adaptation: in-game overlay, game menu, web companion, mobile app, launcher integration or embedded engine UI.

The data model is intended to survive a reskin/rehost.

### World presentation

Current: 2D interactive physical map plus structured entities.

Possible adaptation: proprietary world map, 3D map, quest log, codex, relationship graph, bestiary or diegetic journal.

Unknown/approximate/exact knowledge states should remain distinct even if rendered differently.

### Visual continuity

Current: local imported assets with player-safe bindings to known entities and current-state variants.

Possible adaptation: studio asset database, generative-image pipeline, authored portraits, character renderer or screenshot/reference service.

The reusable idea is that visual identity is persistent data, not a disposable prompt.

## Minimum integration contract

A production adaptation needs equivalents for:

1. **Campaign identity** — stable campaign/save id.
2. **Revision** — monotonic canonical revision.
3. **Timeline identity** — prevents stale/dead-branch updates from being accepted.
4. **Entity identity** — stable ids for characters, places, factions, items and other persistent subjects.
5. **Visibility** — at minimum player-visible versus hidden-authority state.
6. **Atomic mutation batch** — either the whole update applies or none of it does.
7. **Context projection** — export/query only the state the narrative authority needs.
8. **Backup/recovery** — restore without silently rewriting canon.
9. **Audit/provenance** — trace where important changes came from.

## Studio-facing 10–15 minute proof

The strongest demonstration is not a tour of every menu. It should prove the continuity loop:

1. open an already-lived campaign;
2. show character + close relation + journal continuity;
3. open the map and find the current location;
4. show a known character/place visual reference;
5. apply a prepared update that changes the world and reveals/repositions something;
6. show the change appearing in the ordinary player surfaces;
7. show revision/timeline/integrity information;
8. create/restore a technical backup on a disposable demo copy if time allows.

The message should be: **the narrative model can change, the chat can end, the client can restart — the world still knows what is true.**

## What should not be oversold in 0.1.6

The MVP does not yet prove:

- production cloud scale;
- multiplayer conflict resolution;
- turnkey SDK integration for Unity/Unreal;
- automatic cross-chat transfer of image bytes;
- automatic music control;
- finished story-book export;
- finalized combat/progression/economy rules;
- console/mobile certification;
- model-provider abstraction as shipping code.

Those are roadmap/adaptation topics, not reasons to weaken the core demo by pretending they already exist.

## Evaluation questions a studio should be able to answer after the demo

- Can this continuity layer be attached to our existing RPG/game loop?
- Can we substitute our own AI/rules/runtime without discarding the persistent-state model?
- Does the PLAYER/hidden-state split solve a real spoiler/authority problem for our design?
- Does the atlas/visual-memory approach make long-form AI play feel materially more coherent?
- Is the state model generic enough to carry our own entities and fields?
- Which pieces should remain a companion versus move inside the game client?

A successful MVP does not need to answer every production question. It needs to make those questions worth discussing with a studio.