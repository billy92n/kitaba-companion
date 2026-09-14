# Kitaba Companion — compatibilité 0.1.5 → 0.1.6

Status: **release-hardening evidence**. This document does not replace the required real-client smoke test on a disposable backup copy.

## What is intentionally unchanged

At the 0.1.6 freeze, `src-tauri/src/db.rs` is byte-identical between stable `main` 0.1.5 and `next-system-pass` 0.1.6 candidate. Both refs resolve to Git blob SHA:

`e1198993619865a5a38af5acf22a9ab9c1d0f20f`

This means the production code that owns the following remains the same across the two versions:

- SQLite migrations and schema version;
- `.kitaba` technical backup creation;
- `.kitaba` restore;
- revision/timeline persistence;
- Rest Point/dead-timeline integrity handling;
- campaign asset registration and backup inclusion;
- integrity diagnostics.

The schema remains **v4** and there is no migration `0005` in 0.1.6.

## What 0.1.6 adds without changing the DB schema

Visual-reference bindings are implemented as campaign-managed metadata inside the existing asset/backup model. They do not require rewriting a 0.1.5 SQLite database before it can be opened.

A restored 0.1.5 campaign therefore does not need pre-existing visual-binding metadata. It may acquire that metadata only after the player begins using the new visual-reference features.

## Automated compatibility coverage

`reference/tests/test_release_hardening_016.py` fails if the 0.1.6 branch silently:

- changes `CURRENT_SCHEMA_VERSION` away from 4;
- adds an unreviewed migration beyond `0004`;
- loses the technical backup/restore/integrity entry points.

The Rust visual-continuity suite additionally covers a **legacy-style campaign with no `visual-bindings.json` at all**:

1. create a campaign using the existing v4 persistence model;
2. keep visual bindings absent, matching a 0.1.5 campaign;
3. create a `.kitaba` technical backup;
4. restore it into a fresh database/storage root;
5. verify the new visual-binding API returns an empty set rather than an error;
6. run campaign integrity and require it to remain green.

This specifically guards the additive 0.1.6 visual-reference feature against assuming that older campaigns already contain its metadata.

These are release guards, not substitutes for using a real save copy.

## Why a human migration copy is still required

Byte-identical persistence code and compatibility tests substantially reduce migration risk, but a real installation can still reveal issues that repository-level tests cannot prove, for example:

- application storage paths/permissions on the user's Windows machine;
- interaction with an already-existing installed data directory;
- actual campaign asset files created during play;
- UI regressions after restore/reopen;
- user-specific combinations of campaign data.

Therefore the first upgrade of a lived campaign must remain:

1. create/keep a `.kitaba` backup from 0.1.5;
2. use a disposable copy for first 0.1.6 validation;
3. verify campaign revision/timeline and green integrity;
4. verify map and visual-reference behavior;
5. only then approve the normal live upgrade.

## Release claim

Safe wording for 0.1.6 before the real-save-copy gate is complete:

> "0.1.6 preserves the 0.1.5 persistence schema and backup/restore implementation and has automated compatibility guards, including restore of a campaign with no 0.1.6 visual metadata; final lived-save compatibility remains subject to the real-client copy test."

Do not claim a lived-save migration is proven until that client gate has actually passed.
