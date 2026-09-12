use chrono::Utc;
use base64::Engine;
use rusqlite::{params, Connection, OptionalExtension, Transaction};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use uuid::Uuid;
use std::io::{Read, Write};
use zip::{CompressionMethod, ZipArchive, ZipWriter, write::SimpleFileOptions};

use crate::{error::KitabaError, model::{AssetSummary, CampaignSummary, ImportResult, KitabaUpdate, LinkOperation, Operation, UpdatePreview}};

const MIGRATION_001: &str = include_str!("../migrations/0001_initial.sql");
const MIGRATION_002: &str = include_str!("../migrations/0002_death_gate.sql");
const MIGRATION_003: &str = include_str!("../migrations/0003_entity_protection.sql");
const MIGRATION_004: &str = include_str!("../migrations/0004_sync_export_state.sql");
pub const CURRENT_SCHEMA_VERSION: i64 = 4;

pub fn current_schema_version(conn: &Connection) -> Result<i64, KitabaError> {
    let exists: Option<i64> = conn.query_row(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'",
        [], |r| r.get(0)
    ).optional()?;
    if exists.is_none() { return Ok(0); }
    Ok(conn.query_row("SELECT COALESCE(MAX(version),0) FROM schema_migrations", [], |r| r.get(0))?)
}

pub fn migrate(conn: &Connection) -> Result<(), KitabaError> {
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)",
        [],
    )?;
    for (version, sql) in [(1_i64, MIGRATION_001), (2_i64, MIGRATION_002), (3_i64, MIGRATION_003), (4_i64, MIGRATION_004)] {
        let applied = conn.query_row(
            "SELECT 1 FROM schema_migrations WHERE version=?1",
            [version],
            |r| r.get::<_, i64>(0),
        ).optional()?;
        if applied.is_none() {
            let tx = conn.unchecked_transaction()?;
            tx.execute_batch(sql)?;
            tx.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?1, ?2)",
                params![version, Utc::now().to_rfc3339()],
            )?;
            tx.commit()?;
        }
    }
    Ok(())
}

pub fn create_campaign(conn: &Connection, name: &str) -> Result<CampaignSummary, KitabaError> {
    let id = Uuid::new_v4().to_string();
    let timeline_id = Uuid::new_v4().to_string();
    let now = Utc::now().to_rfc3339();
    let tx = conn.unchecked_transaction()?;
    tx.execute(
        "INSERT INTO campaigns(id,name,current_revision,current_timeline_id,created_at,updated_at) VALUES (?1,?2,0,?3,?4,?4)",
        params![id, name, timeline_id, now],
    )?;
    tx.execute(
        "INSERT INTO timelines(id,campaign_id,status,started_revision,created_at) VALUES (?1,?2,'ACTIVE',0,?3)",
        params![timeline_id, id, now],
    )?;
    audit(&tx, Some(&id), Some(&timeline_id), "campaign_created", "Campaign created", json!({}))?;
    tx.commit()?;
    Ok(CampaignSummary { id, name: name.to_owned(), current_revision: 0, current_timeline_id: timeline_id, game_time: None, death_pending: false, death_summary: None, last_gm_export_revision: None, last_gm_export_at: None, last_player_export_revision: None, last_player_export_at: None })
}

pub fn list_campaigns(conn: &Connection) -> Result<Vec<CampaignSummary>, KitabaError> {
    let mut stmt = conn.prepare(
        "SELECT id,name,current_revision,current_timeline_id,game_time,death_pending,death_summary,last_gm_export_revision,last_gm_export_at,last_player_export_revision,last_player_export_at FROM campaigns WHERE archived_at IS NULL ORDER BY updated_at DESC"
    )?;
    let rows = stmt.query_map([], |r| Ok(CampaignSummary {
        id: r.get(0)?, name: r.get(1)?, current_revision: r.get(2)?, current_timeline_id: r.get(3)?, game_time: r.get(4)?,
        death_pending: r.get::<_, i64>(5)? != 0, death_summary: r.get(6)?, last_gm_export_revision: r.get(7)?, last_gm_export_at: r.get(8)?, last_player_export_revision: r.get(9)?, last_player_export_at: r.get(10)?
    }))?;
    Ok(rows.collect::<Result<Vec<_>, _>>()?)
}


pub fn list_archived_campaigns(conn: &Connection) -> Result<Vec<CampaignSummary>, KitabaError> {
    let mut stmt = conn.prepare(
        "SELECT id,name,current_revision,current_timeline_id,game_time,death_pending,death_summary,last_gm_export_revision,last_gm_export_at,last_player_export_revision,last_player_export_at FROM campaigns WHERE archived_at IS NOT NULL ORDER BY archived_at DESC"
    )?;
    let rows = stmt.query_map([], |r| Ok(CampaignSummary {
        id: r.get(0)?, name: r.get(1)?, current_revision: r.get(2)?, current_timeline_id: r.get(3)?, game_time: r.get(4)?,
        death_pending: r.get::<_, i64>(5)? != 0, death_summary: r.get(6)?, last_gm_export_revision: r.get(7)?, last_gm_export_at: r.get(8)?, last_player_export_revision: r.get(9)?, last_player_export_at: r.get(10)?
    }))?;
    Ok(rows.collect::<Result<Vec<_>, _>>()?)
}

pub fn set_campaign_archived(conn: &Connection, campaign_id: &str, archived: bool) -> Result<(), KitabaError> {
    let row = conn.query_row(
        "SELECT current_timeline_id,archived_at FROM campaigns WHERE id=?1",
        [campaign_id],
        |r| Ok((r.get::<_, String>(0)?, r.get::<_, Option<String>>(1)?)),
    ).optional()?.ok_or(KitabaError::CampaignNotFound)?;
    let already = row.1.is_some();
    if already == archived { return Ok(()); }
    let now = Utc::now().to_rfc3339();
    let tx = conn.unchecked_transaction()?;
    if archived {
        tx.execute("UPDATE campaigns SET archived_at=?1,updated_at=?1 WHERE id=?2", params![now, campaign_id])?;
        audit(&tx, Some(campaign_id), Some(&row.0), "campaign_archived", "Campaign archived", json!({}))?;
    } else {
        tx.execute("UPDATE campaigns SET archived_at=NULL,updated_at=?1 WHERE id=?2", params![now, campaign_id])?;
        audit(&tx, Some(campaign_id), Some(&row.0), "campaign_unarchived", "Campaign restored from archive", json!({}))?;
    }
    tx.commit()?;
    Ok(())
}

pub fn delete_campaign_permanently(conn: &Connection, campaign_id: &str, expected_name: &str, asset_root: &std::path::Path) -> Result<(), KitabaError> {
    let name = conn.query_row("SELECT name FROM campaigns WHERE id=?1", [campaign_id], |r| r.get::<_, String>(0)).optional()?.ok_or(KitabaError::CampaignNotFound)?;
    if name != expected_name { return Err(KitabaError::Validation("Campaign name confirmation does not match".into())); }
    conn.execute("DELETE FROM campaigns WHERE id=?1", [campaign_id])?;
    let campaign_dir = asset_root.join(campaign_id);
    if campaign_dir.exists() { std::fs::remove_dir_all(campaign_dir)?; }
    Ok(())
}

pub fn integrity_report(conn: &Connection, campaign_id: &str, asset_root: &std::path::Path) -> Result<crate::model::IntegrityReport, KitabaError> {
    let campaign = conn.query_row(
        "SELECT current_revision,current_timeline_id FROM campaigns WHERE id=?1",
        [campaign_id],
        |r| Ok((r.get::<_, i64>(0)?, r.get::<_, String>(1)?)),
    ).optional()?.ok_or(KitabaError::CampaignNotFound)?;
    let mut checks: Vec<crate::model::IntegrityCheck> = Vec::new();
    let mut push = |code: &str, ok: bool, message: String| {
        checks.push(crate::model::IntegrityCheck { code: code.to_owned(), ok, message });
    };

    let sqlite_integrity: String = conn.query_row("PRAGMA integrity_check", [], |r| r.get(0))?;
    push("sqlite_integrity", sqlite_integrity == "ok", if sqlite_integrity == "ok" { "Base SQLite saine".into() } else { "Échec du contrôle SQLite".into() });

    let mut fk_stmt = conn.prepare("PRAGMA foreign_key_check")?;
    let mut fk_rows = fk_stmt.query([])?;
    let fk_ok = fk_rows.next()?.is_none();
    push("foreign_keys", fk_ok, if fk_ok { "Clés étrangères cohérentes".into() } else { "Violation(s) de clé étrangère détectée(s)".into() });

    let mut active_stmt = conn.prepare("SELECT id FROM timelines WHERE campaign_id=?1 AND status='ACTIVE'")?;
    let active_ids = active_stmt.query_map([campaign_id], |r| r.get::<_, String>(0))?.collect::<Result<Vec<_>, _>>()?;
    let active_ok = active_ids.len() == 1 && active_ids[0] == campaign.1;
    push("active_timeline", active_ok, if active_ok { "Timeline active cohérente".into() } else { "Incohérence de timeline active".into() });

    let future_updates: i64 = conn.query_row("SELECT COUNT(*) FROM applied_updates WHERE campaign_id=?1 AND target_revision>?2", params![campaign_id, campaign.0], |r| r.get(0))?;
    push("revision_bounds", future_updates == 0, if future_updates == 0 { "Révisions appliquées cohérentes".into() } else { "Une mise à jour dépasse la révision canonique".into() });

    let mut bad_rest = 0_i64;
    let mut rest_stmt = conn.prepare("SELECT snapshot_json,snapshot_sha256 FROM rest_points WHERE campaign_id=?1")?;
    for row in rest_stmt.query_map([campaign_id], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))? {
        let (raw, expected) = row?;
        let actual = hex::encode(Sha256::digest(raw.as_bytes()));
        if actual != expected { bad_rest += 1; }
    }
    push("rest_point_hashes", bad_rest == 0, if bad_rest == 0 { "Rest Points intègres".into() } else { format!("{bad_rest} Rest Point(s) altéré(s)") });

    let mut bad_dead = 0_i64;
    let mut dead_stmt = conn.prepare("SELECT state_snapshot_json,state_snapshot_sha256 FROM dead_timelines WHERE campaign_id=?1")?;
    for row in dead_stmt.query_map([campaign_id], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))? {
        let (raw, expected) = row?;
        let actual = hex::encode(Sha256::digest(raw.as_bytes()));
        if actual != expected { bad_dead += 1; }
    }
    push("dead_timeline_hashes", bad_dead == 0, if bad_dead == 0 { "Timelines mortes intègres".into() } else { format!("{bad_dead} timeline(s) morte(s) altérée(s)") });

    let mut missing_assets = 0_i64;
    let mut altered_assets = 0_i64;
    let mut asset_stmt = conn.prepare("SELECT relative_path,sha256 FROM assets WHERE campaign_id=?1")?;
    for row in asset_stmt.query_map([campaign_id], |r| Ok((r.get::<_, String>(0)?, r.get::<_, Option<String>>(1)?)))? {
        let (relative, expected) = row?;
        let path = match managed_asset_path(asset_root, campaign_id, &relative) {
            Ok(path) => path,
            Err(_) => { altered_assets += 1; continue; }
        };
        if !path.is_file() { missing_assets += 1; continue; }
        if let Some(expected_hash) = expected {
            let actual = hex::encode(Sha256::digest(std::fs::read(&path)?));
            if actual != expected_hash { altered_assets += 1; }
        }
    }
    let assets_ok = missing_assets == 0 && altered_assets == 0;
    push("assets", assets_ok, if assets_ok { "Assets intègres".into() } else { format!("Assets: {missing_assets} manquant(s), {altered_assets} altéré(s)") });

    let invalid_visibility: i64 = conn.query_row("SELECT COUNT(*) FROM entity_documents WHERE campaign_id=?1 AND visibility NOT IN ('PLAYER','GM')", [campaign_id], |r| r.get(0))?;
    push("visibility_domain", invalid_visibility == 0, if invalid_visibility == 0 { "Domaines de visibilité valides".into() } else { "Valeur de visibilité invalide détectée".into() });

    let ok = checks.iter().all(|c| c.ok);
    Ok(crate::model::IntegrityReport { campaign_id: campaign_id.to_owned(), checked_at: Utc::now().to_rfc3339(), ok, checks })
}

fn managed_asset_path(asset_root: &std::path::Path, campaign_id: &str, relative: &str) -> Result<std::path::PathBuf, KitabaError> {
    let relative_path = std::path::Path::new(relative);
    if relative_path.is_absolute() || relative_path.components().any(|c| matches!(c, std::path::Component::ParentDir)) {
        return Err(KitabaError::Validation("unsafe registered asset path".into()));
    }
    let first = relative_path.components().next();
    let belongs = matches!(first, Some(std::path::Component::Normal(part)) if part == std::ffi::OsStr::new(campaign_id));
    if !belongs { return Err(KitabaError::Validation("registered asset path does not belong to campaign".into())); }
    Ok(asset_root.join(relative_path))
}

fn validate_image_asset(bytes: &[u8]) -> Result<(&'static str, &'static str), KitabaError> {
    if bytes.starts_with(b"\x89PNG\r\n\x1a\n") {
        return Ok(("image/png", "png"));
    }
    if bytes.starts_with(b"\xff\xd8\xff") {
        return Ok(("image/jpeg", "jpg"));
    }
    if bytes.len() >= 12 && &bytes[0..4] == b"RIFF" && &bytes[8..12] == b"WEBP" {
        return Ok(("image/webp", "webp"));
    }
    Err(KitabaError::Validation("Only PNG, JPEG and WebP image assets are accepted".into()))
}

pub fn list_assets(conn: &Connection, campaign_id: &str) -> Result<Vec<AssetSummary>, KitabaError> {
    let exists = conn.query_row("SELECT 1 FROM campaigns WHERE id=?1", [campaign_id], |r| r.get::<_, i64>(0)).optional()?;
    if exists.is_none() { return Err(KitabaError::CampaignNotFound); }
    let mut stmt = conn.prepare(
        "SELECT id,campaign_id,kind,relative_path,mime_type,sha256,created_at FROM assets WHERE campaign_id=?1 ORDER BY created_at DESC"
    )?;
    let rows = stmt.query_map([campaign_id], |r| Ok(AssetSummary {
        id: r.get(0)?, campaign_id: r.get(1)?, kind: r.get(2)?, relative_path: r.get(3)?,
        mime_type: r.get(4)?, sha256: r.get(5)?, created_at: r.get(6)?,
    }))?;
    Ok(rows.collect::<Result<Vec<_>, _>>()?)
}

pub fn import_asset(conn: &Connection, campaign_id: &str, kind: &str, input_path: &std::path::Path, asset_root: &std::path::Path) -> Result<AssetSummary, KitabaError> {
    if !matches!(kind, "world_map" | "player_portrait" | "npc_portrait" | "other_image") {
        return Err(KitabaError::Validation(format!("Unsupported asset kind: {kind}")));
    }
    let exists = conn.query_row("SELECT 1 FROM campaigns WHERE id=?1", [campaign_id], |r| r.get::<_, i64>(0)).optional()?;
    if exists.is_none() { return Err(KitabaError::CampaignNotFound); }
    let meta = std::fs::metadata(input_path)?;
    if !meta.is_file() { return Err(KitabaError::Validation("Asset path is not a file".into())); }
    if meta.len() > 25 * 1024 * 1024 { return Err(KitabaError::Validation("Asset file is too large".into())); }
    let bytes = std::fs::read(input_path)?;
    let (mime, ext) = validate_image_asset(&bytes)?;
    let asset_id = Uuid::new_v4().to_string();
    let relative_path = format!("{campaign_id}/{asset_id}.{ext}");
    let target = asset_root.join(&relative_path);
    if let Some(parent) = target.parent() { std::fs::create_dir_all(parent)?; }
    std::fs::write(&target, &bytes)?;
    let digest = hex::encode(Sha256::digest(&bytes));
    let now = Utc::now().to_rfc3339();

    let old_paths: Vec<String> = if matches!(kind, "world_map" | "player_portrait") {
        let mut stmt = conn.prepare("SELECT relative_path FROM assets WHERE campaign_id=?1 AND kind=?2")?;
        let rows = stmt.query_map(params![campaign_id, kind], |r| r.get(0))?.collect::<Result<Vec<String>, _>>()?;
        rows
    } else { Vec::new() };

    let tx = conn.unchecked_transaction()?;
    let result = (|| -> Result<(), KitabaError> {
        if matches!(kind, "world_map" | "player_portrait") {
            tx.execute("DELETE FROM assets WHERE campaign_id=?1 AND kind=?2", params![campaign_id, kind])?;
        }
        tx.execute(
            "INSERT INTO assets(id,campaign_id,kind,relative_path,mime_type,sha256,created_at) VALUES (?1,?2,?3,?4,?5,?6,?7)",
            params![asset_id, campaign_id, kind, relative_path, mime, digest, now],
        )?;
        let timeline_id: String = tx.query_row("SELECT current_timeline_id FROM campaigns WHERE id=?1", [campaign_id], |r| r.get(0))?;
        audit(&tx, Some(campaign_id), Some(&timeline_id), "asset_imported", &format!("Imported {kind} asset"), json!({"asset_id": asset_id, "kind": kind}))?;
        Ok(())
    })();
    if let Err(err) = result {
        let _ = std::fs::remove_file(&target);
        return Err(err);
    }
    if let Err(err) = tx.commit() {
        let _ = std::fs::remove_file(&target);
        return Err(err.into());
    }
    for old in old_paths {
        if let Ok(old_path) = managed_asset_path(asset_root, campaign_id, &old) {
            if old_path != target { let _ = std::fs::remove_file(old_path); }
        }
    }
    Ok(AssetSummary { id: asset_id, campaign_id: campaign_id.to_owned(), kind: kind.to_owned(), relative_path, mime_type: Some(mime.to_owned()), sha256: Some(digest), created_at: now })
}

pub fn read_asset_data_url(conn: &Connection, campaign_id: &str, asset_id: &str, asset_root: &std::path::Path) -> Result<String, KitabaError> {
    let row: Option<(String, Option<String>, Option<String>)> = conn.query_row(
        "SELECT relative_path,mime_type,sha256 FROM assets WHERE campaign_id=?1 AND id=?2",
        params![campaign_id, asset_id], |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?))
    ).optional()?;
    let (relative, mime, expected_hash) = row.ok_or_else(|| KitabaError::Validation("Unknown asset".into()))?;
    let path = managed_asset_path(asset_root, campaign_id, &relative)?;
    let bytes = std::fs::read(path)?;
    if bytes.len() > 25 * 1024 * 1024 { return Err(KitabaError::Validation("Asset file is too large".into())); }
    let digest = hex::encode(Sha256::digest(&bytes));
    if let Some(expected) = expected_hash {
        if digest != expected { return Err(KitabaError::Validation("Asset checksum mismatch".into())); }
    }
    let mime = mime.unwrap_or_else(|| "application/octet-stream".into());
    let encoded = base64::engine::general_purpose::STANDARD.encode(bytes);
    Ok(format!("data:{mime};base64,{encoded}"))
}

fn validate_entity_type(value: &str) -> bool {
    let mut chars = value.chars();
    match chars.next() {
        Some(c) if c.is_ascii_lowercase() => {}
        _ => return false,
    }
    value.len() >= 2 && value.len() <= 64 && chars.all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '_')
}

fn validate_operation(op: &Operation, player_scope: bool) -> Result<(), KitabaError> {
    if !validate_entity_type(&op.entity_type) {
        return Err(KitabaError::Validation(format!("invalid entity_type {}", op.entity_type)));
    }
    if player_scope && op.entity_type.starts_with("gm_") {
        return Err(KitabaError::Validation("player operation cannot target gm_* entity_type".into()));
    }
    if Uuid::parse_str(&op.entity_id).is_err() {
        return Err(KitabaError::Validation("entity_id must be UUID".into()));
    }
    match op.op.as_str() {
        "create" | "replace" | "patch" => {
            if !op.data.as_ref().map(Value::is_object).unwrap_or(false) {
                return Err(KitabaError::Validation(format!("{} requires object data", op.op)));
            }
        }
        "archive" => {}
        "reveal" => {
            if !player_scope { return Err(KitabaError::Validation("reveal is forbidden in gm_operations".into())); }
            if !op.data.as_ref().map(Value::is_object).unwrap_or(false) {
                return Err(KitabaError::Validation("reveal requires object data".into()));
            }
            let source = op.source_gm_entity_id.as_deref().ok_or_else(|| KitabaError::Validation("reveal requires source_gm_entity_id".into()))?;
            if Uuid::parse_str(source).is_err() { return Err(KitabaError::Validation("source_gm_entity_id must be UUID".into())); }
        }
        _ => return Err(KitabaError::Validation(format!("unsupported operation {}", op.op))),
    }
    if let Some(version) = op.expected_entity_version {
        if version < 1 { return Err(KitabaError::Validation("expected_entity_version must be >= 1".into())); }
    }
    if let Some(protection) = op.protection.as_deref() {
        if !matches!(protection, "NORMAL" | "PROTECTED" | "IMMUTABLE") {
            return Err(KitabaError::Validation("invalid protection value".into()));
        }
    }
    if op.override_immutable == Some(true) && op.override_reason.as_deref().map(str::trim).filter(|s| !s.is_empty()).is_none() {
        return Err(KitabaError::Validation("override_immutable requires override_reason".into()));
    }
    Ok(())
}

fn validate_link_operation(op: &LinkOperation) -> Result<(), KitabaError> {
    if Uuid::parse_str(&op.link_id).is_err() { return Err(KitabaError::Validation("link_id must be UUID".into())); }
    match op.op.as_str() {
        "unlink" => Ok(()),
        "link" => {
            let from = op.from_entity_id.as_deref().ok_or_else(|| KitabaError::Validation("link requires from_entity_id".into()))?;
            let to = op.to_entity_id.as_deref().ok_or_else(|| KitabaError::Validation("link requires to_entity_id".into()))?;
            if Uuid::parse_str(from).is_err() || Uuid::parse_str(to).is_err() { return Err(KitabaError::Validation("link entity IDs must be UUIDs".into())); }
            if op.link_type.as_deref().map(str::trim).filter(|s| !s.is_empty()).is_none() { return Err(KitabaError::Validation("link requires link_type".into())); }
            if let Some(data) = &op.data { if !data.is_object() { return Err(KitabaError::Validation("link data must be object".into())); } }
            Ok(())
        }
        _ => Err(KitabaError::Validation(format!("unsupported link operation {}", op.op))),
    }
}

fn validate_update(update: &KitabaUpdate) -> Result<(), KitabaError> {
    if update.format != "KITABA_UPDATE" { return Err(KitabaError::Validation("format must be KITABA_UPDATE".into())); }
    if update.protocol_version != 1 { return Err(KitabaError::Validation("unsupported protocol_version".into())); }
    if update.target_revision != update.base_revision + 1 { return Err(KitabaError::Validation("target_revision must equal base_revision + 1".into())); }
    if update.base_revision < 0 { return Err(KitabaError::Validation("base_revision must be >= 0".into())); }
    if Uuid::parse_str(&update.campaign_id).is_err() || Uuid::parse_str(&update.timeline_id).is_err() || Uuid::parse_str(&update.update_id).is_err() {
        return Err(KitabaError::Validation("campaign_id, timeline_id and update_id must be UUIDs".into()));
    }
    if let Some(game_time) = &update.game_time {
        if game_time.elapsed_minutes.is_some_and(|v| v < 0) { return Err(KitabaError::Validation("elapsed_minutes must be >= 0".into())); }
        if game_time.elapsed_minutes.is_some() && game_time.set.as_deref().map(str::trim).filter(|s| !s.is_empty()).is_none() {
            return Err(KitabaError::Validation("game_time.elapsed_minutes requires an explicit game_time.set; the Companion never computes calendar time autonomously".into()));
        }
        if game_time.set.as_deref().is_some_and(|s| s.trim().is_empty()) {
            return Err(KitabaError::Validation("game_time.set cannot be empty".into()));
        }
    }
    for notification in &update.notifications {
        if !matches!(notification.level.as_str(), "info" | "warning" | "success") {
            return Err(KitabaError::Validation("notification level must be info, warning or success".into()));
        }
        if notification.message.trim().is_empty() {
            return Err(KitabaError::Validation("notification message cannot be empty".into()));
        }
    }
    for op in &update.operations { validate_operation(op, true)?; }
    for op in &update.gm_operations { validate_operation(op, false)?; }
    for op in &update.link_operations { validate_link_operation(op)?; }
    for op in &update.gm_link_operations { validate_link_operation(op)?; }
    for entry in &update.journal_entries {
        let object = entry.as_object().ok_or_else(|| KitabaError::Validation("journal entry must be object".into()))?;
        let entity_type = object.get("entity_type").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("journal entry entity_type missing".into()))?;
        if !validate_entity_type(entity_type) { return Err(KitabaError::Validation("journal entry entity_type invalid".into())); }
        let entity_id = object.get("entity_id").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("journal entry entity_id missing".into()))?;
        if Uuid::parse_str(entity_id).is_err() { return Err(KitabaError::Validation("journal entry entity_id must be UUID".into())); }
        if !object.get("data").map(Value::is_object).unwrap_or(false) { return Err(KitabaError::Validation("journal entry data must be object".into())); }
    }
    if let Some(cp) = &update.checkpoint {
        if Uuid::parse_str(&cp.id).is_err() { return Err(KitabaError::Validation("checkpoint id must be UUID".into())); }
    }
    for resolution in &update.dead_timeline_resolutions {
        let obj = resolution.as_object().ok_or_else(|| KitabaError::Validation("dead timeline resolution must be object".into()))?;
        let id = obj.get("id").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("dead resolution id missing".into()))?;
        if Uuid::parse_str(id).is_err() { return Err(KitabaError::Validation("dead resolution id must be UUID".into())); }
        if let Some(cp) = obj.get("checkpoint_id").and_then(Value::as_str) { if Uuid::parse_str(cp).is_err() { return Err(KitabaError::Validation("dead resolution checkpoint_id must be UUID".into())); } }
        for key in ["state_fingerprint", "action_fingerprint"] {
            if obj.get(key).and_then(Value::as_str).map(str::trim).filter(|s| !s.is_empty()).is_none() { return Err(KitabaError::Validation(format!("dead resolution {key} missing"))); }
        }
        for key in ["context", "result", "consequences"] {
            if !obj.get(key).map(Value::is_object).unwrap_or(false) { return Err(KitabaError::Validation(format!("dead resolution {key} must be object"))); }
        }
    }
    if let Some(death) = &update.death {
        let occurred = death.get("occurred").and_then(Value::as_bool);
        if occurred != Some(true) { return Err(KitabaError::Validation("death.occurred must be true when death is present".into())); }
    }
    Ok(())
}

pub fn preview_update(conn: &Connection, raw: &str) -> Result<UpdatePreview, KitabaError> {
    let update: KitabaUpdate = serde_json::from_str(raw)?;
    validate_update(&update)?;
    let campaign = conn.query_row(
        "SELECT current_revision,current_timeline_id,death_pending FROM campaigns WHERE id=?1",
        [&update.campaign_id],
        |r| Ok((r.get::<_, i64>(0)?, r.get::<_, String>(1)?, r.get::<_, i64>(2)?)),
    ).optional()?.ok_or(KitabaError::CampaignNotFound)?;
    if campaign.2 != 0 { return Err(KitabaError::Validation("Campaign is awaiting authorized death rollback".into())); }
    if conn.query_row("SELECT 1 FROM applied_updates WHERE update_id=?1", [&update.update_id], |r| r.get::<_, i64>(0)).optional()?.is_some() {
        return Err(KitabaError::DuplicateUpdate);
    }
    if campaign.0 != update.base_revision {
        return Err(KitabaError::RevisionConflict { local: campaign.0, incoming: update.base_revision });
    }
    if campaign.1 != update.timeline_id { return Err(KitabaError::TimelineConflict); }
    let player_changes = update.operations.iter().take(12)
        .map(|op| format!("{} · {}", op.op, op.entity_type))
        .collect();
    Ok(UpdatePreview {
        campaign_id: update.campaign_id,
        timeline_id: update.timeline_id,
        update_id: update.update_id,
        base_revision: update.base_revision,
        target_revision: update.target_revision,
        player_operation_count: update.operations.len(),
        gm_operation_count: update.gm_operations.len(),
        player_link_operation_count: update.link_operations.len(),
        gm_link_operation_count: update.gm_link_operations.len(),
        journal_entry_count: update.journal_entries.len(),
        notification_count: update.notifications.len(),
        dead_resolution_count: update.dead_timeline_resolutions.len(),
        creates_checkpoint: update.checkpoint.is_some(),
        marks_death: update.death.is_some(),
        player_changes,
    })
}

pub fn apply_update(conn: &mut Connection, raw: &str) -> Result<ImportResult, KitabaError> {
    let update: KitabaUpdate = serde_json::from_str(raw)?;
    validate_update(&update)?;
    let player_count = update.operations.len();
    let gm_count = update.gm_operations.len();
    let payload_hash = hex::encode(Sha256::digest(raw.as_bytes()));
    let tx = conn.transaction()?;

    let campaign = tx.query_row(
        "SELECT current_revision,current_timeline_id,game_time,death_pending FROM campaigns WHERE id=?1",
        [&update.campaign_id],
        |r| Ok((r.get::<_, i64>(0)?, r.get::<_, String>(1)?, r.get::<_, Option<String>>(2)?, r.get::<_, i64>(3)?)),
    ).optional()?.ok_or(KitabaError::CampaignNotFound)?;

    if campaign.3 != 0 { return Err(KitabaError::Validation("Campaign is awaiting authorized death rollback".into())); }
    if tx.query_row("SELECT 1 FROM applied_updates WHERE update_id=?1", [&update.update_id], |r| r.get::<_, i64>(0)).optional()?.is_some() {
        return Err(KitabaError::DuplicateUpdate);
    }
    if campaign.0 != update.base_revision {
        return Err(KitabaError::RevisionConflict { local: campaign.0, incoming: update.base_revision });
    }
    if campaign.1 != update.timeline_id { return Err(KitabaError::TimelineConflict); }

    for op in &update.operations { apply_operation(&tx, &update.campaign_id, &update.update_id, "PLAYER", op)?; }
    for op in &update.gm_operations { apply_operation(&tx, &update.campaign_id, &update.update_id, "GM", op)?; }
    for op in &update.link_operations { apply_link_operation(&tx, &update.campaign_id, &update.update_id, "PLAYER", op)?; }
    for op in &update.gm_link_operations { apply_link_operation(&tx, &update.campaign_id, &update.update_id, "GM", op)?; }
    for entry in &update.journal_entries {
        let entity_type = entry.get("entity_type").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("journal entry entity_type missing".into()))?;
        let entity_id = entry.get("entity_id").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("journal entry entity_id missing".into()))?;
        let data = entry.get("data").cloned().ok_or_else(|| KitabaError::Validation("journal entry data missing".into()))?;
        let op = Operation { op: "create".into(), entity_type: entity_type.into(), entity_id: entity_id.into(), expected_entity_version: None, data: Some(data), source_gm_entity_id: None, protection: None, override_immutable: None, override_reason: None };
        apply_operation(&tx, &update.campaign_id, &update.update_id, "PLAYER", &op)?;
    }
    for resolution in &update.dead_timeline_resolutions {
        let id = resolution.get("id").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("dead resolution id missing".into()))?;
        let checkpoint_id = resolution.get("checkpoint_id").and_then(Value::as_str);
        let state_fingerprint = resolution.get("state_fingerprint").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("dead resolution state_fingerprint missing".into()))?;
        let action_fingerprint = resolution.get("action_fingerprint").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("dead resolution action_fingerprint missing".into()))?;
        let context = resolution.get("context").cloned().unwrap_or_else(|| json!({}));
        let result = resolution.get("result").cloned().unwrap_or_else(|| json!({}));
        let consequences = resolution.get("consequences").cloned().unwrap_or_else(|| json!({}));
        let notes = resolution.get("notes").and_then(Value::as_str);
        tx.execute(
            "INSERT INTO dead_timeline_resolutions(id,campaign_id,source_timeline_id,checkpoint_id,state_fingerprint,action_fingerprint,context_json,result_json,consequences_json,source_update_id,notes,created_at) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12)",
            params![id, update.campaign_id, update.timeline_id, checkpoint_id, state_fingerprint, action_fingerprint, canonical_json(&context)?, canonical_json(&result)?, canonical_json(&consequences)?, update.update_id, notes, Utc::now().to_rfc3339()],
        )?;
    }

    let new_game_time = update.game_time.as_ref().and_then(|g| g.set.clone()).or(campaign.2);
    let now = Utc::now().to_rfc3339();
    tx.execute(
        "INSERT INTO applied_updates(update_id,campaign_id,timeline_id,base_revision,target_revision,payload_sha256,applied_at) VALUES (?1,?2,?3,?4,?5,?6,?7)",
        params![update.update_id, update.campaign_id, update.timeline_id, update.base_revision, update.target_revision, payload_hash, now],
    )?;
    let death_pending = update.death.as_ref().and_then(|d| d.get("occurred")).and_then(Value::as_bool).unwrap_or(false);
    let death_summary = if death_pending { update.death.as_ref().and_then(|d| d.get("summary")).and_then(Value::as_str) } else { None };
    tx.execute(
        "UPDATE campaigns SET current_revision=?1,game_time=?2,last_update_id=?3,updated_at=?4,death_pending=?5,death_summary=?6 WHERE id=?7",
        params![update.target_revision, new_game_time, update.update_id, now, if death_pending {1} else {0}, death_summary, update.campaign_id],
    )?;

    if let Some(cp) = &update.checkpoint {
        let snapshot = snapshot_state(&tx, &update.campaign_id)?;
        let snapshot_raw = canonical_json(&snapshot)?;
        let hash = hex::encode(Sha256::digest(snapshot_raw.as_bytes()));
        tx.execute(
            "INSERT INTO rest_points(id,campaign_id,timeline_id,source_update_id,snapshot_revision,game_time,location,description,snapshot_json,snapshot_sha256,created_at) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11)",
            params![cp.id, update.campaign_id, update.timeline_id, update.update_id, update.target_revision, new_game_time, cp.location, cp.description, snapshot_raw, hash, now],
        )?;
    }

    audit(&tx, Some(&update.campaign_id), Some(&update.timeline_id), "kitaba_update_applied", "KITABA_UPDATE applied", json!({"update_id": update.update_id, "gm_operation_count": gm_count, "journal_entry_count": update.journal_entries.len(), "notification_count": update.notifications.len(), "death_flag": update.death.is_some()}))?;
    tx.commit()?;
    Ok(ImportResult {
        revision: update.target_revision,
        timeline_id: update.timeline_id,
        update_id: update.update_id,
        player_operation_count: player_count,
        gm_operation_count: gm_count,
        notifications: update.notifications,
    })
}

fn apply_operation(tx: &Transaction<'_>, campaign_id: &str, update_id: &str, visibility: &str, op: &Operation) -> Result<(), KitabaError> {
    let row = tx.query_row(
        "SELECT entity_type,visibility,entity_version,data_json,protection FROM entity_documents WHERE campaign_id=?1 AND id=?2",
        params![campaign_id, op.entity_id],
        |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?, r.get::<_, i64>(2)?, r.get::<_, String>(3)?, r.get::<_, String>(4)?)),
    ).optional()?;
    let now = Utc::now().to_rfc3339();

    match op.op.as_str() {
        "create" => {
            if row.is_some() { return Err(KitabaError::EntityConflict("entity already exists".into())); }
            let data = op.data.as_ref().ok_or_else(|| KitabaError::Validation("create requires data".into()))?;
            let protection = op.protection.as_deref().unwrap_or("NORMAL");
            tx.execute(
                "INSERT INTO entity_documents(id,campaign_id,entity_type,visibility,entity_version,data_json,protection,created_by_update_id,updated_by_update_id,created_at,updated_at) VALUES (?1,?2,?3,?4,1,?5,?6,?7,?7,?8,?8)",
                params![op.entity_id, campaign_id, op.entity_type, visibility, canonical_json(data)?, protection, update_id, now],
            )?;
        }
        "reveal" => {
            if visibility != "PLAYER" { return Err(KitabaError::EntityConflict("reveal is player-scope only".into())); }
            let source = op.source_gm_entity_id.as_ref().ok_or_else(|| KitabaError::Validation("reveal requires source_gm_entity_id".into()))?;
            let exists = tx.query_row(
                "SELECT 1 FROM entity_documents WHERE campaign_id=?1 AND id=?2 AND visibility='GM' AND archived=0",
                params![campaign_id, source], |r| r.get::<_, i64>(0)
            ).optional()?.is_some();
            if !exists { return Err(KitabaError::EntityConflict("GM reveal source not found".into())); }
            let data = op.data.as_ref().ok_or_else(|| KitabaError::Validation("reveal requires data".into()))?;
            if let Some(existing) = row {
                ensure_scope_and_version(&existing, visibility, &op.entity_type, op.expected_entity_version)?;
                let merged = merge_json(&serde_json::from_str(&existing.3)?, data);
                tx.execute("UPDATE entity_documents SET data_json=?1,entity_version=entity_version+1,updated_by_update_id=?2,updated_at=?3 WHERE campaign_id=?4 AND id=?5",
                    params![canonical_json(&merged)?, update_id, now, campaign_id, op.entity_id])?;
            } else {
                tx.execute("INSERT INTO entity_documents(id,campaign_id,entity_type,visibility,entity_version,data_json,created_by_update_id,updated_by_update_id,created_at,updated_at) VALUES (?1,?2,?3,'PLAYER',1,?4,?5,?5,?6,?6)",
                    params![op.entity_id, campaign_id, op.entity_type, canonical_json(data)?, update_id, now])?;
            }
        }
        "replace" | "patch" | "archive" => {
            let existing = row.ok_or_else(|| KitabaError::EntityConflict("entity not found".into()))?;
            if existing.4 == "IMMUTABLE" {
                let allowed = op.override_immutable == Some(true) && op.override_reason.as_deref().map(str::trim).filter(|s| !s.is_empty()).is_some();
                if !allowed { return Err(KitabaError::EntityConflict("immutable entity requires explicit override with reason".into())); }
            }
            if existing.4 == "PROTECTED" && op.expected_entity_version.is_none() {
                return Err(KitabaError::EntityConflict("protected entity requires expected_entity_version".into()));
            }
            ensure_scope_and_version(&existing, visibility, &op.entity_type, op.expected_entity_version)?;
            match op.op.as_str() {
                "replace" => {
                    let data = op.data.as_ref().ok_or_else(|| KitabaError::Validation("replace requires data".into()))?;
                    let next_protection = op.protection.as_deref().unwrap_or(&existing.4);
                    tx.execute("UPDATE entity_documents SET data_json=?1,protection=?2,entity_version=entity_version+1,archived=0,updated_by_update_id=?3,updated_at=?4 WHERE campaign_id=?5 AND id=?6",
                        params![canonical_json(data)?, next_protection, update_id, now, campaign_id, op.entity_id])?;
                }
                "patch" => {
                    let data = op.data.as_ref().ok_or_else(|| KitabaError::Validation("patch requires data".into()))?;
                    let merged = merge_json(&serde_json::from_str(&existing.3)?, data);
                    let next_protection = op.protection.as_deref().unwrap_or(&existing.4);
                    tx.execute("UPDATE entity_documents SET data_json=?1,protection=?2,entity_version=entity_version+1,updated_by_update_id=?3,updated_at=?4 WHERE campaign_id=?5 AND id=?6",
                        params![canonical_json(&merged)?, next_protection, update_id, now, campaign_id, op.entity_id])?;
                }
                _ => {
                    tx.execute("UPDATE entity_documents SET archived=1,entity_version=entity_version+1,updated_by_update_id=?1,updated_at=?2 WHERE campaign_id=?3 AND id=?4",
                        params![update_id, now, campaign_id, op.entity_id])?;
                }
            }
        }
        _ => return Err(KitabaError::Validation(format!("unsupported operation {}", op.op))),
    }
    Ok(())
}

fn apply_link_operation(tx: &Transaction<'_>, campaign_id: &str, update_id: &str, visibility: &str, op: &LinkOperation) -> Result<(), KitabaError> {
    if Uuid::parse_str(&op.link_id).is_err() { return Err(KitabaError::Validation("link_id must be UUID".into())); }
    let now = Utc::now().to_rfc3339();
    let existing = tx.query_row(
        "SELECT visibility FROM entity_links WHERE campaign_id=?1 AND id=?2",
        params![campaign_id, op.link_id], |r| r.get::<_, String>(0)
    ).optional()?;
    match op.op.as_str() {
        "unlink" => {
            let scope = existing.ok_or_else(|| KitabaError::EntityConflict("link not found".into()))?;
            if scope != visibility { return Err(KitabaError::EntityConflict("link visibility mismatch".into())); }
            tx.execute(
                "UPDATE entity_links SET archived=1,updated_by_update_id=?1,updated_at=?2 WHERE campaign_id=?3 AND id=?4",
                params![update_id, now, campaign_id, op.link_id],
            )?;
        }
        "link" => {
            if existing.is_some() { return Err(KitabaError::EntityConflict("link already exists".into())); }
            let from = op.from_entity_id.as_deref().ok_or_else(|| KitabaError::Validation("link requires from_entity_id".into()))?;
            let to = op.to_entity_id.as_deref().ok_or_else(|| KitabaError::Validation("link requires to_entity_id".into()))?;
            let link_type = op.link_type.as_deref().ok_or_else(|| KitabaError::Validation("link requires link_type".into()))?;
            if Uuid::parse_str(from).is_err() || Uuid::parse_str(to).is_err() { return Err(KitabaError::Validation("link entity IDs must be UUIDs".into())); }
            let mut stmt = tx.prepare("SELECT id,visibility FROM entity_documents WHERE campaign_id=?1 AND id IN (?2,?3) AND archived=0")?;
            let refs = stmt.query_map(params![campaign_id, from, to], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))?.collect::<Result<Vec<_>, _>>()?;
            let expected = if from == to { 1 } else { 2 };
            if refs.len() != expected { return Err(KitabaError::EntityConflict("link references unknown entity".into())); }
            if visibility == "PLAYER" && refs.iter().any(|(_, v)| v != "PLAYER") {
                return Err(KitabaError::EntityConflict("player link cannot reference GM-only entity".into()));
            }
            tx.execute(
                "INSERT INTO entity_links(id,campaign_id,from_entity_id,to_entity_id,link_type,visibility,data_json,archived,created_by_update_id,updated_by_update_id,created_at,updated_at) VALUES (?1,?2,?3,?4,?5,?6,?7,0,?8,?8,?9,?9)",
                params![op.link_id, campaign_id, from, to, link_type, visibility, canonical_json(&op.data.clone().unwrap_or_else(|| json!({})))?, update_id, now],
            )?;
        }
        _ => return Err(KitabaError::Validation(format!("unsupported link operation {}", op.op))),
    }
    Ok(())
}

fn ensure_scope_and_version(existing: &(String,String,i64,String,String), visibility: &str, entity_type: &str, expected: Option<i64>) -> Result<(), KitabaError> {
    if existing.0 != entity_type { return Err(KitabaError::EntityConflict("entity_type cannot change".into())); }
    if existing.1 != visibility { return Err(KitabaError::EntityConflict("visibility scope mismatch".into())); }
    if let Some(v) = expected { if existing.2 != v { return Err(KitabaError::EntityConflict(format!("entity version mismatch: local={}, expected={}", existing.2, v))); } }
    Ok(())
}

fn merge_json(base: &Value, patch: &Value) -> Value {
    match (base, patch) {
        (Value::Object(base_map), Value::Object(patch_map)) => {
            let mut out: Map<String, Value> = base_map.clone();
            for (k, v) in patch_map {
                if v.is_null() { out.remove(k); }
                else if let Some(old) = out.get(k) { out.insert(k.clone(), merge_json(old, v)); }
                else { out.insert(k.clone(), v.clone()); }
            }
            Value::Object(out)
        }
        (_, p) => p.clone(),
    }
}

fn canonical_json(value: &Value) -> Result<String, KitabaError> {
    Ok(serde_json::to_string(value)?)
}

fn snapshot_state(tx: &Transaction<'_>, campaign_id: &str) -> Result<Value, KitabaError> {
    let game_time: Option<String> = tx.query_row("SELECT game_time FROM campaigns WHERE id=?1", [campaign_id], |r| r.get(0))?;
    let mut stmt = tx.prepare("SELECT id,entity_type,visibility,entity_version,data_json,protection FROM entity_documents WHERE campaign_id=?1 AND archived=0 ORDER BY entity_type,id")?;
    let rows = stmt.query_map([campaign_id], |r| Ok(json!({
        "id": r.get::<_, String>(0)?,
        "entity_type": r.get::<_, String>(1)?,
        "visibility": r.get::<_, String>(2)?,
        "entity_version": r.get::<_, i64>(3)?,
        "data": serde_json::from_str::<Value>(&r.get::<_, String>(4)?).unwrap_or(Value::Null),
        "protection": r.get::<_, String>(5)?
    })))?.collect::<Result<Vec<_>, _>>()?;
    let mut links_stmt = tx.prepare("SELECT id,from_entity_id,to_entity_id,link_type,visibility,data_json FROM entity_links WHERE campaign_id=?1 AND archived=0 ORDER BY id")?;
    let links = links_stmt.query_map([campaign_id], |r| Ok(json!({
        "id": r.get::<_, String>(0)?,
        "from_entity_id": r.get::<_, String>(1)?,
        "to_entity_id": r.get::<_, String>(2)?,
        "link_type": r.get::<_, String>(3)?,
        "visibility": r.get::<_, String>(4)?,
        "data_json": r.get::<_, String>(5)?
    })))?.collect::<Result<Vec<_>, _>>()?;
    Ok(json!({"game_time": game_time, "entities": rows, "links": links}))
}

pub fn export_context(conn: &Connection, campaign_id: &str, mode: &str) -> Result<String, KitabaError> {
    let include_gm = match mode { "PLAYER" => false, "GM_FULL" => true, _ => return Err(KitabaError::Validation("mode must be PLAYER or GM_FULL".into())) };
    let c = conn.query_row(
        "SELECT current_revision,current_timeline_id,game_time,last_update_id,death_pending,death_summary,name FROM campaigns WHERE id=?1",
        [campaign_id], |r| Ok((r.get::<_, i64>(0)?, r.get::<_, String>(1)?, r.get::<_, Option<String>>(2)?, r.get::<_, Option<String>>(3)?, r.get::<_, i64>(4)?, r.get::<_, Option<String>>(5)?, r.get::<_, String>(6)?))
    ).optional()?.ok_or(KitabaError::CampaignNotFound)?;
    let timeline_meta = conn.query_row(
        "SELECT parent_timeline_id,restored_from_rest_point_id FROM timelines WHERE id=?1", [&c.1],
        |r| Ok((r.get::<_, Option<String>>(0)?, r.get::<_, Option<String>>(1)?))
    )?;

    let sql = if include_gm {
        "SELECT id,entity_type,visibility,entity_version,data_json,protection FROM entity_documents WHERE campaign_id=?1 AND archived=0 ORDER BY entity_type,id"
    } else {
        "SELECT id,entity_type,visibility,entity_version,data_json,protection FROM entity_documents WHERE campaign_id=?1 AND archived=0 AND visibility='PLAYER' ORDER BY entity_type,id"
    };
    let mut stmt = conn.prepare(sql)?;
    let entities = stmt.query_map([campaign_id], |r| Ok(json!({
        "id": r.get::<_, String>(0)?, "entity_type": r.get::<_, String>(1)?, "visibility": r.get::<_, String>(2)?,
        "entity_version": r.get::<_, i64>(3)?, "data": serde_json::from_str::<Value>(&r.get::<_, String>(4)?).unwrap_or(Value::Null),
        "protection": r.get::<_, String>(5)?
    })))?.collect::<Result<Vec<_>, _>>()?;

    let mut dead_timelines: Vec<Value> = Vec::new();
    let mut dead_resolutions: Vec<Value> = Vec::new();
    if include_gm {
        let mut dt = conn.prepare("SELECT timeline_id,died_at_revision,death_summary,state_snapshot_json,rolled_back_to_rest_point_id,created_at FROM dead_timelines WHERE campaign_id=?1 ORDER BY created_at")?;
        dead_timelines = dt.query_map([campaign_id], |r| Ok(json!({
            "timeline_id": r.get::<_, String>(0)?,
            "died_at_revision": r.get::<_, i64>(1)?,
            "death_summary": r.get::<_, Option<String>>(2)?,
            "state_snapshot": serde_json::from_str::<Value>(&r.get::<_, String>(3)?).unwrap_or_else(|_| json!({})),
            "rolled_back_to_rest_point_id": r.get::<_, Option<String>>(4)?,
            "created_at": r.get::<_, String>(5)?
        })))?.collect::<Result<Vec<_>, _>>()?;
        let mut s = conn.prepare("SELECT id,source_timeline_id,checkpoint_id,state_fingerprint,action_fingerprint,context_json,result_json,consequences_json,source_update_id,notes,created_at FROM dead_timeline_resolutions WHERE campaign_id=?1 ORDER BY created_at")?;
        dead_resolutions = s.query_map([campaign_id], |r| Ok(json!({
            "id": r.get::<_, String>(0)?, "source_timeline_id": r.get::<_, String>(1)?, "checkpoint_id": r.get::<_, Option<String>>(2)?,
            "state_fingerprint": r.get::<_, String>(3)?, "action_fingerprint": r.get::<_, String>(4)?,
            "context": serde_json::from_str::<Value>(&r.get::<_, String>(5)?).unwrap_or(Value::Null),
            "result": serde_json::from_str::<Value>(&r.get::<_, String>(6)?).unwrap_or(Value::Null),
            "consequences": serde_json::from_str::<Value>(&r.get::<_, String>(7)?).unwrap_or(Value::Null),
            "source_update_id": r.get::<_, Option<String>>(8)?, "notes": r.get::<_, Option<String>>(9)?, "created_at": r.get::<_, String>(10)?
        })))?.collect::<Result<Vec<_>, _>>()?;
    }

    let last_rest_point: Option<Value> = conn.query_row(
        "SELECT id,snapshot_revision,game_time,location,description,created_at FROM rest_points WHERE campaign_id=?1 AND invalidated_at IS NULL ORDER BY snapshot_revision DESC, created_at DESC, rowid DESC LIMIT 1",
        [campaign_id], |r| Ok(json!({
            "id": r.get::<_, String>(0)?, "snapshot_revision": r.get::<_, i64>(1)?, "game_time": r.get::<_, Option<String>>(2)?,
            "location": r.get::<_, Option<String>>(3)?, "description": r.get::<_, String>(4)?, "created_at": r.get::<_, String>(5)?
        }))
    ).optional()?;
    let canon_facts: Vec<Value> = if include_gm {
        entities.iter().filter(|e| e.get("entity_type").and_then(Value::as_str) == Some("canon_fact") && e.get("visibility").and_then(Value::as_str) == Some("GM")).cloned().collect()
    } else { Vec::new() };
    let links_sql = if include_gm {
        "SELECT id,from_entity_id,to_entity_id,link_type,visibility,data_json FROM entity_links WHERE campaign_id=?1 AND archived=0 ORDER BY id"
    } else {
        "SELECT id,from_entity_id,to_entity_id,link_type,visibility,data_json FROM entity_links WHERE campaign_id=?1 AND archived=0 AND visibility='PLAYER' ORDER BY id"
    };
    let mut links_stmt = conn.prepare(links_sql)?;
    let links = links_stmt.query_map([campaign_id], |r| Ok(json!({
        "id": r.get::<_, String>(0)?, "from_entity_id": r.get::<_, String>(1)?, "to_entity_id": r.get::<_, String>(2)?,
        "link_type": r.get::<_, String>(3)?, "visibility": r.get::<_, String>(4)?, "data": serde_json::from_str::<Value>(&r.get::<_, String>(5)?).unwrap_or_else(|_| json!({}))
    })))?.collect::<Result<Vec<_>, _>>()?;
    let export_state = json!({
        "revision": c.0,
        "timeline_id": c.1,
        "game_time": c.2,
        "entities": entities,
        "links": links,
    });
    let export_state_sha256 = hex::encode(Sha256::digest(canonical_json(&export_state)?.as_bytes()));
    let entities = export_state.get("entities").cloned().unwrap_or_else(|| json!([]));
    let links = export_state.get("links").cloned().unwrap_or_else(|| json!([]));

    let context = json!({
        "format": "KITABA_CONTEXT", "protocol_version": 1, "mode": mode, "campaign_id": campaign_id,
        "campaign_name": c.6,
        "campaign_revision": c.0, "timeline_id": c.1, "exported_at": Utc::now().to_rfc3339(), "game_time": c.2,
        "death_pending": c.4 != 0, "death_summary": c.5,
        "entities": entities, "links": links, "last_rest_point": last_rest_point,
        "dead_timelines": dead_timelines,
        "dead_timeline_resolutions": dead_resolutions,
        "canon_facts": canon_facts,
        "companion_contract": {
            "update_format": "KITABA_UPDATE",
            "update_protocol_version": 1,
            "next_base_revision": c.0,
            "next_target_revision": c.0 + 1,
            "required_timeline_id": c.1,
            "supported_operations": ["create", "replace", "patch", "archive", "reveal"],
            "ui_entity_types": {
                "character": ["player_character", "characteristic", "specialized_stat", "injury", "status_effect", "awakening"],
                "skills": ["skill", "mastery"],
                "magic": ["magic", "spell", "affinity", "invocation", "contract", "enchantment", "known_aptitude"],
                "inventory": ["item", "inventory_item", "equipment", "wallet", "currency", "debt"],
                "relations": ["npc", "relationship", "reputation"],
                "journal": ["journal_entry"],
                "missions": ["mission", "quest"],
                "knowledge": ["knowledge", "rumor", "belief"],
                "world": ["faction", "organization", "settlement", "state", "market", "economy_state", "conflict", "world_event", "environment_state", "resource_state", "infrastructure", "law", "political_state"],
                "map": ["place", "map_marker", "map", "current_location", "settlement", "state", "region", "route", "dungeon"],
                "timeline": ["timeline_event", "historical_event"],
                "adventurer_card": ["adventurer_card", "evaluation", "certification"],
                "gm": ["canon_fact"]
            },
            "rules": [
                "Use campaign_id, required_timeline_id and next_base_revision exactly as exported.",
                "target_revision must equal base_revision + 1.",
                "Use operations for player-visible knowledge and gm_operations for hidden canonical truth.",
                "Never expose hidden truth by copying it into a player operation; reveal only the partial information the character actually learns.",
                "The Companion never advances time itself. When time advances, provide an explicit game_time.set; elapsed_minutes is informational and requires set.",
                "Create checkpoint only after a sufficiently safe completed long rest validated by the GM.",
                "Set death.occurred=true only for confirmed player death. After death, no further update is accepted until Companion rollback.",
                "Store repeated dead-timeline material resolutions in dead_timeline_resolutions with stable fingerprints.",
                "Persist durable campaign-world changes, including off-screen changes unknown to the player, as entities. Keep unknown world truth in GM scope until legitimately revealed.",
                "For a fresh campaign with no player_character, complete character creation and starting-world anchoring before the first narrated gameplay scene.",
                "Never assume the human player knows developer or world terminology. Introduce unfamiliar concepts diegetically and contextually when first encountered, even if the character would regard them as ordinary.",
                "The initial campaign update must persist the player_character, immediate known setting, relevant close relations and baseline knowledge actually possessed by the character before gameplay begins.",
                "Do not generate or import a character/PNJ portrait until the represented person's appearance has been canonically fixed; an illustration never creates canon by itself.",
                "Prefer frequent playable beats over long passive narration: use a few salient sensory details, then return control to the player; action and dialogue beats should be especially concise.",
                "When player input is brief or underspecified, treat it as intent and render the protagonist's execution with a few concrete physical, sensory and emotional details consistent with established personality and current state. Do not require micromanagement; never invent a materially different choice, strategic commitment, consent, hidden knowledge or fixed inner decision. Keep the embellishment concise and return control quickly.",
                "The player controls only the protagonist's attempted actions, speech, intentions and voluntary thoughts. NPC reactions, action outcomes and external events remain GM-controlled even if the player writes a desired reaction.",
                "Treat any player wording that states a success or world outcome as an attempted action, not as an automatic fact. Resolve uncertainty from established abilities, knowledge, tools, injuries, opposition, environment and stakes; when a meaningful uncertain outcome exists, perform a single hidden dice-like or equivalent random draw calibrated to the real odds, then allow failure, partial success, complications or success as warranted. Do not expose the number by default, do not reroll merely because the result is inconvenient, and do not roll for trivial uncontested actions.",
                "When the player gives a terse action, enrich its presentation with concise physical detail, sensory context and character-consistent emotional shading so the scene feels alive, but do not invent a materially different intention, irreversible choice or successful outcome. If added detail would change risk or intent, keep the expansion minimal or ask for clarification.",
                "When a player-known durable place becomes sufficiently localizable, persist stable normalized map coordinates x/y in [0,1] plus appropriate location_precision; never reveal secret GM geography through PLAYER map data.",
                "Persist a stable textual visual_identity for important characters before or alongside reference imagery. Later state variants and multi-character scenes must preserve that identity; text canon always overrides an image.",
                "Treat adaptive music as scene-level ambience: change music_state only at meaningful scene or emotional transitions, prefer long instrumental ambience, and never claim playback unless a compatible reader is actually connected."
            ]
        },
        "continuity_metadata": {"schema_version": CURRENT_SCHEMA_VERSION, "last_update_id": c.3, "parent_timeline_id": timeline_meta.0, "restored_from_rest_point_id": timeline_meta.1, "export_state_sha256": export_state_sha256}
    });
    Ok(serde_json::to_string_pretty(&context)?)
}

fn audit(tx: &Connection, campaign_id: Option<&str>, timeline_id: Option<&str>, event_type: &str, summary: &str, metadata: Value) -> Result<(), KitabaError> {
    tx.execute(
        "INSERT INTO audit_log(id,campaign_id,timeline_id,event_type,summary,metadata_json,created_at) VALUES (?1,?2,?3,?4,?5,?6,?7)",
        params![Uuid::new_v4().to_string(), campaign_id, timeline_id, event_type, summary, serde_json::to_string(&metadata)?, Utc::now().to_rfc3339()],
    )?;
    Ok(())
}

pub fn list_entities(conn: &Connection, campaign_id: &str, include_gm: bool) -> Result<Vec<crate::model::EntityDocument>, KitabaError> {
    let sql = if include_gm {
        "SELECT id,entity_type,visibility,entity_version,data_json,protection,updated_at FROM entity_documents WHERE campaign_id=?1 AND archived=0 ORDER BY entity_type,updated_at DESC,id"
    } else {
        "SELECT id,entity_type,visibility,entity_version,data_json,protection,updated_at FROM entity_documents WHERE campaign_id=?1 AND archived=0 AND visibility='PLAYER' ORDER BY entity_type,updated_at DESC,id"
    };
    let mut stmt = conn.prepare(sql)?;
    let rows = stmt.query_map([campaign_id], |r| {
        let raw: String = r.get(4)?;
        Ok(crate::model::EntityDocument {
            id: r.get(0)?,
            entity_type: r.get(1)?,
            visibility: r.get(2)?,
            entity_version: r.get(3)?,
            protection: r.get(5)?,
            data: serde_json::from_str::<Value>(&raw).unwrap_or(Value::Object(Map::new())),
            updated_at: r.get(6)?,
        })
    })?;
    Ok(rows.collect::<Result<Vec<_>, _>>()?)
}

pub fn list_rest_points(conn: &Connection, campaign_id: &str) -> Result<Vec<crate::model::RestPointSummary>, KitabaError> {
    let mut stmt = conn.prepare(
        "SELECT id,timeline_id,snapshot_revision,game_time,location,description,created_at FROM rest_points WHERE campaign_id=?1 AND invalidated_at IS NULL ORDER BY snapshot_revision DESC, created_at DESC, rowid DESC"
    )?;
    let rows = stmt.query_map([campaign_id], |r| Ok(crate::model::RestPointSummary {
        id: r.get(0)?, timeline_id: r.get(1)?, snapshot_revision: r.get(2)?, game_time: r.get(3)?,
        location: r.get(4)?, description: r.get(5)?, created_at: r.get(6)?,
    }))?;
    Ok(rows.collect::<Result<Vec<_>, _>>()?)
}

pub fn list_audit_events(conn: &Connection, campaign_id: &str, limit: usize) -> Result<Vec<crate::model::AuditEvent>, KitabaError> {
    let capped = limit.clamp(1, 200) as i64;
    let mut stmt = conn.prepare(
        "SELECT id,event_type,summary,created_at FROM audit_log WHERE campaign_id=?1 ORDER BY created_at DESC, rowid DESC LIMIT ?2"
    )?;
    let rows = stmt.query_map(params![campaign_id, capped], |r| Ok(crate::model::AuditEvent {
        id: r.get(0)?, event_type: r.get(1)?, summary: r.get(2)?, created_at: r.get(3)?,
    }))?;
    Ok(rows.collect::<Result<Vec<_>, _>>()?)
}

pub fn rollback_death(conn: &mut Connection, campaign_id: &str, rest_point_id: &str, death_summary: Option<&str>) -> Result<crate::model::RollbackResult, KitabaError> {
    let tx = conn.transaction()?;
    let campaign = tx.query_row(
        "SELECT current_revision,current_timeline_id,death_pending FROM campaigns WHERE id=?1",
        [campaign_id], |r| Ok((r.get::<_, i64>(0)?, r.get::<_, String>(1)?, r.get::<_, i64>(2)?))
    ).optional()?.ok_or(KitabaError::CampaignNotFound)?;
    let latest_rest_id: Option<String> = tx.query_row(
        "SELECT id FROM rest_points WHERE campaign_id=?1 AND invalidated_at IS NULL ORDER BY snapshot_revision DESC, created_at DESC, rowid DESC LIMIT 1",
        [campaign_id], |r| r.get(0)
    ).optional()?;
    if latest_rest_id.as_deref() != Some(rest_point_id) {
        return Err(KitabaError::Validation("Death rollback is only authorized to the latest valid Rest Point".into()));
    }
    let rest = tx.query_row(
        "SELECT snapshot_json,game_time FROM rest_points WHERE id=?1 AND campaign_id=?2 AND invalidated_at IS NULL",
        params![rest_point_id, campaign_id], |r| Ok((r.get::<_, String>(0)?, r.get::<_, Option<String>>(1)?))
    ).optional()?.ok_or_else(|| KitabaError::Validation("Rest Point inconnu ou invalide".into()))?;
    if campaign.2 == 0 { return Err(KitabaError::Validation("Death rollback is not authorized: no confirmed player death".into())); }

    let dead_snapshot = snapshot_state(&tx, campaign_id)?;
    let dead_raw = canonical_json(&dead_snapshot)?;
    let now = Utc::now().to_rfc3339();
    let old_timeline_id = campaign.1;
    let new_timeline_id = Uuid::new_v4().to_string();
    let new_revision = campaign.0 + 1;

    tx.execute(
        "INSERT INTO dead_timelines(id,campaign_id,timeline_id,died_at_revision,death_summary,state_snapshot_json,state_snapshot_sha256,rolled_back_to_rest_point_id,created_at) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9)",
        params![Uuid::new_v4().to_string(), campaign_id, old_timeline_id, campaign.0, death_summary, dead_raw, hex::encode(Sha256::digest(dead_raw.as_bytes())), rest_point_id, now],
    )?;
    tx.execute("UPDATE timelines SET status='DEAD',ended_revision=?1 WHERE id=?2", params![campaign.0, old_timeline_id])?;

    let snapshot: Value = serde_json::from_str(&rest.0)?;
    let entities = snapshot.get("entities").and_then(Value::as_array).ok_or_else(|| KitabaError::Validation("Snapshot Rest Point invalide: entities manquant".into()))?;
    tx.execute("DELETE FROM entity_documents WHERE campaign_id=?1", [campaign_id])?;
    tx.execute("DELETE FROM entity_links WHERE campaign_id=?1", [campaign_id])?;
    for entity in entities {
        let id = entity.get("id").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("Snapshot entity id invalide".into()))?;
        let entity_type = entity.get("entity_type").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("Snapshot entity_type invalide".into()))?;
        let visibility = entity.get("visibility").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("Snapshot visibility invalide".into()))?;
        let version = entity.get("entity_version").and_then(Value::as_i64).ok_or_else(|| KitabaError::Validation("Snapshot entity_version invalide".into()))?;
        let data = entity.get("data").cloned().unwrap_or_else(|| json!({}));
        let protection = entity.get("protection").and_then(Value::as_str).unwrap_or("NORMAL");
        tx.execute(
            "INSERT INTO entity_documents(id,campaign_id,entity_type,visibility,entity_version,data_json,protection,archived,created_at,updated_at) VALUES (?1,?2,?3,?4,?5,?6,?7,0,?8,?8)",
            params![id, campaign_id, entity_type, visibility, version, canonical_json(&data)?, protection, now],
        )?;
    }
    if let Some(links) = snapshot.get("links").and_then(Value::as_array) {
        for link in links {
            let id = link.get("id").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("Snapshot link id invalide".into()))?;
            let from = link.get("from_entity_id").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("Snapshot link source invalide".into()))?;
            let to = link.get("to_entity_id").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("Snapshot link destination invalide".into()))?;
            let link_type = link.get("link_type").and_then(Value::as_str).ok_or_else(|| KitabaError::Validation("Snapshot link_type invalide".into()))?;
            let visibility = link.get("visibility").and_then(Value::as_str).unwrap_or("PLAYER");
            let data_json = link.get("data_json").and_then(Value::as_str).unwrap_or("{}");
            tx.execute(
                "INSERT INTO entity_links(id,campaign_id,from_entity_id,to_entity_id,link_type,visibility,data_json,archived,created_at,updated_at) VALUES (?1,?2,?3,?4,?5,?6,?7,0,?8,?8)",
                params![id, campaign_id, from, to, link_type, visibility, data_json, now],
            )?;
        }
    }

    tx.execute(
        "INSERT INTO timelines(id,campaign_id,parent_timeline_id,restored_from_rest_point_id,status,started_revision,created_at) VALUES (?1,?2,?3,?4,'ACTIVE',?5,?6)",
        params![new_timeline_id, campaign_id, old_timeline_id, rest_point_id, new_revision, now],
    )?;
    tx.execute(
        "UPDATE campaigns SET current_revision=?1,current_timeline_id=?2,game_time=?3,last_update_id=NULL,updated_at=?4,death_pending=0,death_summary=NULL WHERE id=?5",
        params![new_revision, new_timeline_id, rest.1, now, campaign_id],
    )?;
    audit(&tx, Some(campaign_id), Some(&new_timeline_id), "death_rollback", "Death rollback to authorized Rest Point", json!({"rest_point_id": rest_point_id, "previous_timeline_id": old_timeline_id}))?;
    tx.commit()?;
    Ok(crate::model::RollbackResult { revision: new_revision, timeline_id: new_timeline_id, restored_rest_point_id: rest_point_id.to_string() })
}

pub fn manual_patch_entity(
    conn: &mut Connection,
    campaign_id: &str,
    entity_id: &str,
    patch: Value,
    expected_entity_version: i64,
    reason: &str,
    visibility: &str,
    override_immutable: bool,
) -> Result<crate::model::ManualCorrectionResult, KitabaError> {
    if !matches!(visibility, "PLAYER" | "GM") {
        return Err(KitabaError::Validation("visibility must be PLAYER or GM".into()));
    }
    let patch_obj = patch.as_object().ok_or_else(|| KitabaError::Validation("manual patch must be a JSON object".into()))?;
    if patch_obj.is_empty() {
        return Err(KitabaError::Validation("manual patch must not be empty".into()));
    }
    if expected_entity_version < 1 {
        return Err(KitabaError::Validation("expected_entity_version must be positive".into()));
    }
    if reason.trim().is_empty() {
        return Err(KitabaError::Validation("manual correction requires a reason".into()));
    }

    let tx = conn.transaction()?;
    let campaign: (i64, String, i64) = tx.query_row(
        "SELECT current_revision,current_timeline_id,death_pending FROM campaigns WHERE id=?1",
        [campaign_id],
        |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
    ).optional()?.ok_or(KitabaError::CampaignNotFound)?;
    if campaign.2 != 0 {
        return Err(KitabaError::Validation("Manual correction is blocked while death rollback is pending".into()));
    }

    let row: (String, String, i64, String, String) = tx.query_row(
        "SELECT entity_type,visibility,entity_version,data_json,protection FROM entity_documents WHERE campaign_id=?1 AND id=?2 AND archived=0",
        params![campaign_id, entity_id],
        |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?, r.get(3)?, r.get(4)?)),
    ).optional()?.ok_or_else(|| KitabaError::Validation("Entity does not exist".into()))?;

    if row.1 != visibility {
        return Err(KitabaError::Validation("Manual correction scope does not match entity visibility".into()));
    }
    if row.2 != expected_entity_version {
        return Err(KitabaError::Validation(format!(
            "Entity version conflict: expected {expected_entity_version}, actual {}", row.2
        )));
    }
    if row.4 == "IMMUTABLE" && !override_immutable {
        return Err(KitabaError::Validation("immutable entity requires explicit override".into()));
    }

    let base: Value = serde_json::from_str(&row.3)?;
    let merged = merge_json(&base, &patch);
    let correction_id = Uuid::new_v4().to_string();
    let provenance = format!("manual:{correction_id}");
    let now = Utc::now().to_rfc3339();
    let new_revision = campaign.0 + 1;
    let new_entity_version = row.2 + 1;
    tx.execute(
        "UPDATE entity_documents SET data_json=?1,entity_version=?2,updated_by_update_id=?3,updated_at=?4 WHERE campaign_id=?5 AND id=?6",
        params![canonical_json(&merged)?, new_entity_version, provenance, now, campaign_id, entity_id],
    )?;
    tx.execute(
        "UPDATE campaigns SET current_revision=?1,updated_at=?2 WHERE id=?3",
        params![new_revision, now, campaign_id],
    )?;

    if visibility == "GM" {
        audit(
            &tx, Some(campaign_id), Some(&campaign.1),
            "manual_entity_correction", "Correction manuelle MJ enregistrée",
            json!({"correction_id": correction_id, "visibility": "GM", "reason_recorded": true}),
        )?;
    } else {
        audit(
            &tx, Some(campaign_id), Some(&campaign.1),
            "manual_entity_correction", &format!("Correction manuelle joueur : {}", row.0),
            json!({"correction_id": correction_id, "visibility": "PLAYER", "entity_id": entity_id, "entity_type": row.0, "reason": reason.trim()}),
        )?;
    }
    tx.commit()?;
    Ok(crate::model::ManualCorrectionResult {
        correction_id,
        campaign_revision: new_revision,
        entity_id: entity_id.to_owned(),
        entity_version: new_entity_version,
    })
}

pub fn record_context_export(conn: &Connection, campaign_id: &str, mode: &str) -> Result<(), KitabaError> {
    let (revision, timeline_id): (i64, String) = conn.query_row(
        "SELECT current_revision,current_timeline_id FROM campaigns WHERE id=?1",
        [campaign_id], |r| Ok((r.get(0)?, r.get(1)?))
    ).optional()?.ok_or(KitabaError::CampaignNotFound)?;
    let now = Utc::now().to_rfc3339();
    match mode {
        "GM_FULL" => { conn.execute("UPDATE campaigns SET last_gm_export_revision=?1,last_gm_export_at=?2 WHERE id=?3", params![revision, now, campaign_id])?; }
        "PLAYER" => { conn.execute("UPDATE campaigns SET last_player_export_revision=?1,last_player_export_at=?2 WHERE id=?3", params![revision, now, campaign_id])?; }
        _ => return Err(KitabaError::Validation("mode must be PLAYER or GM_FULL".into())),
    }
    audit(conn, Some(campaign_id), Some(&timeline_id), "context_exported", &format!("{mode} context exported"), json!({"mode": mode, "revision": revision}))?;
    Ok(())
}

pub fn create_technical_backup(
    conn: &Connection,
    campaign_id: Option<&str>,
    output_path: &std::path::Path,
    reason: &str,
    asset_root: &std::path::Path,
) -> Result<(), KitabaError> {
    use rusqlite::DatabaseName;
    if let Some(parent) = output_path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    if let Some(cid) = campaign_id {
        let exists = conn.query_row("SELECT 1 FROM campaigns WHERE id=?1", [cid], |r| r.get::<_, i64>(0)).optional()?;
        if exists.is_none() { return Err(KitabaError::CampaignNotFound); }
    }

    let temp_db = std::env::temp_dir().join(format!("kitaba-backup-{}.sqlite", Uuid::new_v4()));
    conn.backup(DatabaseName::Main, &temp_db, None)?;
    let probe = Connection::open(&temp_db)?;
    probe.execute_batch("PRAGMA foreign_keys=ON;")?;
    if let Some(cid) = campaign_id {
        probe.execute("DELETE FROM campaigns WHERE id<>?1", [cid])?;
        probe.execute("DELETE FROM technical_backups WHERE campaign_id IS NULL OR campaign_id<>?1", [cid])?;
        probe.execute("DELETE FROM audit_log WHERE campaign_id IS NULL OR campaign_id<>?1", [cid])?;
    }
    let integrity: String = probe.query_row("PRAGMA integrity_check", [], |r| r.get(0))?;
    drop(probe);
    if integrity != "ok" {
        let _ = std::fs::remove_file(&temp_db);
        return Err(KitabaError::Validation(format!("backup integrity check failed: {integrity}")));
    }

    let db_bytes = std::fs::read(&temp_db)?;
    let db_hash = hex::encode(Sha256::digest(&db_bytes));
    let mut files = Map::new();
    files.insert("campaign.sqlite".into(), json!({"sha256": db_hash}));

    let asset_rows: Vec<(String, String, Option<String>)> = if let Some(cid) = campaign_id {
        let mut stmt = conn.prepare("SELECT campaign_id,relative_path,sha256 FROM assets WHERE campaign_id=?1 ORDER BY relative_path")?;
        let rows = stmt.query_map([cid], |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)))?.collect::<Result<Vec<_>, _>>()?;
        rows
    } else {
        let mut stmt = conn.prepare("SELECT campaign_id,relative_path,sha256 FROM assets ORDER BY campaign_id,relative_path")?;
        let rows = stmt.query_map([], |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)))?.collect::<Result<Vec<_>, _>>()?;
        rows
    };

    let mut staged_assets: Vec<(std::path::PathBuf, String)> = Vec::new();
    for (registered_campaign_id, relative, registered_hash) in asset_rows {
        if let Some(expected_campaign_id) = campaign_id {
            if registered_campaign_id != expected_campaign_id {
                let _ = std::fs::remove_file(&temp_db);
                return Err(KitabaError::Validation("campaign backup contains asset registration from another campaign".into()));
            }
        }
        let source = managed_asset_path(asset_root, &registered_campaign_id, &relative)?;
        if !source.is_file() {
            let _ = std::fs::remove_file(&temp_db);
            return Err(KitabaError::Validation(format!("registered asset is missing: {relative}")));
        }
        let bytes = std::fs::read(&source)?;
        let digest = hex::encode(Sha256::digest(&bytes));
        if let Some(expected) = registered_hash {
            if expected != digest {
                let _ = std::fs::remove_file(&temp_db);
                return Err(KitabaError::Validation(format!("registered asset checksum mismatch: {relative}")));
            }
        }
        let archive_name = format!("assets/{relative}");
        files.insert(archive_name.clone(), json!({"sha256": digest}));
        staged_assets.push((source, archive_name));
    }

    let manifest = json!({
        "format": "KITABA_BACKUP",
        "backup_version": 1,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "campaign_id": campaign_id,
        "reason": reason,
        "created_at": Utc::now().to_rfc3339(),
        "files": Value::Object(files),
    });

    let write_result = (|| -> Result<(), KitabaError> {
        let file = std::fs::File::create(output_path)?;
        let mut zip = ZipWriter::new(file);
        let options = SimpleFileOptions::default().compression_method(CompressionMethod::Deflated);
        zip.start_file("campaign.sqlite", options).map_err(|e| KitabaError::Validation(e.to_string()))?;
        zip.write_all(&db_bytes)?;
        for (source, archive_name) in staged_assets {
            zip.start_file(&archive_name, options).map_err(|e| KitabaError::Validation(e.to_string()))?;
            let bytes = std::fs::read(source)?;
            zip.write_all(&bytes)?;
        }
        zip.start_file("manifest.json", options).map_err(|e| KitabaError::Validation(e.to_string()))?;
        zip.write_all(serde_json::to_string_pretty(&manifest)?.as_bytes())?;
        zip.finish().map_err(|e| KitabaError::Validation(e.to_string()))?;
        Ok(())
    })();
    let _ = std::fs::remove_file(&temp_db);
    write_result?;

    let archive_bytes = std::fs::read(output_path)?;
    let archive_hash = hex::encode(Sha256::digest(&archive_bytes));
    conn.execute(
        "INSERT INTO technical_backups(id,campaign_id,reason,file_name,sha256,created_at) VALUES (?1,?2,?3,?4,?5,?6)",
        params![Uuid::new_v4().to_string(), campaign_id, reason, output_path.file_name().and_then(|s| s.to_str()).unwrap_or("backup.kitaba"), archive_hash, Utc::now().to_rfc3339()],
    )?;
    Ok(())
}

fn extract_verified_backup(input_path: &std::path::Path) -> Result<(Value, std::path::PathBuf, std::path::PathBuf), KitabaError> {
    if !input_path.exists() { return Err(KitabaError::Validation("backup file not found".into())); }
    let file = std::fs::File::open(input_path)?;
    let mut archive = ZipArchive::new(file).map_err(|e| KitabaError::Validation(format!("invalid .kitaba archive: {e}")))?;

    let manifest: Value = {
        let mut entry = archive.by_name("manifest.json").map_err(|_| KitabaError::Validation("not a Kitaba backup: manifest.json missing".into()))?;
        if entry.size() > 1_048_576 { return Err(KitabaError::Validation("backup manifest is unexpectedly large".into())); }
        let mut raw = String::new();
        entry.read_to_string(&mut raw)?;
        serde_json::from_str(&raw)?
    };
    if manifest.get("format").and_then(Value::as_str) != Some("KITABA_BACKUP") {
        return Err(KitabaError::Validation("not a Kitaba backup: invalid manifest format".into()));
    }
    if manifest.get("backup_version").and_then(Value::as_i64) != Some(1) {
        return Err(KitabaError::Validation("unsupported Kitaba backup version".into()));
    }
    let schema = manifest.get("schema_version").and_then(Value::as_i64)
        .ok_or_else(|| KitabaError::Validation("backup manifest has no schema_version".into()))?;
    if schema > CURRENT_SCHEMA_VERSION {
        return Err(KitabaError::Validation(format!("backup schema {schema} is newer than this Companion supports ({CURRENT_SCHEMA_VERSION})")));
    }
    let files = manifest.get("files").and_then(Value::as_object)
        .ok_or_else(|| KitabaError::Validation("backup manifest has no files map".into()))?;
    if !files.contains_key("campaign.sqlite") {
        return Err(KitabaError::Validation("backup manifest has no database checksum".into()));
    }

    let temp_root = std::env::temp_dir().join(format!("kitaba-restore-{}", Uuid::new_v4()));
    std::fs::create_dir_all(&temp_root)?;
    let temp_db = temp_root.join("campaign.sqlite");

    for (archive_name, metadata) in files {
        let path = std::path::Path::new(archive_name);
        if path.is_absolute() || path.components().any(|c| matches!(c, std::path::Component::ParentDir)) {
            let _ = std::fs::remove_dir_all(&temp_root);
            return Err(KitabaError::Validation("backup manifest contains an unsafe file path".into()));
        }
        if archive_name != "campaign.sqlite" && !archive_name.starts_with("assets/") {
            let _ = std::fs::remove_dir_all(&temp_root);
            return Err(KitabaError::Validation(format!("unsupported file in backup manifest: {archive_name}")));
        }
        let expected = metadata.get("sha256").and_then(Value::as_str)
            .ok_or_else(|| KitabaError::Validation(format!("backup manifest has no checksum for {archive_name}")))?;
        let mut entry = archive.by_name(archive_name).map_err(|_| KitabaError::Validation(format!("backup file is missing: {archive_name}")))?;
        let max_size = if archive_name == "campaign.sqlite" { 2 * 1024 * 1024 * 1024_u64 } else { 25 * 1024 * 1024_u64 };
        if entry.size() > max_size {
            let _ = std::fs::remove_dir_all(&temp_root);
            return Err(KitabaError::Validation(format!("backup file is too large: {archive_name}")));
        }
        let mut bytes = Vec::with_capacity(entry.size().min(64 * 1024 * 1024) as usize);
        entry.read_to_end(&mut bytes)?;
        let actual = hex::encode(Sha256::digest(&bytes));
        if actual != expected {
            let _ = std::fs::remove_dir_all(&temp_root);
            return Err(KitabaError::Validation(format!("backup checksum mismatch: {archive_name}")));
        }
        let destination = temp_root.join(path);
        if let Some(parent) = destination.parent() { std::fs::create_dir_all(parent)?; }
        std::fs::write(destination, bytes)?;
    }
    if !temp_db.exists() {
        let _ = std::fs::remove_dir_all(&temp_root);
        return Err(KitabaError::Validation("not a Kitaba backup: campaign.sqlite missing".into()));
    }
    Ok((manifest, temp_db, temp_root))
}

fn copy_dir_recursive(source: &std::path::Path, destination: &std::path::Path) -> Result<(), KitabaError> {
    if !source.exists() { return Ok(()); }
    std::fs::create_dir_all(destination)?;
    for entry in std::fs::read_dir(source)? {
        let entry = entry?;
        let file_type = entry.file_type()?;
        let dest = destination.join(entry.file_name());
        if file_type.is_dir() { copy_dir_recursive(&entry.path(), &dest)?; }
        else if file_type.is_file() { std::fs::copy(entry.path(), dest)?; }
    }
    Ok(())
}

pub fn restore_technical_backup(
    conn: &mut Connection,
    input_path: &std::path::Path,
    asset_root: &std::path::Path,
) -> Result<(), KitabaError> {
    use rusqlite::DatabaseName;
    let (manifest, temp_db, temp_root) = extract_verified_backup(input_path)?;
    let result = (|| -> Result<(), KitabaError> {
        let probe = Connection::open(&temp_db)?;
        probe.execute_batch("PRAGMA foreign_keys=ON;")?;
        let integrity: String = probe.query_row("PRAGMA integrity_check", [], |r| r.get(0))?;
        if integrity != "ok" { return Err(KitabaError::Validation(format!("backup integrity check failed: {integrity}"))); }
        let has_campaigns: Option<i64> = probe.query_row("SELECT 1 FROM sqlite_master WHERE type='table' AND name='campaigns'", [], |r| r.get(0)).optional()?;
        if has_campaigns.is_none() { return Err(KitabaError::Validation("not a Kitaba backup: campaigns table missing".into())); }
        let has_migrations: Option<i64> = probe.query_row("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'", [], |r| r.get(0)).optional()?;
        if has_migrations.is_none() { return Err(KitabaError::Validation("not a Kitaba backup: schema metadata missing".into())); }
        let backup_schema: i64 = probe.query_row("SELECT COALESCE(MAX(version),0) FROM schema_migrations", [], |r| r.get(0))?;
        if backup_schema > CURRENT_SCHEMA_VERSION {
            return Err(KitabaError::Validation(format!("backup schema {backup_schema} is newer than this Companion supports ({CURRENT_SCHEMA_VERSION})")));
        }
        migrate(&probe)?;
        let fk_problem: Option<String> = probe.query_row("SELECT 'foreign_key_violation' FROM pragma_foreign_key_check LIMIT 1", [], |r| r.get(0)).optional()?;
        if fk_problem.is_some() { return Err(KitabaError::Validation("backup foreign-key integrity check failed".into())); }
        drop(probe);

        if let Some(cid) = manifest.get("campaign_id").and_then(Value::as_str) {
            let incoming = Connection::open(&temp_db)?;
            let (count, only_id): (i64, Option<String>) = (
                incoming.query_row("SELECT COUNT(*) FROM campaigns", [], |r| r.get(0))?,
                incoming.query_row("SELECT id FROM campaigns LIMIT 1", [], |r| r.get(0)).optional()?,
            );
            drop(incoming);
            if count != 1 || only_id.as_deref() != Some(cid) {
                return Err(KitabaError::Validation("campaign backup manifest/database mismatch".into()));
            }
            let incoming_asset_dir = temp_root.join("assets").join(cid);
            if temp_root.join("assets").exists() {
                for entry in std::fs::read_dir(temp_root.join("assets"))? {
                    let entry = entry?;
                    if entry.file_name().to_string_lossy() != cid {
                        return Err(KitabaError::Validation("campaign backup contains an asset from another campaign".into()));
                    }
                }
            }

            // Stage the incoming campaign assets on the same filesystem before touching
            // either the canonical database or the currently active asset directory. This
            // makes ordinary I/O failures happen while the old state is still untouched.
            std::fs::create_dir_all(asset_root)?;
            let destination = asset_root.join(cid);
            let swap_token = Uuid::new_v4().to_string();
            let staged_destination = asset_root.join(format!(".restore-stage-{cid}-{swap_token}"));
            let previous_destination = asset_root.join(format!(".restore-previous-{cid}-{swap_token}"));
            std::fs::create_dir_all(&staged_destination)?;
            copy_dir_recursive(&incoming_asset_dir, &staged_destination)?;

            let temp_db_owned = temp_db.to_string_lossy().into_owned();
            conn.execute("ATTACH DATABASE ?1 AS incoming", [&temp_db_owned])?;
            let merge_result = (|| -> Result<(), KitabaError> {
                let tx = conn.transaction()?;
                tx.execute_batch("PRAGMA defer_foreign_keys=ON;")?;
                tx.execute("DELETE FROM technical_backups WHERE campaign_id=?1", [cid])?;
                tx.execute("DELETE FROM campaigns WHERE id=?1", [cid])?;
                tx.execute("INSERT INTO campaigns SELECT * FROM incoming.campaigns WHERE id=?1", [cid])?;
                for table in [
                    "timelines", "entity_documents", "entity_links", "applied_updates",
                    "rest_points", "dead_timelines", "dead_timeline_resolutions",
                    "technical_backups", "audit_log", "assets",
                ] {
                    tx.execute(&format!("INSERT INTO {table} SELECT * FROM incoming.{table} WHERE campaign_id=?1"), [cid])?;
                }

                // Keep the SQLite transaction open while swapping the filesystem state.
                // If activation fails, dropping tx rolls the DB back. If SQLite commit
                // fails after activation, restore the previous asset directory immediately.
                let had_previous_assets = destination.exists();
                if had_previous_assets {
                    std::fs::rename(&destination, &previous_destination)?;
                }
                if let Err(err) = std::fs::rename(&staged_destination, &destination) {
                    if had_previous_assets {
                        let _ = std::fs::rename(&previous_destination, &destination);
                    }
                    return Err(err.into());
                }

                if let Err(err) = tx.commit() {
                    let _ = std::fs::remove_dir_all(&destination);
                    if had_previous_assets {
                        let _ = std::fs::rename(&previous_destination, &destination);
                    }
                    return Err(err.into());
                }

                if previous_destination.exists() {
                    let _ = std::fs::remove_dir_all(&previous_destination);
                }
                Ok(())
            })();
            let detach = conn.execute_batch("DETACH DATABASE incoming;");
            if staged_destination.exists() { let _ = std::fs::remove_dir_all(&staged_destination); }
            if merge_result.is_err() && previous_destination.exists() && !destination.exists() {
                let _ = std::fs::rename(&previous_destination, &destination);
            }
            merge_result?;
            detach?;
        } else {
            // Full-application restore: prepare both rollback material and the incoming
            // filesystem state before replacing anything live.
            let restore_token = Uuid::new_v4().to_string();
            let asset_parent = asset_root.parent().unwrap_or_else(|| std::path::Path::new("."));
            std::fs::create_dir_all(asset_parent)?;
            let staged_assets = asset_parent.join(format!(".full-restore-stage-{restore_token}"));
            let previous_assets = asset_parent.join(format!(".full-restore-previous-{restore_token}"));
            std::fs::create_dir_all(&staged_assets)?;
            copy_dir_recursive(&temp_root.join("assets"), &staged_assets)?;

            let previous_db = std::env::temp_dir().join(format!("kitaba-full-restore-previous-{restore_token}.sqlite"));
            conn.backup(DatabaseName::Main, &previous_db, None)?;

            let had_previous_assets = asset_root.exists();
            if had_previous_assets {
                std::fs::rename(asset_root, &previous_assets)?;
            }
            if let Err(err) = std::fs::rename(&staged_assets, asset_root) {
                if had_previous_assets {
                    let _ = std::fs::rename(&previous_assets, asset_root);
                }
                let _ = std::fs::remove_file(&previous_db);
                return Err(err.into());
            }

            let database_result = (|| -> Result<(), KitabaError> {
                conn.restore(DatabaseName::Main, &temp_db, None::<fn(rusqlite::backup::Progress)>)?;
                migrate(conn)?;
                conn.execute_batch("PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL;")?;
                Ok(())
            })();

            if let Err(restore_error) = database_result {
                let recovery_result = (|| -> Result<(), KitabaError> {
                    conn.restore(DatabaseName::Main, &previous_db, None::<fn(rusqlite::backup::Progress)>)?;
                    migrate(conn)?;
                    conn.execute_batch("PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL;")?;
                    Ok(())
                })();
                let _ = std::fs::remove_dir_all(asset_root);
                if had_previous_assets {
                    let _ = std::fs::rename(&previous_assets, asset_root);
                }
                let _ = std::fs::remove_file(&previous_db);
                if let Err(recovery_error) = recovery_result {
                    return Err(KitabaError::Validation(format!(
                        "full restore failed ({restore_error}); automatic rollback also failed ({recovery_error})"
                    )));
                }
                return Err(restore_error);
            }

            if previous_assets.exists() { let _ = std::fs::remove_dir_all(&previous_assets); }
            let _ = std::fs::remove_file(&previous_db);
        }
        Ok(())
    })();
    let _ = std::fs::remove_dir_all(&temp_root);
    result
}


#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        conn.execute_batch("PRAGMA foreign_keys=ON;").unwrap();
        migrate(&conn).unwrap();
        conn
    }

    fn update_json(campaign_id: &str, timeline_id: &str, revision: i64, operations: Value, gm_operations: Value) -> String {
        serde_json::to_string(&json!({
            "format": "KITABA_UPDATE",
            "protocol_version": 1,
            "campaign_id": campaign_id,
            "timeline_id": timeline_id,
            "update_id": Uuid::new_v4().to_string(),
            "base_revision": revision,
            "target_revision": revision + 1,
            "game_time": {"set": format!("Jour 1 {:02}:00", 8 + revision), "elapsed_minutes": if revision == 0 { 0 } else { 60 }},
            "operations": operations,
            "gm_operations": gm_operations,
            "link_operations": [],
            "gm_link_operations": [],
            "journal_entries": [],
            "notifications": [],
            "dead_timeline_resolutions": [],
            "checkpoint": null,
            "death": null
        })).unwrap()
    }

    #[test]
    fn rust_core_campaign_and_update_roundtrip() {
        let mut conn = setup();
        let campaign = create_campaign(&conn, "Sully").unwrap();
        let entity_id = Uuid::new_v4().to_string();
        let raw = update_json(
            &campaign.id,
            &campaign.current_timeline_id,
            0,
            json!([{"op":"create","entity_type":"player_character","entity_id":entity_id,"data":{"first_name":"Sully","age":8}}]),
            json!([]),
        );
        let result = apply_update(&mut conn, &raw).unwrap();
        assert_eq!(result.revision, 1);
        let context: Value = serde_json::from_str(&export_context(&conn, &campaign.id, "PLAYER").unwrap()).unwrap();
        assert_eq!(context["campaign_revision"], 1);
        assert_eq!(context["entities"][0]["data"]["first_name"], "Sully");
    }

    #[test]
    fn rust_core_player_export_hides_gm_entities() {
        let mut conn = setup();
        let campaign = create_campaign(&conn, "Sully").unwrap();
        let gm_id = Uuid::new_v4().to_string();
        let raw = update_json(
            &campaign.id,
            &campaign.current_timeline_id,
            0,
            json!([]),
            json!([{"op":"create","entity_type":"canon_fact","entity_id":gm_id,"data":{"secret":"hidden"}}]),
        );
        apply_update(&mut conn, &raw).unwrap();
        let player = export_context(&conn, &campaign.id, "PLAYER").unwrap();
        let full = export_context(&conn, &campaign.id, "GM_FULL").unwrap();
        assert!(!player.contains("\"secret\": \"hidden\""));
        assert!(full.contains("\"secret\": \"hidden\""));
    }

    #[test]
    fn rust_core_duplicate_update_is_rejected() {
        let mut conn = setup();
        let campaign = create_campaign(&conn, "Sully").unwrap();
        let raw = update_json(&campaign.id, &campaign.current_timeline_id, 0, json!([]), json!([]));
        apply_update(&mut conn, &raw).unwrap();
        assert!(matches!(apply_update(&mut conn, &raw), Err(KitabaError::DuplicateUpdate)));
    }

    #[test]
    fn rust_core_archive_restore_and_integrity() {
        let conn = setup();
        let campaign = create_campaign(&conn, "Sully").unwrap();
        let root = std::env::temp_dir().join(format!("kitaba-rust-test-{}", Uuid::new_v4()));
        std::fs::create_dir_all(&root).unwrap();
        let report = integrity_report(&conn, &campaign.id, &root).unwrap();
        assert!(report.ok);
        set_campaign_archived(&conn, &campaign.id, true).unwrap();
        assert_eq!(list_archived_campaigns(&conn).unwrap().len(), 1);
        set_campaign_archived(&conn, &campaign.id, false).unwrap();
        assert!(list_archived_campaigns(&conn).unwrap().is_empty());
        let _ = std::fs::remove_dir_all(root);
    }

    #[test]
    fn rust_core_registered_asset_path_is_contained() {
        let conn = setup();
        let campaign = create_campaign(&conn, "Sully").unwrap();
        let root = std::env::temp_dir().join(format!("kitaba-rust-test-{}", Uuid::new_v4()));
        std::fs::create_dir_all(&root).unwrap();
        conn.execute(
            "INSERT INTO assets(id,campaign_id,kind,relative_path,mime_type,sha256,created_at) VALUES (?1,?2,'other_image','../escape.png','image/png',NULL,?3)",
            params![Uuid::new_v4().to_string(), campaign.id, Utc::now().to_rfc3339()],
        ).unwrap();
        let report = integrity_report(&conn, &campaign.id, &root).unwrap();
        assert!(!report.ok);
        assert!(report.checks.iter().any(|c| c.code == "assets" && !c.ok));
        let _ = std::fs::remove_dir_all(root);
    }

    #[test]
    fn rust_core_campaign_backup_restore_preserves_other_campaign_and_assets() {
        let mut conn = setup();
        let sully = create_campaign(&conn, "Sully").unwrap();
        let other = create_campaign(&conn, "Other campaign").unwrap();
        let entity_id = Uuid::new_v4().to_string();
        let initial = update_json(
            &sully.id,
            &sully.current_timeline_id,
            0,
            json!([{"op":"create","entity_type":"player_character","entity_id":entity_id,"data":{"first_name":"Sully","age":8}}]),
            json!([]),
        );
        apply_update(&mut conn, &initial).unwrap();

        let root = std::env::temp_dir().join(format!("kitaba-rust-restore-test-{}", Uuid::new_v4()));
        let asset_root = root.join("assets");
        std::fs::create_dir_all(&root).unwrap();
        let original_image = root.join("original.png");
        let original_bytes = b"\x89PNG\r\n\x1a\nkitaba-original";
        std::fs::write(&original_image, original_bytes).unwrap();
        let original_asset = import_asset(&conn, &sully.id, "world_map", &original_image, &asset_root).unwrap();

        let backup = root.join("sully.kitaba");
        create_technical_backup(&conn, Some(&sully.id), &backup, "test", &asset_root).unwrap();

        let changed = update_json(
            &sully.id,
            &sully.current_timeline_id,
            1,
            json!([{"op":"patch","entity_type":"player_character","entity_id":entity_id,"data":{"first_name":"Changed"}}]),
            json!([]),
        );
        apply_update(&mut conn, &changed).unwrap();
        let replacement_image = root.join("replacement.png");
        std::fs::write(&replacement_image, b"\x89PNG\r\n\x1a\nreplacement").unwrap();
        import_asset(&conn, &sully.id, "world_map", &replacement_image, &asset_root).unwrap();

        restore_technical_backup(&mut conn, &backup, &asset_root).unwrap();

        let restored: (i64, String) = conn.query_row(
            "SELECT current_revision,current_timeline_id FROM campaigns WHERE id=?1",
            [&sully.id],
            |r| Ok((r.get(0)?, r.get(1)?)),
        ).unwrap();
        assert_eq!(restored.0, 1);
        assert_eq!(restored.1, sully.current_timeline_id);
        let restored_name: String = conn.query_row(
            "SELECT json_extract(data_json,'$.first_name') FROM entity_documents WHERE campaign_id=?1 AND id=?2",
            params![sully.id, entity_id],
            |r| r.get(0),
        ).unwrap();
        assert_eq!(restored_name, "Sully");

        let other_still_exists: i64 = conn.query_row(
            "SELECT COUNT(*) FROM campaigns WHERE id=?1",
            [&other.id],
            |r| r.get(0),
        ).unwrap();
        assert_eq!(other_still_exists, 1);

        let restored_assets = list_assets(&conn, &sully.id).unwrap();
        assert_eq!(restored_assets.len(), 1);
        assert_eq!(restored_assets[0].id, original_asset.id);
        let restored_path = managed_asset_path(&asset_root, &sully.id, &restored_assets[0].relative_path).unwrap();
        assert_eq!(std::fs::read(restored_path).unwrap(), original_bytes);

        assert_eq!(conn.query_row("PRAGMA integrity_check", [], |r| r.get::<_, String>(0)).unwrap(), "ok");
        let mut fk = conn.prepare("PRAGMA foreign_key_check").unwrap();
        assert!(fk.query([]).unwrap().next().unwrap().is_none());
        let _ = std::fs::remove_dir_all(root);
    }


    #[test]
    fn rust_core_full_backup_restore_roundtrip_with_assets() {
        let mut conn = setup();
        let sully = create_campaign(&conn, "Sully").unwrap();
        let other = create_campaign(&conn, "Other").unwrap();
        let sully_entity = Uuid::new_v4().to_string();
        let other_entity = Uuid::new_v4().to_string();
        apply_update(&mut conn, &update_json(
            &sully.id, &sully.current_timeline_id, 0,
            json!([{"op":"create","entity_type":"player_character","entity_id":sully_entity,"data":{"first_name":"Sully","age":8}}]),
            json!([]),
        )).unwrap();
        apply_update(&mut conn, &update_json(
            &other.id, &other.current_timeline_id, 0,
            json!([{"op":"create","entity_type":"player_character","entity_id":other_entity,"data":{"first_name":"Other"}}]),
            json!([]),
        )).unwrap();

        let root = std::env::temp_dir().join(format!("kitaba-rust-full-restore-test-{}", Uuid::new_v4()));
        let asset_root = root.join("assets");
        std::fs::create_dir_all(&root).unwrap();
        let sully_image = root.join("sully.png");
        let other_image = root.join("other.png");
        let sully_bytes = b"\x89PNG\r\n\x1a\nfull-sully-original";
        let other_bytes = b"\x89PNG\r\n\x1a\nfull-other-original";
        std::fs::write(&sully_image, sully_bytes).unwrap();
        std::fs::write(&other_image, other_bytes).unwrap();
        import_asset(&conn, &sully.id, "world_map", &sully_image, &asset_root).unwrap();
        import_asset(&conn, &other.id, "player_portrait", &other_image, &asset_root).unwrap();

        let backup = root.join("full.kitaba");
        create_technical_backup(&conn, None, &backup, "full-test", &asset_root).unwrap();

        apply_update(&mut conn, &update_json(
            &sully.id, &sully.current_timeline_id, 1,
            json!([{"op":"patch","entity_type":"player_character","entity_id":sully_entity,"data":{"first_name":"Changed Sully"}}]),
            json!([]),
        )).unwrap();
        apply_update(&mut conn, &update_json(
            &other.id, &other.current_timeline_id, 1,
            json!([{"op":"patch","entity_type":"player_character","entity_id":other_entity,"data":{"first_name":"Changed Other"}}]),
            json!([]),
        )).unwrap();
        std::fs::remove_dir_all(&asset_root).unwrap();
        std::fs::create_dir_all(&asset_root).unwrap();

        restore_technical_backup(&mut conn, &backup, &asset_root).unwrap();

        let sully_name: String = conn.query_row(
            "SELECT json_extract(data_json,'$.first_name') FROM entity_documents WHERE campaign_id=?1 AND id=?2",
            params![sully.id, sully_entity], |r| r.get(0),
        ).unwrap();
        let other_name: String = conn.query_row(
            "SELECT json_extract(data_json,'$.first_name') FROM entity_documents WHERE campaign_id=?1 AND id=?2",
            params![other.id, other_entity], |r| r.get(0),
        ).unwrap();
        assert_eq!(sully_name, "Sully");
        assert_eq!(other_name, "Other");

        for (cid, expected) in [(&sully.id, sully_bytes.as_slice()), (&other.id, other_bytes.as_slice())] {
            let assets = list_assets(&conn, cid).unwrap();
            assert_eq!(assets.len(), 1);
            let path = managed_asset_path(&asset_root, cid, &assets[0].relative_path).unwrap();
            assert_eq!(std::fs::read(path).unwrap(), expected);
        }
        assert_eq!(conn.query_row("PRAGMA integrity_check", [], |r| r.get::<_, String>(0)).unwrap(), "ok");
        let mut fk = conn.prepare("PRAGMA foreign_key_check").unwrap();
        assert!(fk.query([]).unwrap().next().unwrap().is_none());
        let _ = std::fs::remove_dir_all(root);
    }

}
