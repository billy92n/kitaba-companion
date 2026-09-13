# Kitaba Companion — runbook de démonstration studio

Status: **0.1.6 presentation runbook**. This is a deterministic demo sequence, not a gameplay rule source.

## Goal

In 10–15 minutes, demonstrate one idea clearly:

> **The narrative model can change, the chat can end, the app can restart — the world still knows what is true.**

The audience should understand that Kitaba is not only a chat UI and not only a save manager. It is a continuity layer for long-form RPG experiences.

## Demo preparation

Use a disposable campaign copy containing:

- one established player character;
- one close NPC relation;
- at least one journal entry;
- a world map with current location and several known places;
- one primary visual reference for a known character/place;
- one current-state variant if available;
- a prepared, non-secret update that reveals or better localizes one place;
- green integrity before the demo.

Never use the only copy of a live campaign for a public demonstration.

## 0:00–1:00 — Premise

Explain only the product loop:

- the narrative/gameplay authority decides what happens;
- the Companion keeps canonical continuity;
- PLAYER and hidden authority data are separated;
- changes are versioned and validated instead of trusting free-form prose as a save file.

Do not open with implementation details.

## 1:00–3:00 — A lived campaign

Open the campaign and show:

- character identity/state;
- current in-game time/revision;
- one close relation;
- recent journal continuity.

Key message: this is not a fresh prompt reconstructed from memory; it is persistent campaign state.

Briefly explain character development:

- the player may start with a light personality anchor or leave it OPEN;
- the protagonist's nature emerges through choices and costly decisions rather than a fixed morality slider;
- reputation is separate from internal nature;
- observed traits never take control of voluntary player actions.

## 3:00–4:00 — Guided freedom

Show or describe one player decision using the Kitaba **3+1** pattern:

1. three short contextual suggestions;
2. one permanent free-input path.

Make the point explicit: the suggestions reduce blank-page paralysis but are not exhaustive actions. The player may rewrite, combine or ignore them.

For the 0.1.6 prototype, this behavior can be demonstrated in the current ChatGPT play surface. Native clickable 3+1 controls belong to the future in-app API play loop and must not be claimed as already implemented in 0.1.6.

## 4:00–6:00 — Living world

Open the map:

- center on current position;
- search for a known place;
- toggle one or two useful layers;
- zoom enough to demonstrate detail/clustering;
- if useful, show an approximate location/uncertainty area.

Avoid spending time showing every map control.

## 6:00–7:30 — Visual continuity

Show one known subject with its persistent reference directly in the normal view.

Then open Media / visual continuity only if needed to show that:

- references are explicit bindings, not disposable chat images;
- a state variant can correspond to wounded/sick/fatigued/etc.;
- images preserve proportions and do not distort the UI;
- visual identity follows already-established canon.

## 7:30–10:00 — The continuity loop

Apply the prepared update.

Show that the Companion:

- validates campaign/revision/timeline;
- applies the update atomically;
- advances revision;
- refreshes the relevant player-facing surfaces.

Then return to the map or relevant entity and show the new/repositioned information.

This is the core proof: narrative output becomes controlled persistent world state.

## 10:00–11:30 — Recovery / trust

Show synchronization/integrity:

- timeline id;
- current revision;
- green integrity;
- backup action.

If time permits and the demonstration copy is prepared for it, restore a backup and show that the campaign remains coherent.

Do not attempt an unpracticed destructive restore during a pitch.

## 11:30–13:00 — Studio adaptation boundary

Explain in under 90 seconds:

- ChatGPT is the current prototype narrative authority;
- the Companion persistence model is not tied conceptually to ChatGPT;
- a studio can replace the narrative/runtime side with its own LLM stack, rules engine or game backend;
- the future target is to put the whole play surface inside the Companion via a controlled API adapter;
- the same canonical validation remains between model output and saved game state;
- the 3+1 suggestions are presentation data that a studio UI can render as quick actions without restricting free-form input.

Reference `ARCHITECTURE.md`, `STUDIO_ADAPTATION_GUIDE.md` and `API_INTEGRATION_TARGET.md` if technical follow-up is requested.

## Optional 13:00–15:00 — Questions / deeper proof

Only if useful:

- show PLAYER vs GM separation conceptually without exposing actual campaign secrets;
- show backup/integrity metadata;
- discuss no-schema extensible entity documents;
- discuss timeline rollback / stale update rejection;
- show route distance versus map presentation coordinates;
- explain that 0.1.5 and 0.1.6 deliberately share the same persistence schema/backup implementation, while final lived-save compatibility is still verified on a disposable real campaign copy.

## Claims that are safe for the 0.1.6 MVP

- persistent canonical campaign state outside one chat;
- backend-enforced PLAYER/GM separation;
- atomic revision/timeline-aware updates;
- technical backup/restore and integrity diagnostics;
- living player-knowledge map;
- persistent visual-reference continuity;
- guided 3+1 player choices in the current game contract, while preserving unrestricted free input;
- optional initial character anchor plus emergent character development in the current game contract;
- Windows desktop prototype;
- architecture designed so a future API runtime can replace manual exchange.

## Claims to avoid

Do not claim the MVP already has:

- integrated OpenAI/other API gameplay inside the app;
- native clickable 3+1 controls inside the Companion;
- production cloud sync;
- multiplayer concurrency;
- Unity/Unreal SDK;
- mobile/console clients;
- automatic music control;
- finished book export;
- finalized combat/progression/economy rules;
- automatic transport of all local image bytes into a new AI session.

## Demo failure fallback

If the network or external narrative service is unavailable, the demo should still work because the 0.1.6 proof uses a prepared update and local campaign state.

If an update fails validation, do not bypass the validator. Explain that refusing a stale/invalid mutation is part of the product value, then continue from the unchanged campaign state.

## Success criterion

A studio viewer should leave able to summarize Kitaba as:

**“A persistent continuity and world-state layer that makes an AI-assisted RPG behave like one evolving game rather than a sequence of disposable chats.”**
