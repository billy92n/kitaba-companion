# Kitaba Companion 0.1.6 — release / migration plan

Status: **DRAFT / release gate**. Nothing in this document authorizes installation on the live campaign yet.

## Why 0.1.6

The MVP pass is materially different from stable 0.1.5, so it must ship under a new application version. Reusing 0.1.5 would make installer provenance, bug reports, rollback and support ambiguous.

## Live-campaign rule

`Kitaba Solo - Test 1` / the ongoing `Kitaba première partie` campaign is never used as the first migration target. The first validation uses a COPY restored from the known-good 0.1.5 `.kitaba` backup. Only after that copy passes revision/timeline checks, integrity, map, visual-reference and update smoke tests may the live installation be upgraded.

No release may require recreating the character or restarting the campaign.

## Project Sources

Until the 0.1.6 content contract is intentionally frozen, the user's current project Sources remain exactly:

1. `KITABA_MASTER_PROJECT_SOURCE_v1.4_FINAL.md`
2. `Carte fantasy panoramique sans légendes.png`

Development drafts, installers, release ZIPs, migration guides, LIVE_PATCH files and campaign GM_FULL exports are never added to Project Sources.

## Content-contract deliverables before 0.1.6 migration

The application build alone is not enough. Before telling the user to migrate, prepare and verify:

- a next MASTER SOURCE revision only for rules that have actually been accepted/promoted from PROPOSAL;
- a LIVE_PATCH for the existing game chat so interaction/pacing/new persistence contracts can be adopted without restarting the save;
- an updated fresh-campaign game prompt for future campaigns;
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

Adaptive music is not advertised as automatically controlled by ChatGPT until the actual playback/control surface is verified end-to-end. If reliable control is unavailable, it remains a prototype/post-MVP capability.

Likewise, the editorial HTML renderer foundation is not advertised as an in-app `Exporter mon histoire` feature until the Companion actually exposes and persists the required editorial scenes.
