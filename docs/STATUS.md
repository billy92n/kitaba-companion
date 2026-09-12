# Verification status

Legend:
- **IMPLEMENTED+TESTED**: behavior is covered by executable tests and/or the production Windows CI gate.
- **IMPLEMENTED+STATIC-TESTED**: frontend behavior is covered by static/type/build verification and may still need installed-app interaction smoke-testing.
- **LIVE-UPGRADE SMOKE TEST PENDING**: automated production build is green; final validation concerns preserving the existing campaign while upgrading in place.

| Area | Status |
|---|---|
| SQLite core schema + migrations v1–v4 | IMPLEMENTED+TESTED |
| KITABA_UPDATE validation/reference engine | IMPLEMENTED+TESTED |
| Revision conflict / duplicate rejection / atomic rollback | IMPLEMENTED+TESTED |
| Player/GM export separation | IMPLEMENTED+TESTED |
| KITABA_CONTEXT player/full + continuity contract | IMPLEMENTED+TESTED |
| Rest Points / death gate / dead timeline preservation / anti-save-scum | IMPLEMENTED+TESTED |
| Technical `.kitaba` ZIP backup + checksums | IMPLEMENTED+TESTED |
| Campaign-scoped/full restore protection | IMPLEMENTED+TESTED |
| Campaign visual assets + backup inclusion | IMPLEMENTED+TESTED |
| Campaign integrity diagnostics / managed path containment | IMPLEMENTED+TESTED |
| Rust/Tauri persistence core | IMPLEMENTED+TESTED |
| Generic fresh-campaign onboarding / no hard-coded protagonist | IMPLEMENTED+TESTED |
| Diegetic terminology + canon-before-image contract | IMPLEMENTED+TESTED |
| Discovery-gated navigation | IMPLEMENTED+TESTED |
| Responsive PC sidebar / mobile drawer | IMPLEMENTED+STATIC-TESTED |
| Character/Inventory/Relations/Knowledge/Journal/Missions views | IMPLEMENTED+STATIC-TESTED |
| Skills/Magic/Timeline/Adventurer Card views | IMPLEMENTED+STATIC-TESTED |
| Interactive world map: zoom / pan / fullscreen / clickable markers | IMPLEMENTED+TESTED |
| Player-knowledge-gated map entities and normalized x/y contract | IMPLEMENTED+TESTED |
| Hidden GM map layer | IMPLEMENTED+STATIC-TESTED |
| Stable visual identity / state variants / group-scene guidance | IMPLEMENTED+TESTED |
| Concise enrichment of terse player actions | IMPLEMENTED+TESTED |
| Declared-success becomes attempt + hidden uncertainty resolution | IMPLEMENTED+TESTED |
| Adaptive-music scene-state contract | IMPLEMENTED+TESTED |
| Campaign archive / restore / guarded deletion | IMPLEMENTED+TESTED |
| Windows x64 `.exe` / NSIS installer | IMPLEMENTED+TESTED |
| Existing 0.1.4 campaign upgraded in place to 0.1.5 | LIVE-UPGRADE SMOKE TEST PENDING |

## Automated verification

The 0.1.5 Windows production workflow verifies, in order:

1. executable Python reference tests;
2. reproducible `npm ci` installation;
3. TypeScript/Vite production build;
4. Rust unit tests;
5. Tauri Windows packaging;
6. Windows GUI PE subsystem;
7. upload of the portable executable and NSIS installer.

Production gate: **SUCCESS** on Build Windows Direct Source #71 (`34715221001`) for the 0.1.5 source merge commit `dcbeaf468d60bdaf4d96c5b83bd01b16a01cff2c`. The run reported 76 Python tests passed, 7 Rust tests passed, a successful production frontend build, successful Tauri/NSIS packaging and successful artifact upload.

## Remaining gate for the running playtest

The campaign no longer needs to be restarted. The only remaining user-visible gate is the in-place live-upgrade smoke test on the current campaign: create a `.kitaba` backup, install 0.1.5 over the current application, reopen the same campaign, verify revision/timeline/player data are preserved, run integrity diagnostics, confirm the world map is still present, export a fresh GM_FULL, then continue in the same ChatGPT game chat. No new SQLite migration is involved; `CURRENT_SCHEMA_VERSION` remains 4.
