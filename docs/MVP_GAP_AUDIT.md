# Kitaba 0.1.6 MVP — gap audit

Status: **release-hardening + studio-readiness audit**. This list prevents a green CI build from being mistaken for a complete/presentable MVP. Each item is either resolved for 0.1.6, deliberately outside the frozen scope, or still requires real-client proof.

## Covered for the 0.1.6 candidate

- existing-campaign preservation strategy: schema remains v4 and release validation is performed on a backup copy first;
- interactive atlas core: strict pan/zoom/fullscreen bounds, search, filters, clustering, current position, points/routes/regions and broad uncertainty areas;
- player/GM separation for map and visual-binding subjects;
- concise interactive MJ pacing contract and terse-action enrichment without stealing player agency;
- visual-reference sidecar is checksum-protected and included in `.kitaba` backups;
- primary/current-state visual references are surfaced in ordinary PC/NPC/place views;
- fixed portrait/reference slots preserve aspect ratio and center-crop rather than stretching oversized images;
- visual-reference launcher is no longer a global floating obstruction and is confined to the Media/continuity surface;
- map coordinates remain presentation-only and route distance uses explicit `distance_km`;
- release identity is aligned to 0.1.6 in npm/Tauri/Rust metadata, lockfiles and Windows artifact naming;
- story/editorial separation and safe HTML-rendering foundation remain available without being advertised as a finished in-app export feature;
- architecture/presentation distinguish the current ChatGPT prototype from the reusable studio adaptation boundary;
- post-MVP API direction is documented without making API integration a 0.1.6 release dependency.

## Human evidence already observed

- the 0.1.6 client opened with an existing lived campaign visible;
- the supplied client screenshot showed a green integrity diagnostic;
- the top-left portrait appeared correctly framed rather than visibly stretched in the observed surface;
- the only obvious UI issue reported was the global floating `Références visuelles` launcher;
- that launcher was moved into the Media/continuity page, rebuilt through the complete Windows pipeline, and the user subsequently confirmed the correction was satisfactory.

This is useful client evidence, but it does **not** automatically prove every migration-copy gate below unless the specific action was exercised on a disposable copy.

## Deliberately outside the frozen 0.1.6 MVP

### Full in-app narrative API

The long-term product target is to let the player perform the complete game loop inside the Companion through a controlled narrative runtime/API. The target architecture is documented in `API_INTEGRATION_TARGET.md`.

0.1.6 does not need a live API provider integration. Adding credentials, streaming chat, provider error handling and automatic update execution during release hardening would expand the failure surface without improving proof of the core continuity model.

### Visual handoff into new ChatGPT conversations

The Companion persists local visual references, but a new ChatGPT conversation does not automatically receive the image bytes. A future player-safe visual manifest/reference handoff can be designed with the post-MVP source/prompt package. The 0.1.6 claim is therefore **Companion continuity**, not automatic cross-chat image transport.

### Permanent deletion of individual media assets

0.1.6 supports association, reassociation and unbinding. An unbound/obsolete image remains visibly unbound in the media library and cannot masquerade as the active reference. Destructive per-asset deletion, including backup/audit semantics, is deferred rather than added during release hardening.

### Full leveling/combat simulation contract

Skill progression, characteristic growth, bleeding/stabilization, surrender, disengage/flee, non-lethal combat, recovery/camp pressure and economy/travel calibration remain **PROPOSAL**. They are reference/test candidates, not promises of the 0.1.6 client and not canon until explicitly promoted into a later MASTER/MJ contract.

### Automatic adaptive music

The `music_state` and anti-churn model remain prototype foundations. Automatic model-controlled playback is not part of the 0.1.6 MVP until a real control surface is validated end-to-end.

### In-app `Exporter mon histoire`

The safe editorial model/HTML renderer remains a tested foundation. Persistence of editorial scenes and a user-facing export action are post-MVP so they do not introduce a new persistence/asset surface during migration hardening.

## Gates that still require a real client/campaign copy

Automated tests can validate contracts, builds and artifact metadata, but they cannot substitute for every interaction with the user's real Windows installation and campaign data. Before merge/live upgrade, a COPY of a real 0.1.5 `.kitaba` should still explicitly pass:

1. restore/open + revision/timeline continuity + integrity;
2. map edges at multiple zooms/fullscreen with no exposed black background;
3. search/layers/current-location plus a reveal/reposition update;
4. primary NPC portrait + current-state variant + scene reference where applicable;
5. backup → restore → integrity with visual bindings preserved;
6. close/reopen + final integrity spot check.

The oversized-image display and obstructive visual-reference launcher already have direct client evidence plus automated regression coverage, so they do not need to block the same way unless a new regression appears.

## Studio-readiness gate

Before external presentation, the MVP package should also contain:

- a 10–15 minute deterministic demo path;
- a concise architecture/adaptation explanation;
- explicit separation between implemented features and roadmap claims;
- a clean Windows build/install path;
- no dependence on private campaign secrets for the demo;
- a disposable demonstration save or migration copy;
- a clear statement that the current ChatGPT workflow is replaceable by a future narrative runtime/API without bypassing canonical validation.

## Freeze decision

Feature scope remains frozen. From this point, 0.1.6 accepts only release correctness, regressions, documentation and demo-readiness changes. A future API bridge belongs to the next product phase after this candidate proves the continuity core.