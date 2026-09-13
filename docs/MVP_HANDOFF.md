# Kitaba MVP handoff

Persistent checkpoint for resuming development in a new chat/session.

## Product goal

The immediate goal is a **studio-presentable MVP**: a working Companion + continuity concept that can be demonstrated to game studios as an adaptable RPG/AI continuity layer. The prototype currently uses ChatGPT, but studio-facing material must distinguish the current implementation from the reusable concept.

Do not put confidential commercial strategy, pricing or negotiation material in this public repository.

## Stable user state

- Stable user version: 0.1.5 on `main`.
- Live campaign must remain compatible and must not be reset.
- Development branch must stay isolated until all release gates pass.

## Development branch

- Branch: `next-system-pass`
- Pull request: #2 — 0.1.6 MVP candidate.
- Status: DRAFT, not merged.
- SQLite schema remains v4; no destructive migration has been introduced for the 0.1.6 MVP.

## MVP scope implemented on branch

- Living interactive atlas: strict pan/zoom bounds, fullscreen synchronization, current-position focus, search, layers, zoom-dependent detail, clustering, routes/regions, explicit route distance and approximate-location uncertainty areas.
- Narrative pacing contract inherited from 0.1.5: shorter playable beats, concise enrichment of terse actions, player agency protected, world/NPC consequences remain authority-controlled.
- Visual continuity: persistent player-safe bindings, primary references, current-state variants, scene references, direct display in normal views, backup integration and centered non-stretched fixed-image slots.
- Visual-reference launcher moved from a global floating overlay trigger into the Media/continuity surface after client feedback so it no longer hides page content.
- Hidden progression/resolution, combat/resources, economy/travel, adaptive ambience and editorial story foundations remain tested **PROPOSAL** material rather than promoted canon.
- Studio adaptation boundary documented in `docs/ARCHITECTURE.md` and `docs/STUDIO_ADAPTATION_GUIDE.md`.

## Latest validated Windows state before studio-document pass

Client-smoke correction HEAD `3e51dc4fcff402bbbff560d4b3244aa2ad65b18a` passed Windows workflow run #175 (`34764023146`) completely:

- Python reference suite: success;
- reproducible frontend install/build: success;
- Rust tests/checks: success;
- Tauri/NSIS build: success;
- Windows GUI-subsystem verification: success;
- artifact upload: success.

Artifact: `kitaba-companion-windows-0.1.6`, GitHub SHA-256 `e1624e5a3a003126759a8f8ab28d419b8f74e3e209e9c2f665b90802eae53c46`.

After any subsequent documentation/code commit, re-check the newest PR-head workflow rather than treating this historical run as the final HEAD validation.

## Human feedback already received

- 0.1.6 launched with the existing campaign visible and integrity diagnostic green in the supplied client screenshot.
- User reported no other obvious visual anomalies beyond the floating `Références visuelles` launcher.
- The launcher obstruction was corrected; user then confirmed the result was satisfactory and authorized continuing toward MVP.

Do **not** over-interpret this as proof of every migration gate. A deliberate backup/restore visual-binding cycle and update-driven map discovery still require explicit end-to-end proof before merge if not already exercised on a disposable copy.

## Remaining release gates before merge

1. Latest PR-head Windows pipeline fully green after the final release-document/code pass.
2. Final artifact/version metadata verified for that HEAD if code/build identity changes.
3. Confirm upgrade/restore compatibility on a **copy** of a real 0.1.5 `.kitaba` backup; never use the live save as the first migration test.
4. Complete the human cycle visual binding → technical backup → restore → integrity on the migration copy.
5. Exercise an update that reveals/repositions a place and confirm map/search/current-location behavior.
6. Human-check strict map edges at several zoom levels/fullscreen if not already explicitly exercised.
7. Only then mark the PR ready/merge to `main` and prepare migration/release instructions.

## Studio-facing release discipline

- The MVP should prove persistence/continuity, not claim a finished game engine.
- ChatGPT is the prototype authority; alternative model/rules/runtime integrations are architectural adaptation paths, not already-shipping integrations.
- Avoid promising cloud scale, multiplayer, Unity/Unreal SDKs, automatic music, finished story-book export or finalized PROPOSAL mechanics.
- The 10–15 minute pitch flow should prove: lived campaign → character/relation/visual continuity → living map → update changes the world → integrity/recoverability → explain adaptation boundary.
- Before external outreach, separately decide repository visibility/licensing and commercial materials; do not mix those choices into the functional MVP freeze.

## Next work priority

- Finish current final-head CI and release hardening.
- Keep feature scope frozen: regressions/documentation only.
- Close remaining migration-copy smoke gates.
- Prepare a clean studio demo package and patch-note summary only after the candidate is technically frozen.
- Do not promote PROPOSAL mechanics or rewrite Project Sources until the user explicitly chooses the next MASTER/source-update phase.