# Kitaba 0.1.6 MVP — gap audit

Status: **release-hardening audit**. This list prevents a green CI build from being mistaken for a complete/presentable MVP. Each item is either resolved for 0.1.6 or deliberately classified outside the frozen MVP scope.

## Covered for the 0.1.6 candidate

- existing-campaign preservation strategy: schema remains v4 and release validation is performed on a backup copy first;
- interactive atlas core: strict pan/zoom/fullscreen bounds, search, filters, clustering, current position, points/routes/regions and broad uncertainty areas;
- player/GM separation for map and visual-binding subjects;
- concise interactive MJ pacing contract and terse-action enrichment without stealing player agency;
- visual-reference sidecar is checksum-protected and included in `.kitaba` backups;
- primary/current-state visual references are surfaced in ordinary PC/NPC/place views;
- fixed portrait/reference slots preserve aspect ratio and center-crop rather than stretching oversized images;
- map coordinates remain presentation-only and route distance uses explicit `distance_km`;
- release identity is aligned to 0.1.6 in npm/Tauri/Rust metadata, lockfiles and Windows artifact naming;
- story/editorial separation and safe HTML-rendering foundation remain available without being advertised as a finished in-app export feature.

## Deliberately outside the frozen 0.1.6 MVP

### Visual handoff into new ChatGPT conversations

The Companion persists local visual references, but a new ChatGPT conversation does not automatically receive the image bytes. A future player-safe visual manifest/reference handoff can be designed with the post-MVP source/prompt package. The 0.1.6 claim is therefore **Companion continuity**, not automatic cross-chat image transport.

### Permanent deletion of individual media assets

0.1.6 supports association, reassociation and unbinding. An unbound/obsolete image remains visibly unbound in the media library and cannot masquerade as the active reference. Destructive per-asset deletion, including backup/audit semantics, is deferred rather than added during release hardening.

### Full leveling/combat simulation contract

Skill progression, characteristic growth, bleeding/stabilization, surrender, disengage/flee, non-lethal combat, recovery/camp pressure and economy/travel calibration remain **PROPOSAL**. They are reference/test candidates, not promises of the 0.1.6 client and not canon until explicitly promoted into a later MASTER/MJ contract.

### Automatic adaptive music

The `music_state` and anti-churn model remain prototype foundations. Automatic ChatGPT-controlled playback is not part of the 0.1.6 MVP until a real control surface is validated end-to-end.

### In-app `Exporter mon histoire`

The safe editorial model/HTML renderer remains a tested foundation. Persistence of editorial scenes and a user-facing export action are post-MVP so they do not introduce a new persistence/asset surface during migration hardening.

### Project Sources / live-chat migration package

The live 0.1.5 campaign continues to use only the current MASTER source plus the physical map. A next MASTER, LIVE_PATCH, fresh-campaign prompt and concise migration guide are prepared only after the 0.1.6 client candidate passes migration-copy/client testing. Development drafts, installers and campaign exports are never Project Sources.

## Gates that still require a real client/campaign copy

Automated tests can validate contracts, builds and artifact metadata, but they cannot substitute for interaction with the user's real Windows installation and campaign data. Before merge/live upgrade, a COPY of a real 0.1.5 `.kitaba` must still pass:

1. restore/open + revision/timeline continuity + integrity;
2. map edges at multiple zooms/fullscreen with no exposed black background;
3. search/layers/current-location plus a reveal/reposition update;
4. oversized portrait/reference fitting with no stretching;
5. primary NPC portrait + current-state variant + scene reference where applicable;
6. backup → restore → integrity with visual bindings preserved;
7. close/reopen + final integrity spot check.

## Freeze decision

The code candidate is ready for client validation only after the **final branch HEAD** passes the full Windows pipeline and its produced installer is independently checked as 0.1.6. The PR remains draft and must not merge before the real-save-copy gates above are green.
