# Kitaba Companion 0.1.6 — release / migration plan

Status: **DRAFT / release gate**. Nothing in this document authorizes installation on the live campaign yet.

## Why 0.1.6

The MVP pass is materially different from stable 0.1.5, so it must ship under a new application version. Reusing 0.1.5 would make installer provenance, bug reports, rollback and support ambiguous.

## Live-campaign rule

The user's current ongoing campaign is never used as the first migration target. The first validation uses a COPY restored from a known-good 0.1.5 `.kitaba` backup. Only after that copy passes revision/timeline checks, integrity, map, visual-reference and update smoke tests may the live installation be upgraded.

No release may require recreating the character or restarting the campaign.

## Current live play stack

While 0.1.6 remains a development candidate, the user's real campaign continues on:

1. **Kitaba Companion 0.1.5**;
2. **`KITABA_MASTER_PROJECT_SOURCE_v1.4.4_FINAL.md`** as the single active MASTER SOURCE;
3. the canonical project map image.

The cumulative Source patches already accepted for live play are:

- 1.4.1 — optional initial character anchor + emergent protagonist nature;
- 1.4.2 — default 3+1 guided-choice presentation while preserving unrestricted free input;
- 1.4.3 — future API integration is allowed/targeted; only a paid API forced as the sole play path remains rejected;
- 1.4.4 — clarification that ChatGPT is the **current** narrative runtime, while a future in-app runtime/API may occupy that role without merging narrative authority into the persistence core.

These Source updates do not require a Companion upgrade and do not rewrite an existing campaign's frozen Genesis or established dynamic canon.

Development drafts, installers, release ZIPs, migration guides, LIVE_PATCH files and campaign GM_FULL exports are never Project Sources.

## Content-contract deliverables before 0.1.6 migration

The application build alone is not enough. Before telling the user to migrate, prepare and verify:

- a next MASTER SOURCE revision only for rules that have actually been accepted/promoted from PROPOSAL;
- any necessary live-chat instruction/update so the current campaign can adopt non-Genesis interaction/persistence contracts without restarting the save;
- an updated fresh-campaign game prompt for future campaigns if the Companion/API flow changes;
- a concise migration guide explaining backup → install-in-place → same campaign → integrity → fresh GM_FULL → same game chat;
- release metadata/checksums matching the exact production artifact.

The ongoing campaign keeps its immutable frozen Genesis. A new MASTER must not silently rewrite that snapshot or retroactively change established facts.

## Mechanical promotion rule

Progression/resolution, combat/mana/recovery, economy/travel and any other numerical draft remain **PROPOSAL** until explicitly promoted. A 0.1.6 Companion build may contain reference/test code for them without making those numbers campaign canon.

If a subsystem is not promoted by release freeze, documentation must clearly mark it post-MVP/PROPOSAL rather than implying the live campaign already uses it.

## Required migration-copy smoke test

On the restored copy of the real 0.1.5 backup:

1. open the same campaign and confirm campaign/timeline/revision;
2. run integrity and require every check green;
3. verify existing map, portrait and campaign images;
4. test map zoom/pan at several zoom levels and fullscreen, forcing every edge/corner; no black background may be exposed;
5. verify current-position focus, search, filters and clustering;
6. bind an imported image to a known PLAYER subject, create a variant, back up, restore, and verify the binding survives with integrity green;
7. import a safe test update on the copy that adds/repositions a known location and verify the atlas updates correctly;
8. export a fresh GM_FULL and verify revision/timeline continuity and no PLAYER/GM leak;
9. close/reopen the app and repeat integrity + spot checks.

Only then can the live-save migration instructions be issued.

## Release artifact gates

- Python reference tests green;
- frontend TypeScript/Vite build green;
- Rust tests green;
- Tauri/NSIS build green;
- PE GUI subsystem check green;
- artifact upload green;
- installer/application/artifact all identify 0.1.6;
- production `main` build green after merge;
- hashes recorded after the production build, never copied from an earlier candidate.

## Music and story export honesty gate

Adaptive music is not advertised as automatically controlled by the narrative runtime until the actual playback/control surface is verified end-to-end. If reliable control is unavailable, it remains a prototype/post-MVP capability.

Likewise, the editorial HTML renderer foundation is not advertised as an in-app `Exporter mon histoire` feature until the Companion actually exposes and persists the required editorial scenes.
