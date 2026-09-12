# Kitaba — next system pass backlog

Status: working backlog for the post-0.1.5 development branch. It must not mutate a live campaign by itself.

## P0 — correctness / continuity

- [x] Clamp interactive world-map pan so the image cannot be dragged beyond world bounds.
- [x] Recompute bounds after zoom, resize and fullscreen changes.
- [x] Keep map markers aligned with the actually rendered image area.
- [x] Highlight the current linked settlement/place when coordinates exist.
- [x] Add regression coverage for map boundary behavior.
- [ ] Validate the final dense-map implementation in a Windows build before merging to `main`.

## P1 — core game mechanics

- [x] Draft a calibrated hidden progression model with nonlinear mastery thresholds and anti-farming.
- [x] Draft a single hidden uncertainty-resolution scale shared by exploration, social and skill actions.
- [x] Check common d100 outcome bands with exhaustive 1–100 distribution tests.
- [x] Check baseline learning pace against demanding, severe, teacher-assisted and repeated-identical practice scenarios.
- [x] Keep player-facing progression qualitative while internal points remain hidden.
- [x] Draft damage, protection, HP and per-impact injury severity on the same non-level-scaled foundation.
- [x] Draft mana-cost bands and explicit overchannel deficit severity through strain, injury, coma and death risk.
- [ ] Calibrate combat against representative weak/equal/strong opponents and different armor profiles.
- [ ] Calibrate recovery/stabilization with the future rest/travel model.
- [ ] Promote only the validated portions into the next MASTER SOURCE / MJ contract after user acceptance.

## P1 — interactive fiction quality

Already carried by 0.1.5 contract and still under playtest:

- shorter playable beats rather than passive text walls;
- enrich terse player actions with concise gestures/sensory/emotional detail without changing intent;
- player-declared outcomes remain attempts when uncertain;
- player controls protagonist actions, not NPC reactions or world results;
- deeper description on inspection, major reveals and emotionally important beats rather than every turn.

Next work:

- [x] Add explicit pacing profiles for exploration, dialogue, tension/combat and emotional scenes.
- [x] Define chapter/scene editorial capture for future readable story export without storing a verbatim chat transcript as canon.

## P1 — visual continuity

- [x] Define a stable `visual_identity` record linked to each important PC/NPC/place without requiring a schema migration.
- [x] Define a no-schema reference-image binding model using existing generic entities/assets.
- [x] Define state variants for the same character: normal, wounded, sick, exhausted, ceremonial, heroic, deceased where appropriate.
- [x] Define multi-character scene reference sets so known characters remain visually consistent in group illustrations.
- [x] Define a campaign-level art-direction profile for consistent fantasy-anime/isekai visual language without copying a specific copyrighted production.
- [x] Define an illustration priority policy for home, starting settlement, close relations and major locations/scenes.
- [ ] Implement Companion UI for binding imported local assets to visual identities.
- [ ] Show primary visual references/variants directly on linked character and place views.

## P1 — living atlas

- [x] Normalized x/y world-map markers supported by Companion.
- [x] Strict pan/zoom world bounds with no exposed black border.
- [x] Current-location focus button when a positioned current marker exists.
- [x] Search and recenter on known positioned places.
- [x] Filterable map layers for places, regions, routes, dungeons and other geography.
- [x] Multi-scale detail: less-important labels/markers appear only as the player zooms in.
- [x] Nearby markers automatically cluster and split when zooming in.
- [x] Player/MJ layer separation remains enforced by the existing PLAYER/GM entity boundary.
- [x] Geography-placement contract: biome, climate, rivers, terrain, economy and known demographics constrain new settlements before coordinates are persisted.
- [x] Region/state polygons and route paths supported as scalable map overlays in addition to point markers.
- [x] Formal discovery states defined: unknown location, approximate location, exact location, rumor/known/visited/current.
- [ ] Add optional approximate-area rendering rather than a dashed point when the known position is genuinely broad.

## P1 — adaptive ambience

- [x] Define stable scene-level `music_state` categories and transition semantics.
- [x] Add executable anti-churn transition logic so ambience does not change every message.
- [x] Allow immediate transition for real scene changes or large tonal jumps while requiring confirmation for small fluctuations.
- [ ] Connect the state contract to a real playback path after validating the available ChatGPT/Companion integration surface.

## P1 — book/story foundation

- [x] Separate canonical memory, functional player journal and editorial prose conceptually.
- [x] Define traceable editorial scene captures anchored to canonical source events/revisions.
- [x] Define meaningful scene boundaries instead of splitting by message count.
- [x] Define safe editorial merging rules that never rewrite canon.
- [ ] Persist editorial scene captures in Companion without bloating MJ context.
- [ ] Implement first readable HTML campaign export.

## P1 — MVP presentation

- [x] Define a presentation scope and 10–15 minute demonstration flow.
- [ ] Produce a green Windows candidate build from the final MVP branch state.
- [ ] Verify upgrade compatibility against a real 0.1.5 `.kitaba` backup.
- [ ] Run the MVP demonstration checklist end-to-end with a live campaign copy.
- [ ] Freeze a presentation candidate only after the above gates are green.

## P2 — world simulation systems

- [ ] Economy baseline: currencies, wages, food, lodging, mundane gear, transport, healing, monster/dungeon trade values.
- [ ] Travel model: distance, terrain, weather, pace, fatigue, camp, food/water and meaningful encounter frequency.
- [ ] Equipment/crafting: quality, durability, repair, materials and encumbrance without inventory micromanagement overload.
- [ ] Relationship/reputation evolution: local memory, rumor spread, favors, debts, fear, trust and conflicting dimensions.

## Release rule

No item moves to stable merely because it exists on this branch. Before release: tests → Windows build → artifact verification → live-upgrade compatibility check → then user migration instructions. Existing campaign saves remain the compatibility priority.
