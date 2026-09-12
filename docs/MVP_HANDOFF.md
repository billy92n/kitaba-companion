# Kitaba MVP handoff

Persistent checkpoint for resuming development in a new chat/session.

## Stable user state

- Stable user version: 0.1.5 on `main`.
- Live campaign must remain compatible and must not be reset.
- Development branch must stay isolated until all release gates pass.

## Development branch

- Branch: `next-system-pass`
- Pull request: #2 — `MVP system pass: living atlas + mechanics + ambience/story foundations`
- Status: DRAFT, not merged.

## MVP scope already implemented or drafted on branch

- Living interactive atlas: strict pan/zoom bounds, no exposed black border, current-position focus, search, layers, zoom-dependent detail, clustering, routes and region polygons, approximate/unknown positioning states.
- Narrative pacing contract: shorter playable beats, concise enrichment of terse player actions, player controls protagonist only, NPC/world reactions remain MJ-controlled.
- Visual continuity foundations: stable visual identity, reference images, state variants, multi-character scene references, campaign art direction.
- Hidden progression and unified uncertainty-resolution candidate models with tests.
- Combat/injury/protection, mana/overchanneling and persistent injury recovery candidate models. These remain PROPOSAL until deliberately promoted to the MASTER/MJ contract.
- Adaptive ambience state model with anti-churn transition semantics.
- Editorial story-scene and HTML export foundations, traceable to canon but not themselves canon.
- Structured MVP backlog in `docs/NEXT_SYSTEM_PASS_BACKLOG.md`.

## CI state at handoff

- An earlier candidate failed one story-export regression assertion because the test matched the CSS class name rather than an actual `<img>` tag.
- The regression test was corrected in commit `e0f2dbd80507a73394e5227a8579e629e25d9076`.
- Subsequent branch work continued through combat/recovery and MVP parity tests.
- Latest known branch head before this handoff file: `aafc6782cb48f8f1805c2afa55fe5a1b8e43b22a`.
- Latest known Windows validation run at the time of writing: run #115 (`34722636310`), still in progress when last checked. Re-check the newest PR-head workflow run before any merge.

## Release gates before merge

1. Latest Windows pipeline fully green: Python reference tests, frontend build/type checks, Rust tests/checks, Tauri NSIS build, PE GUI check, artifact upload.
2. Inspect any failed run logs and fix the actual cause; do not treat historical failed runs as current release failures.
3. Verify upgrade compatibility against a real 0.1.5 `.kitaba` backup and run integrity checks after restore/open.
4. Run the 10–15 minute MVP demonstration checklist end-to-end on a campaign copy.
5. Only then promote validated mechanics into the next MASTER/MJ contract and merge PR #2.
6. Do not expose hidden GM-only aptitude details in player-facing material.

## Next work priority

- Finish/verify current CI.
- Complete combat/recovery calibration and MVP parity coverage.
- Implement the first useful visual-identity asset binding UI without destructive schema changes.
- Add persistent editorial scene capture and first usable story export path.
- Validate dense-map behavior with many markers/routes/regions.
- Prepare a presentation candidate only after live-save compatibility is proven.

This file exists so a future chat can resume by inspecting PR #2, `docs/NEXT_SYSTEM_PASS_BACKLOG.md`, this handoff, and the latest GitHub Actions run, without relying on conversational memory.
