# Kitaba Companion 0.1.3 — launch gate

This release is intended to be the first-campaign hardening build.

Critical gates before declaring Sully ready for long-term play:

- Python reference protocol/world-state tests pass.
- TypeScript/Vite production build passes.
- Rust persistence/backup/rollback tests pass.
- Tauri Windows packaging succeeds.
- Windows PE GUI subsystem verification passes.
- Update files loaded through the file picker remain raw-hidden by default; preview exposes player changes and masked GM counts only.
- PLAYER context contains no GM-only truth.
- GM_FULL carries the self-describing World State contract, including off-screen GM-only persistence.
- Campaign-scoped `.kitaba` backup/restore keeps unrelated campaigns isolated and assets checksum-protected.
- Full restore recovery remains DB/assets consistent.
- Player-facing World and Media sections are present.
- Final installed-app Sully smoke test on the user's Windows PC passes before `Commencer`.

The installed-app smoke test is intentionally the only user-visible release gate that automation cannot replace.
