# Kitaba 0.1.6 MVP — gap audit

Status: **working audit**. Created after a deliberate pre-freeze review; this list exists specifically to prevent a green CI build from being mistaken for a complete/presentable MVP.

## Already covered well enough for candidate testing

- existing-campaign preservation strategy: schema remains v4 and release validation is performed on a backup copy first;
- interactive atlas core: pan/zoom/fullscreen bounds implementation, search, filters, clustering, current position, points/routes/regions;
- player/GM separation for map and visual-binding subjects;
- concise interactive MJ pacing contract and terse-action enrichment without stealing player agency;
- hidden uncertainty-resolution and skill-progression candidates with calibration tests;
- combat/mana/recovery and economy/travel reference candidates kept explicitly PROPOSAL;
- visual-reference sidecar is checksum-protected and included in `.kitaba` backups;
- story/editorial separation and safe HTML-rendering foundation.

## Gaps that must not be hidden by the MVP label

### 1. Visual continuity across ChatGPT conversations

The Companion can now remember that an imported local asset belongs to a PLAYER subject, but ChatGPT does not automatically receive the image bytes when a new conversation starts. Before claiming full visual memory, define and test a player-safe exported visual manifest plus a reliable reference-image handoff path.

### 2. Wrong/obsolete illustration cleanup

The current image library can unbind a reference but still lacks a first-class safe per-asset delete flow. Now that illustrations are a major product pillar, the MVP should either add backed-up deletion with binding cleanup or clearly defer it while ensuring obsolete images cannot be mistaken for active references.

### 3. References in ordinary character/place views

A separate visual-reference tool exists, but a polished experience should surface the primary image/current state directly where the player views the relevant NPC/place. This is more important for presentation than a hidden technical binding screen.

### 4. Leveling is not yet the whole progression system

Skill mastery has a calibrated candidate. Long-term growth of underlying characteristics/capacity is not yet calibrated and must remain separate from skill XP. Do not imply that the entire leveling system is final until this exists and is tested.

### 5. Combat critical states

Damage/armor/injury/mana models exist, but bleeding/stabilization, surrender, disengage/flee and explicit non-lethal resolution still require validation before combat mechanics become canon.

### 6. Broad geographic uncertainty

`approximate` markers exist, but a genuinely broad known area still needs uncertainty-area rendering so the UI does not visually imply precision the character does not possess.

### 7. Map coordinates are not physical distance

Normalized x/y are presentation coordinates only. Travel duration must rely on an explicit route/world distance model. Never infer kilometers directly from pixel distance without a separately locked world scale/projection.

### 8. Adaptive music is not end-to-end yet

The scene-state/anti-churn model exists, but automatic ChatGPT-controlled playback has not been validated. Keep it labelled prototype until the actual playback surface is proven; do not simulate success in text.

### 9. `Exporter mon histoire` is foundation-only

The editorial scene model and HTML renderer are tested, but the Companion does not yet expose the complete in-app export pipeline. Either wire a basic HTML export into the MVP or present it explicitly as the next step rather than a finished feature.

### 10. Release/version hygiene

0.1.6 is now separated from stable 0.1.5. Before freeze, confirm installer metadata/artifact name and reconcile informational root-version metadata in lockfiles where practical. Production hashes must come from the final `main` build, not an earlier candidate.

### 11. Current-project source discipline

The live 0.1.5 campaign still needs only MASTER v1.4 + the physical map in Project Sources. The future 0.1.6 migration will require a deliberately prepared next MASTER/LIVE_PATCH/prompt package, but draft development documents must never be added to Project Sources.

## Freeze decision

The MVP is presentation-ready only when every **P0 release gate** is green and each gap above is either implemented/tested or explicitly labelled out-of-scope in the presentation. No ambiguous half-feature is marketed as complete.
