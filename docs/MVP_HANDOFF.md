# Kitaba MVP handoff

Persistent checkpoint for resuming development in a new chat/session.

## Product goal

The immediate goal is a **studio-presentable MVP**: a working Companion + continuity concept that can be demonstrated to game studios as an adaptable RPG/AI continuity layer. The prototype currently uses ChatGPT, but studio-facing material must distinguish the current implementation from the reusable concept.

Do not put confidential commercial strategy, pricing or negotiation material in this public repository.

## Stable user state

- Stable user version: **0.1.5** on `main`.
- Active Project Source for live play: **`KITABA_MASTER_PROJECT_SOURCE_v1.4.4_FINAL.md`** plus the canonical map image.
- Live campaign must remain compatible and must not be reset.
- Development branch must stay isolated until all release gates pass.
- Source 1.4.4 already carries accepted live-play clarifications: emergent protagonist nature, 3+1 guided freedom, and future in-app API/runtime direction. These do not require a Companion upgrade.

## Development branch

- Branch: `next-system-pass`
- Pull request: #2 — 0.1.6 MVP candidate.
- Status: DRAFT, not merged.
- SQLite schema remains v4; no destructive migration has been introduced for the 0.1.6 MVP.

## MVP scope implemented on branch

- Living interactive atlas: strict pan/zoom bounds, fullscreen synchronization, current-position focus, search, layers, zoom-dependent detail, clustering, routes/regions, explicit route distance and approximate-location uncertainty areas.
- Narrative pacing contract inherited from live Sources: shorter playable beats, concise enrichment of terse actions, player agency protected, world/NPC consequences remain authority-controlled.
- Product/gameplay direction documents now also reflect **3+1 guided freedom** and the distinction between optional initial character anchor, emergent nature and public reputation without pretending those are native clickable Companion controls in 0.1.6.
- Visual continuity: persistent player-safe bindings, primary references, current-state variants, scene references, direct display in normal views, backup integration and centered non-stretched fixed-image slots.
- Visual-reference launcher moved from a global floating overlay trigger into the Media/continuity surface after client feedback so it no longer hides page content.
- Hidden progression/resolution, combat/resources, economy/travel, adaptive ambience and editorial story foundations remain tested **PROPOSAL** material rather than promoted canon.
- Studio adaptation boundary documented in `docs/ARCHITECTURE.md`, `docs/STUDIO_ADAPTATION_GUIDE.md` and `docs/API_INTEGRATION_TARGET.md`.

## Compatibility evidence

The stable 0.1.5 `main` and the 0.1.6 branch currently share the exact same `src-tauri/src/db.rs` Git blob:

`e1198993619865a5a38af5acf22a9ab9c1d0f20f`

Therefore the v4 migration set, technical backup/restore path and integrity implementation are unchanged between the two candidates at freeze. CI now additionally rejects an unexpected migration beyond `0004`.

A Rust compatibility regression test also exercises a legacy-style campaign that has **no `visual-bindings.json`** (matching a normal 0.1.5 campaign), backs it up, restores it into fresh storage, requires an empty visual-binding list rather than an error, and requires campaign integrity to remain green.

This materially reduces upgrade uncertainty but does not replace the final real-Windows/save-copy smoke test.

## Human feedback already received

- 0.1.6 launched with an existing campaign visible and integrity diagnostic green in the supplied client screenshot.
- User reported no other obvious visual anomalies beyond the floating `Références visuelles` launcher.
- The launcher obstruction was corrected; user then confirmed the result was satisfactory and authorized continuing toward MVP.

Do **not** over-interpret this as proof of every migration gate. A deliberate backup/restore visual-binding cycle and update-driven map discovery still require explicit end-to-end proof before merge if not already exercised on a disposable copy.

## Remaining release gates before merge

1. Latest PR-head Windows pipeline fully green after the final release-hardening pass.
2. Final artifact/version metadata verified for that HEAD if code/build identity changes.
3. Confirm upgrade/restore compatibility on a **copy** of a real 0.1.5 `.kitaba` backup; never use the live save as the first migration test.
4. Complete the human cycle visual binding → technical backup → restore → integrity on the migration copy.
5. Exercise an update that reveals/repositions a place and confirm map/search/current-location behavior.
6. Human-check strict map edges at several zoom levels/fullscreen if not already explicitly exercised.
7. Only then mark the PR ready/merge to `main` and prepare migration/release instructions.

## Studio-facing release discipline

- The MVP should prove persistence/continuity, not claim a finished game engine.
- ChatGPT is the current prototype runtime; alternative model/rules/runtime integrations are architectural adaptation paths, not already-shipping integrations.
- The persistence core never becomes an uncontrolled narrator: a future in-app runtime/API proposes prose/choices/mutations and the canonical gate still validates writes.
- Avoid promising cloud scale, multiplayer, Unity/Unreal SDKs, automatic music, finished story-book export or finalized PROPOSAL mechanics.
- The 10–15 minute pitch flow should prove: lived campaign → guided freedom/character continuity → relation/visual continuity → living map → update changes the world → integrity/recoverability → explain adaptation boundary.
- Before external outreach, separately decide repository visibility/licensing and commercial materials; do not mix those choices into the functional MVP freeze.

## Next work priority

- Finish current final-head CI and release hardening.
- Keep feature scope frozen: regressions/documentation only.
- Close remaining migration-copy smoke gates only when the user is ready for the 0.1.6 upgrade test; do not interrupt current 0.1.5 play unnecessarily.
- Prepare a clean studio demo package and patch-note summary only after the candidate is technically frozen.
- Do not promote PROPOSAL mechanics unless explicitly accepted into a future MASTER/source revision.
