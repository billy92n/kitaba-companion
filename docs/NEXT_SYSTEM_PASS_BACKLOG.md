# Kitaba — next system pass backlog

Status: working backlog for the post-0.1.5 development branch. It must not mutate a live campaign by itself.

## P0 — correctness / continuity

- [x] Clamp interactive world-map pan so the image cannot be dragged beyond world bounds.
- [x] Recompute bounds after zoom, resize and fullscreen changes.
- [x] Keep map markers aligned with the actually rendered image area.
- [x] Highlight the current linked settlement/place when coordinates exist.
- [x] Add regression coverage for map boundary behavior.
- [ ] Validate the map-boundary fix in a Windows build before merging to `main`.

## P1 — core game mechanics

- [x] Draft a calibrated hidden progression model with nonlinear mastery thresholds and anti-farming.
- [x] Draft a single hidden uncertainty-resolution scale shared by exploration, social and skill actions.
- [ ] Simulate/check probability bands and learning pace against representative character profiles.
- [ ] Promote only the validated portions into the next MASTER SOURCE / MJ contract.
- [ ] Define damage, armor, HP, injuries and recovery on the same scale.
- [ ] Define mana expenditure, recovery and overchanneling severity.

## P1 — interactive fiction quality

Already carried by 0.1.5 contract and still under playtest:

- shorter playable beats rather than passive text walls;
- enrich terse player actions with concise gestures/sensory/emotional detail without changing intent;
- player-declared outcomes remain attempts when uncertain;
- player controls protagonist actions, not NPC reactions or world results;
- deeper description on inspection, major reveals and emotionally important beats rather than every turn.

Next work:

- [ ] Add explicit pacing profiles for exploration, dialogue, tension/combat and emotional scenes.
- [ ] Define chapter/scene editorial capture for future readable story export without storing a verbatim chat transcript as canon.

## P1 — visual continuity

- [ ] Stable visual identity record linked to each important PC/NPC/place.
- [ ] Reference-image binding from media assets to campaign entities.
- [ ] State variants for the same character: normal, wounded, sick, exhausted, ceremonial, heroic, deceased where appropriate.
- [ ] Multi-character scene reference set so known characters remain visually consistent in group illustrations.
- [ ] Campaign-level art-direction profile for consistent fantasy-anime/isekai visual language without copying a specific copyrighted production.
- [ ] Illustration priority policy for home, starting settlement, close relations and major locations/scenes.

## P1 — living atlas

- [x] Normalized x/y world-map markers supported by Companion.
- [ ] Geography-placement contract: biome, climate, rivers, terrain, economy and known demographics constrain new settlements before coordinates are persisted.
- [ ] Region/state/route polygon or path layers in addition to point markers.
- [ ] Current-location auto-focus option without forcing it on the player.
- [ ] Discovery states such as known-by-name, approximately located, precisely located and visited.
- [ ] Player/MJ layer separation for undiscovered geography.

## P2 — world simulation systems

- [ ] Economy baseline: currencies, wages, food, lodging, mundane gear, transport, healing, monster/dungeon trade values.
- [ ] Travel model: distance, terrain, weather, pace, fatigue, camp, food/water and meaningful encounter frequency.
- [ ] Equipment/crafting: quality, durability, repair, materials and encumbrance without inventory micromanagement overload.
- [ ] Relationship/reputation evolution: local memory, rumor spread, favors, debts, fear, trust and conflicting dimensions.

## P2 — adaptive ambience

- [ ] Scene-level `music_state` contract with stable ambience categories and transition rules.
- [ ] Do not switch music on every message; transition only on meaningful scene-tone changes.
- [ ] Evaluate delivery path: ChatGPT-compatible music integration where available versus a future Companion-native player.

## P2 — final story/book

- [ ] Separate compact canonical memory from an editorial narrative layer.
- [ ] Scene/chapter summaries preserving facts without turning summaries into new canon.
- [ ] Illustrated campaign export concept: readable HTML/PDF/EPUB-like output after sufficient validation.

## Release rule

No item moves to stable merely because it exists on this branch. Before release: tests → Windows build → artifact verification → live-upgrade compatibility check → then user migration instructions. Existing campaign saves remain the compatibility priority.
