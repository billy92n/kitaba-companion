# Verification status

Legend:
- **IMPLEMENTED+TESTED**: executable reference implementation exists and automated tests pass in this environment.
- **IMPLEMENTED/NOT COMPILED HERE**: production Rust/React source exists, but this Linux environment has no Rust toolchain / Windows Tauri runtime, so compilation is not yet claimed.
- **NOT YET VERIFIED ON WINDOWS**: requires the future Windows build gate.

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
| Backup tamper/future-schema rejection | IMPLEMENTED+TESTED |
| Rust/Tauri persistence core | IMPLEMENTED/NOT COMPILED HERE |
| Rust core unit tests | IMPLEMENTED/NOT COMPILED HERE |
| Rust `.kitaba` ZIP format parity | IMPLEMENTED/NOT COMPILED HERE |
| React shell + sync/import/export UI | IMPLEMENTED/NOT COMPILED HERE |
| Responsive PC sidebar / mobile drawer navigation | IMPLEMENTED+STATIC-TESTED |
| Purpose-built Character/Inventory/Relations/Knowledge/Journal/Missions views | IMPLEMENTED/NOT COMPILED HERE |
| Skills/Magic/Timeline/Adventurer Card views | IMPLEMENTED/NOT COMPILED HERE |
| World map player layer | IMPLEMENTED/NOT COMPILED HERE |
| Audited manual corrections + revision bump | IMPLEMENTED+TESTED |
| GM manual correction audit anti-spoiler | IMPLEMENTED+TESTED |
| Hidden GM map layer | IMPLEMENTED/NOT COMPILED HERE |
| Campaign archive / restore / guarded deletion | IMPLEMENTED+TESTED |
| Campaign integrity diagnostics | IMPLEMENTED+TESTED |
| Managed asset path-containment guard | IMPLEMENTED+TESTED |
| Cross-layer migration/protocol/Tauri command parity | IMPLEMENTED+TESTED |
| Windows `.exe` / installer | NOT YET VERIFIED ON WINDOWS |

## Automated verification in this environment

`python -m pytest reference/tests -q` → **61 passed**.

The reference suite has already caught real implementation/test issues during development, including migration replay ordering and one false-positive time-validation test that was corrected to test the intended invariant.

## Remaining gate before “playable” release

The application will not be presented to the user as playable until the Rust/Tauri project compiles on a real Windows runner, the frontend production build succeeds, the Windows installer is produced, and the first end-to-end Sully synchronization cycle is exercised against that build.
