# Kitaba Companion 0.1.5 — release gate

Production Windows release validated on `main`.

- commit: `dcbeaf468d60bdaf4d96c5b83bd01b16a01cff2c`
- workflow: Build Windows Direct Source #71 (`34715221001`)
- result: SUCCESS
- Python reference suite: 76 passed
- Rust tests: 7 passed
- TypeScript/Vite: passed
- Tauri/NSIS + Windows GUI PE check: passed
- artifact: `kitaba-companion-windows-0.1.5`
- artifact id: `10304123503`
- artifact SHA-256: `a83f8e2d5288c20c194a376b73bdf64803060bef9247f49af28ca2d0b9be9962`

Compatibility: schema remains v4; there is no 0.1.5 database migration. Existing 0.1.4 campaigns are intended to be upgraded in place after creating a technical `.kitaba` backup.

The remaining user-visible check is the live-upgrade smoke test on the existing campaign: install over 0.1.4, reopen the same campaign, confirm revision/timeline preservation, run integrity diagnostics, export a fresh GM_FULL, and continue in the same game chat.
