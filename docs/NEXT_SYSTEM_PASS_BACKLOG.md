# Kitaba — 0.1.6 MVP system pass backlog

Status: working backlog for the post-0.1.5 development branch. The branch is intentionally isolated from stable `main` and must never mutate the user's live campaign by itself.

## P0 — release correctness / continuity

- [x] Reserve a new application/release version (`0.1.6`) instead of reusing stable `0.1.5` for a materially different build.
- [x] Version package metadata, Tauri/NSIS metadata, Rust package metadata and Windows artifact naming as `0.1.6`.
- [x] Align `package-lock.json` and `src-tauri/Cargo.lock` package metadata with the same `0.1.6` release identity and add regression coverage so version drift fails CI.
- [x] Define the shared MVP theme tokens used by atlas/media surfaces instead of leaving CSS custom properties unresolved.
- [x] Clamp interactive world-map pan so the image cannot be dragged beyond world bounds.
- [x] Recompute bounds after zoom, resize and fullscreen changes.
- [x] Keep map markers aligned with the actually rendered image area.
- [x] Highlight the current linked settlement/place when coordinates exist.
- [x] Add regression coverage for map boundary behavior.
- [x] Obtain at least one fully green Windows build of the feature branch before release hardening.
- [x] Obtain a fully green Windows build after the final 0.1.6 code correction: run #175 / `34764023146` at `3e51dc4fcff402bbbff560d4b3244aa2ad65b18a`.
- [x] Verify the corrected artifact name and installer product version are 0.1.6; artifact `kitaba-companion-windows-0.1.6`, GitHub digest `e1624e5a3a003126759a8f8ab28d419b8f74e3e209e9c2f665b90802eae53c46`.
- [ ] Re-check newest PR-head CI after final documentation/freeze commits; documentation-only commits do not invalidate the last built binary, but merge still requires a green current HEAD.
- [ ] Verify upgrade/restore compatibility on a COPY of a real 0.1.5 `.kitaba` backup; never use the live save as the first migration test.
- [ ] Human smoke-test strict map edges at several zoom levels and fullscreen so no black background can be exposed.
- [ ] Human smoke-test visual binding → backup → restore → integrity on the migration copy.
- [x] Client evidence: oversized protagonist portrait is no longer visibly stretched in the observed 0.1.6 surface; automated image-fit regression remains active.
- [x] Client evidence: global floating `Références visuelles` launcher was identified, moved into Media/continuity, rebuilt green, and user confirmed the correction was satisfactory.
- [ ] Human smoke-test an update that reveals/repositions a place and confirm map/search/current-location behavior.

## P1 — core game mechanics

- [x] Draft a calibrated hidden progression model with nonlinear mastery thresholds and anti-farming.
- [x] Draft a single hidden uncertainty-resolution scale shared by exploration, social and skill actions.
- [x] Check common d100 outcome bands with exhaustive 1–100 distribution tests.
- [x] Check baseline learning pace against demanding, severe, teacher-assisted and repeated-identical practice scenarios.
- [x] Keep player-facing progression qualitative while internal points remain hidden.
- [x] Draft damage, protection, HP and per-impact injury severity on the same non-level-scaled foundation.
- [x] Draft mana-cost bands and explicit overchannel deficit severity through strain, injury, coma and death risk.
- [x] Calibrate representative weak/equal/strong resolution targets and multiple armor/protection profiles.
- [x] Draft safe-rest HP recovery separated from persistent injuries, with injury severity slowing recovery.
- [ ] Define long-term characteristic/capacity growth separately from skill mastery; the current leveling candidate is intentionally skill-centric.
- [ ] Calibrate stabilization, bleeding/critical-state handling and recovery against travel/camp conditions.
- [ ] Validate surrender/flee/disengage and non-lethal combat outcomes before promoting combat mechanics.
- [ ] Promote only validated portions into the next MASTER SOURCE / MJ contract after explicit user acceptance.

## P1 — interactive fiction quality

Already carried by the 0.1.5 contract and still under live playtest:

- shorter playable beats rather than passive text walls;
- enrich terse player actions with concise gestures/sensory/emotional detail without changing intent;
- player-declared outcomes remain attempts when uncertain;
- player controls protagonist actions, not NPC reactions or world results;
- deeper description on inspection, major reveals and emotionally important beats rather than every turn.

Additional MVP work:

- [x] Add explicit pacing profiles for exploration, dialogue, tension/combat and emotional scenes.
- [x] Define chapter/scene editorial capture for future readable story export without storing a verbatim chat transcript as canon.
- [ ] Keep collecting live-player feedback before freezing the next MJ contract; no pacing rule is promoted merely because it exists in code/docs.

## P1 — visual continuity / illustration

- [x] Define a stable `visual_identity` record linked to each important PC/NPC/place without requiring a schema migration.
- [x] Define a no-schema reference-image binding model using existing assets.
- [x] Define state variants for the same character: normal, wounded, sick, exhausted, ceremonial, heroic, deceased where appropriate.
- [x] Define multi-character scene reference sets so known characters remain visually consistent in group illustrations.
- [x] Define a campaign-level art-direction profile for a coherent fantasy-anime/isekaï visual language without copying a specific copyrighted production.
- [x] Define an illustration priority policy for home, starting settlement, close relations and major locations/scenes.
- [x] Implement backup-safe Companion backend for binding local image assets to visible campaign subjects without schema migration.
- [x] Add MVP binding UI: associate imported portraits/illustrations with a known player-facing character/place, role and visual state; edit/remove association without deleting the image.
- [x] Surface the primary visual reference and current-state variant directly in normal PC/NPC/place views so the player does not have to open a separate reference tool.
- [x] Center and crop fixed portrait/reference slots with `object-fit: cover` so oversized images never stretch; keep full previews/map imagery on `contain`.
- [x] Invalidate/reload inline visual references when the active campaign changes so a shared entity id cannot display an image from the previous campaign.
- [x] Preserve the canon-before-image rule in the new visual-reference dock, including during campaign switching/loading.
- [x] Move the visual-reference launcher out of the global floating layer and into the Media/continuity page after client-smoke feedback.
- [ ] Smoke-test a close NPC with primary portrait + wounded/sick variant + shared scene reference through backup/restore.

## P1 — living atlas

- [x] Normalized x/y world-map markers supported by Companion.
- [x] Strict pan/zoom world bounds with no exposed black border in the implementation.
- [x] Current-location focus button when a positioned current marker exists.
- [x] Search and recenter on known positioned places.
- [x] Filterable map layers for places, regions, routes, dungeons and other geography.
- [x] Multi-scale detail: less-important labels/markers appear only as the player zooms in.
- [x] Nearby markers automatically cluster and split when zooming in.
- [x] Player/MJ layer separation remains enforced by the existing PLAYER/GM entity boundary.
- [x] Geography-placement contract: biome, climate, rivers, terrain, economy and known demographics constrain new settlements before coordinates are persisted.
- [x] Region/state polygons and route paths supported as scalable map overlays in addition to point markers.
- [x] Formal discovery states: unknown location, approximate location, exact location, rumor/known/visited/current.
- [x] Render a true uncertainty area when a location is only broadly known, instead of implying a precise point.
- [x] Define/validate an explicit route-distance field for travel calculations; normalized x/y are presentation coordinates and must not silently become kilometers.

## P1 — adaptive ambience

- [x] Define stable scene-level `music_state` categories and transition semantics.
- [x] Add executable anti-churn transition logic so ambience does not change every message.
- [x] Allow immediate transition for real scene changes/large tonal jumps while requiring confirmation for small fluctuations.
- [ ] Validate the actual playback/control surface before promising automatic music switching.
- [x] Keep adaptive music explicitly prototype/post-MVP for 0.1.6 until a real playback/control surface is validated; Companion-native playback remains a fallback design, not a silently substituted feature.

## P1 — book/story foundation

- [x] Separate canonical memory, functional player journal and editorial prose conceptually.
- [x] Define traceable editorial scene captures anchored to canonical source events/revisions.
- [x] Define meaningful scene boundaries instead of splitting by message count.
- [x] Define safe editorial merging rules that never rewrite canon.
- [x] Implement and test a safe reference HTML renderer with optional scene illustrations.
- [ ] Persist editorial scene captures in Companion without bloating authority context. Explicitly deferred post-MVP 0.1.6 by `MVP_0.1.6_SCOPE_FREEZE.md`.
- [x] Decide the first HTML `Exporter mon histoire` action is post-MVP 0.1.6 rather than introducing a new persistence/asset surface during release hardening.

## P1 — economy / travel candidate

- [x] Draft internally consistent value-unit anchors for wages, meals, lodging, mundane equipment and transport without prematurely locking a public currency name.
- [x] Draft travel pace from explicit route distance + terrain/weather/pace, with bounded danger-check pressure.
- [x] Keep normalized map coordinates independent from physical distance.
- [ ] Stress-test price anchors against adventurer/guild rewards and dungeon/monster trade before canon promotion.
- [ ] Add camp, food/water, exhaustion and weather consequences to the recovery/travel calibration.

## P1 — MVP presentation / studio readiness

- [x] Define a 10–15 minute presentation flow.
- [x] Prove the branch can pass the full Windows pipeline before final freeze.
- [x] Freeze presentation scope: direct linked illustrations are in 0.1.6; HTML story export, live API gameplay and automatic music playback are explicitly post-MVP until their persistence/control surfaces are proven.
- [x] Document studio adaptation boundary so ChatGPT-specific prototype choices are not confused with product invariants.
- [x] Document future in-app API target while preserving canonical validation as a separate authority boundary.
- [x] Add deterministic studio demo runbook.
- [ ] Complete the remaining P0 release gates on a real-save COPY.
- [ ] Run the MVP demonstration checklist end-to-end on a migration/demo copy of an existing campaign.
- [ ] Freeze and merge only after all required presentation gates are green.

## P2 — post-MVP productization

- [ ] Build a provider-neutral `NarrativeRuntimeAdapter` and one real API implementation inside the Companion.
- [ ] Add secure credential storage outside campaign backups/contexts/logs.
- [ ] Add in-app player conversation/streaming surface.
- [ ] Project only causal/relevant context to the narrative runtime instead of sending the full database each turn.
- [ ] Keep model prose separate from structured canonical update proposals and validate all proposed mutations before commit.
- [ ] Add robust retry/idempotency/failure behavior so a network/model failure never advances canon.
- [ ] Equipment/crafting: quality, durability, repair, materials and encumbrance without inventory micromanagement overload.
- [ ] Relationship/reputation evolution: local memory, rumor spread, favors, debts, fear, trust and conflicting dimensions.
- [ ] Broader world-economy stress tests and regional price variation.
- [ ] Physical-world scale model if long-distance travel eventually needs coordinate-derived distances rather than explicit route distances.
- [ ] PDF/EPUB export after the HTML book pipeline is proven.

## Release rule

No item moves to stable merely because it exists on this branch. Before release: version separation → automated tests → Windows build → artifact/version verification → migration-copy compatibility → human map/visual/update smoke tests → integrity check → then merge/freeze and user migration instructions. The existing live campaign remains the compatibility priority.
