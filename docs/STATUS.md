# Verification status

Legend:
- **IMPLEMENTED+TESTED**: behavior is covered by executable tests and/or the production Windows CI gate.
- **IMPLEMENTED+STATIC-TESTED**: frontend behavior is covered by static/type/build verification but still needs user interaction smoke-testing on the installed app.
- **RUNTIME SMOKE TEST PENDING**: automated production build is green; final validation requires launching the installed application and exercising the real fresh-campaign workflow.

| Area | Status |
|---|---|
| SQLite core schema + migrations v1–v4 | IMPLEMENTED+TESTED |
| KITABA_UPDATE validation/reference engine | IMPLEMENTED+TESTED |
| Revision conflict rejection | IMPLEMENTED+TESTED |
| Duplicate update rejection | IMPLEMENTED+TESTED |
| Atomic transaction rollback | IMPLEMENTED+TESTED |
| Player/GM export separation | IMPLEMENTED+TESTED |
| KITABA_CONTEXT player/full | IMPLEMENTED+TESTED |
| Self-describing ChatGPT continuity contract | IMPLEMENTED+TESTED |
| Context export revision tracking / sync dirty state | IMPLEMENTED+TESTED |
| Rest Point snapshot | IMPLEMENTED+TESTED |
| Death gate + rollback/new timeline | IMPLEMENTED+TESTED |
| Latest-Rest-Point-only rollback | IMPLEMENTED+TESTED |
| Dead timeline preservation | IMPLEMENTED+TESTED |
| Dead resolution anti-save-scum storage | IMPLEMENTED+TESTED |
| Technical `.kitaba` ZIP backup + checksums | IMPLEMENTED+TESTED |
| Campaign visual assets (map/portrait) + backup inclusion | IMPLEMENTED+TESTED |
| Campaign-scoped `.kitaba` isolation + merge restore | IMPLEMENTED+TESTED |
| Full-backup DB/assets recovery hardening | IMPLEMENTED+TESTED |
| Backup tamper/future-schema rejection | IMPLEMENTED+TESTED |
| Rust/Tauri persistence core | IMPLEMENTED+TESTED |
| Rust core unit tests | IMPLEMENTED+TESTED |
| Rust `.kitaba` ZIP format parity | IMPLEMENTED+TESTED |
| React shell + sync/import/export UI | IMPLEMENTED+STATIC-TESTED |
| Fresh-campaign character creation gate | IMPLEMENTED+STATIC-TESTED |
| Generic campaign naming / no hard-coded protagonist | IMPLEMENTED+STATIC-TESTED |
| Diegetic terminology + canon-before-image contract rules | IMPLEMENTED+TESTED |
| Responsive PC sidebar / mobile drawer navigation | IMPLEMENTED+STATIC-TESTED |
| Purpose-built Character/Inventory/Relations/Knowledge/Journal/Missions views | IMPLEMENTED+STATIC-TESTED |
| Skills/Magic/Timeline/Adventurer Card views | IMPLEMENTED+STATIC-TESTED |
| World map player layer | IMPLEMENTED+STATIC-TESTED |
| Audited manual corrections + revision bump | IMPLEMENTED+TESTED |
| GM manual correction audit anti-spoiler | IMPLEMENTED+TESTED |
| Hidden GM map layer | IMPLEMENTED+STATIC-TESTED |
| Campaign archive / restore / guarded deletion | IMPLEMENTED+TESTED |
| Campaign integrity diagnostics | IMPLEMENTED+TESTED |
| Managed asset path-containment guard | IMPLEMENTED+TESTED |
| Cross-layer migration/protocol/Tauri command parity | IMPLEMENTED+TESTED |
| Windows x64 `.exe` / NSIS installer | IMPLEMENTED+TESTED |
| Installed-app end-to-end fresh-campaign smoke test | RUNTIME SMOKE TEST PENDING |

## Automated verification

The Windows production workflow verifies, in order:

1. executable Python reference tests;
2. reproducible `npm ci` installation;
3. TypeScript/Vite production build;
4. Rust unit tests;
5. Tauri Windows packaging;
6. Windows GUI PE subsystem;
7. upload of the portable executable and NSIS installer.

A clean 0.1.4 release candidate has passed every automated gate. Distribution uses the latest green `main` artifact, which must pass the same gates and contain both `kitaba-companion.exe` and the 0.1.4 NSIS installer.

## Remaining gate before long-term gameplay

The remaining release gate is a human end-to-end smoke test on the installed Windows application using a brand-new generic campaign workflow: launch, create a blank campaign, integrity diagnostic, GM context export, ChatGPT character-creation round-trip, update preview/import, re-export, backup creation, and restart persistence. The campaign should not be declared ready for long-term play until this user-visible smoke test passes.
