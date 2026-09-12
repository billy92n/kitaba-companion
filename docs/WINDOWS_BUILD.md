# Windows build

## GitHub Actions

Push the repository to GitHub and run **Actions → Build Windows → Run workflow**.

The workflow:
1. installs Node 22;
2. installs stable Rust;
3. installs npm dependencies;
4. builds the React frontend;
5. runs Rust checks/tests;
6. runs the Tauri release build;
7. uploads the NSIS installer and release executable as an artifact.

## Local Windows build

Prerequisites follow Tauri 2 requirements: Node.js, Rust stable, Microsoft C++ Build Tools/WebView2 as required by Tauri.

Then:

```powershell
npm install
npm run build
cargo test --manifest-path src-tauri/Cargo.toml
npm run tauri build
```

Expected bundle directory:

```text
src-tauri/target/release/bundle/nsis/
```

Do not treat the Windows executable as verified until this build has actually succeeded on Windows.
