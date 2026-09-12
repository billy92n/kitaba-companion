# Kitaba — 0.1.6 MVP system pass backlog

Status: working backlog for the post-0.1.5 development branch. The branch is intentionally isolated from stable `main` and must never mutate the user's live campaign by itself.

## P0 — release correctness / continuity

- [x] Reserve a new application/release version (`0.1.6`) instead of reusing stable `0.1.5` for a materially different build.
- [x] Version package metadata, Tauri/NSIS metadata, Rust package metadata and Windows artifact naming as `0.1.6`.
- [x] Clamp interactive world-map pan so the image cannot be dragged beyond world bounds.
- [x] Recompute bounds after zoom, resize and fullscreen changes.
- [x] Keep map markers aligned with the actually rendered image area.
- [x] Highlight the current linked settlement/place when coordinates exist.
- [x] Add regression coverage for map boundary behavior.
- [x] Obtain at least one fully green Windows build of the feature branch before release hardening.
- [ ] Obtain a fully green Windows build after the final 0.1.6 version/freeze changes.
- [ ] Verify the final artifact name and installer product version are 0.1.6.
- [ ] Verify upgrade/restore compatibility on a COPY of a real 0.1.5 `.kitaba` backup; never use the live save as the first migration test.
- [ ] Human smoke-test strict map edges at several zoom levels and fullscreen so no black background can be exposed.
- [ ] Human smoke-test visual binding → backup → restore → integrity on the migration copy.
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
- [ ] Surface the primary visual reference and current-state variant directly in normal PC/NPC/place views so the player does not have to open a separate reference tool.
- [ ] Smoke-test a close NPC with primary portrait + wounded/sick variant + shared scene reference.

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
- [ ] Render a true uncertainty area when a location is only broadly known, instead of implying a precise point.
- [ ] Define/validate an explicit route-distance field for travel calculations; normalized x/y are presentation coordinates and must not silently become kilometers.

## P1 — adaptive ambience

- [x] Define stable scene-level `music_state` categories and transition semantics.
- [x] Add executable anti-churn transition logic so ambience does not change every message.
- [x] Allow immediate transition for real scene changes/large tonal jumps while requiring confirmation for small fluctuations.
- [ ] Validate the actual ChatGPT playback/control surface before promising automatic music switching.
- [ ] If direct ChatGPT control cannot be made reliable, keep adaptive music labeled prototype/post-MVP rather than faking automation; Companion-native playback remains a fallback design, not a silently substituted feature.

## P1 — book/story foundation

- [x] Separate canonical memory, functional player journal and editorial prose conceptually.
- [x] Define traceable editorial scene captures anchored to canonical source events/revisions.
- [x] Define meaningful scene boundaries instead of splitting by message count.
- [x] Define safe editorial merging rules that never rewrite canon.
- [x] Implement and test a safe reference HTML renderer with optional scene illustrations.
- [ ] Persist editorial scene captures in Companion without bloating MJ context.
- [ ] Connect a first HTML `Exporter mon histoire` action to Companion and campaign assets, or explicitly mark this as post-MVP before presentation freeze.

## P1 — economy / travel candidate

- [x] Draft internally consistent value-unit anchors for wages, meals, lodging, mundane equipment and transport without prematurely locking a public currency name.
- [x] Draft travel pace from explicit route distance + terrain/weather/pace, with bounded danger-check pressure.
- [x] Keep normalized map coordinates independent from physical distance.
- [ ] Stress-test price anchors against adventurer/guild rewards and dungeon/monster trade before canon promotion.
- [ ] Add camp, food/water, exhaustion and weather consequences to the recovery/travel calibration.

## P1 — MVP presentation

- [x] Define a 10–15 minute presentation flow.
- [x] Prove the branch can pass the full Windows pipeline before final freeze.
- [ ] Complete the remaining P0 release gates on a real-save COPY.
- [ ] Decide whether direct linked illustrations and basic HTML story export are in the presentation slice or explicitly post-MVP; do not leave either in an ambiguous half-shipped state.
- [ ] Run the MVP demonstration checklist end-to-end on a migration copy of an existing campaign.
- [ ] Freeze and merge only after all required presentation gates are green.

## P2 — deeper simulation after the MVP gate

- [ ] Equipment/crafting: quality, durability, repair, materials and encumbrance without inventory micromanagement overload.
- [ ] Relationship/reputation evolution: local memory, rumor spread, favors, debts, fear, trust and conflicting dimensions.
- [ ] Broader world-economy stress tests and regional price variation.
- [ ] Physical-world scale model if long-distance travel eventually needs coordinate-derived distances rather than explicit route distances.
- [ ] PDF/EPUB export after the HTML book pipeline is proven.

## Release rule

No item moves to stable merely because it exists on this branch. Before release: version separation → automated tests → Windows build → artifact/version verification → migration-copy compatibility → human map/visual/update smoke tests → integrity check → then merge/freeze and user migration instructions. The existing live campaign remains the compatibility priority.
