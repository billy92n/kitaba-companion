# Kitaba Companion

Build staging repository for Kitaba Companion.

The current source snapshot is stored in `kitaba-companion-source.zip`; the Windows GitHub Actions workflow extracts it, runs the reference tests, builds the React frontend, runs Rust tests, and then attempts the Tauri Windows build.

This repository is intentionally separate from the historical `Kitaba` repository.
