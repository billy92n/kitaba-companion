mod db;
mod error;
mod model;

use std::{fs, path::PathBuf, sync::Mutex};
use rusqlite::Connection;
use tauri::{Manager, State};

use crate::{error::KitabaError, model::{AssetSummary, AuditEvent, CampaignSummary, EntityDocument, ImportResult, IntegrityReport, ManualCorrectionResult, RestPointSummary, RollbackResult, UpdatePreview}};

struct DbState { conn: Mutex<Connection>, app_dir: PathBuf }

fn auto_backup_path(app_dir: &std::path::Path, label: &str) -> Result<PathBuf, KitabaError> {
    let dir = app_dir.join("backups");
    std::fs::create_dir_all(&dir).map_err(|e| KitabaError::Validation(e.to_string()))?;
    Ok(dir.join(format!("{}-{}.kitaba", label, chrono::Utc::now().format("%Y%m%d-%H%M%S-%3f"))))
}

fn prune_auto_backups(app_dir: &std::path::Path, keep: usize) -> Result<(), KitabaError> {
    let dir = app_dir.join("backups");
    if !dir.exists() { return Ok(()); }
    let mut files: Vec<_> = std::fs::read_dir(&dir)
        .map_err(|e| KitabaError::Validation(e.to_string()))?
        .filter_map(Result::ok)
        .filter(|entry| entry.path().extension().and_then(|x| x.to_str()) == Some("kitaba"))
        .collect();
    files.sort_by_key(|entry| entry.metadata().and_then(|m| m.modified()).ok());
    let excess = files.len().saturating_sub(keep);
    for entry in files.into_iter().take(excess) {
        let _ = std::fs::remove_file(entry.path());
    }
    Ok(())
}

#[tauri::command]
fn list_campaigns(state: State<'_, DbState>) -> Result<Vec<CampaignSummary>, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::list_campaigns(&conn)
}

#[tauri::command]
fn create_campaign(name: String, state: State<'_, DbState>) -> Result<CampaignSummary, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::create_campaign(&conn, &name)
}


#[tauri::command]
fn list_archived_campaigns(state: State<'_, DbState>) -> Result<Vec<CampaignSummary>, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::list_archived_campaigns(&conn)
}

#[tauri::command]
fn set_campaign_archived(campaign_id: String, archived: bool, state: State<'_, DbState>) -> Result<(), KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::set_campaign_archived(&conn, &campaign_id, archived)
}

#[tauri::command]
fn delete_campaign_permanently(campaign_id: String, expected_name: String, state: State<'_, DbState>) -> Result<(), KitabaError> {
    let mut conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    let path = auto_backup_path(&state.app_dir, "pre-delete")?;
    db::create_technical_backup(&conn, Some(&campaign_id), &path, "automatic_pre_delete", &state.app_dir.join("assets"))?;
    prune_auto_backups(&state.app_dir, 30)?;
    db::delete_campaign_permanently(&conn, &campaign_id, &expected_name, &state.app_dir.join("assets"))
}

#[tauri::command]
fn campaign_integrity_report(campaign_id: String, state: State<'_, DbState>) -> Result<IntegrityReport, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::integrity_report(&conn, &campaign_id, &state.app_dir.join("assets"))
}

#[tauri::command]
fn preview_kitaba_update(json_text: String, state: State<'_, DbState>) -> Result<UpdatePreview, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::preview_update(&conn, &json_text)
}

#[tauri::command]
fn import_kitaba_update(json_text: String, state: State<'_, DbState>) -> Result<ImportResult, KitabaError> {
    let campaign_id = serde_json::from_str::<serde_json::Value>(&json_text).ok()
        .and_then(|v| v.get("campaign_id").and_then(|x| x.as_str()).map(str::to_owned));
    let mut conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    if let Some(ref cid) = campaign_id {
        if conn.query_row("SELECT 1 FROM campaigns WHERE id=?1", [cid], |r| r.get::<_, i64>(0)).is_ok() {
            let path = auto_backup_path(&state.app_dir, "pre-update")?;
            db::create_technical_backup(&conn, Some(cid), &path, "automatic_pre_update", &state.app_dir.join("assets"))?;
            prune_auto_backups(&state.app_dir, 30)?;
        }
    }
    db::apply_update(&mut conn, &json_text)
}

#[tauri::command]
fn export_kitaba_context(campaign_id: String, mode: String, state: State<'_, DbState>) -> Result<String, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::export_context(&conn, &campaign_id, &mode)
}


#[tauri::command]
fn list_entities(campaign_id: String, include_gm: bool, state: State<'_, DbState>) -> Result<Vec<EntityDocument>, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::list_entities(&conn, &campaign_id, include_gm)
}

#[tauri::command]
fn list_rest_points(campaign_id: String, state: State<'_, DbState>) -> Result<Vec<RestPointSummary>, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::list_rest_points(&conn, &campaign_id)
}

#[tauri::command]
fn list_audit_events(campaign_id: String, limit: Option<usize>, state: State<'_, DbState>) -> Result<Vec<AuditEvent>, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::list_audit_events(&conn, &campaign_id, limit.unwrap_or(50))
}

#[tauri::command]
fn rollback_death(campaign_id: String, rest_point_id: String, death_summary: Option<String>, state: State<'_, DbState>) -> Result<RollbackResult, KitabaError> {
    let mut conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    let path = auto_backup_path(&state.app_dir, "pre-rollback")?;
    db::create_technical_backup(&conn, Some(&campaign_id), &path, "automatic_pre_rollback", &state.app_dir.join("assets"))?;
    prune_auto_backups(&state.app_dir, 30)?;
    db::rollback_death(&mut conn, &campaign_id, &rest_point_id, death_summary.as_deref())
}


#[tauri::command]
fn create_technical_backup(campaign_id: Option<String>, output_path: String, reason: String, state: State<'_, DbState>) -> Result<(), KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::create_technical_backup(&conn, campaign_id.as_deref(), std::path::Path::new(&output_path), &reason, &state.app_dir.join("assets"))
}

#[tauri::command]
fn restore_technical_backup(input_path: String, state: State<'_, DbState>) -> Result<Vec<CampaignSummary>, KitabaError> {
    let auto_dir = state.app_dir.join("backups");
    std::fs::create_dir_all(&auto_dir).map_err(|e| KitabaError::Validation(e.to_string()))?;
    let auto_path = auto_dir.join(format!("pre-restore-{}.kitaba", chrono::Utc::now().format("%Y%m%d-%H%M%S")));
    let mut conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::create_technical_backup(&conn, None, &auto_path, "automatic_pre_restore", &state.app_dir.join("assets"))?;
    prune_auto_backups(&state.app_dir, 30)?;
    db::restore_technical_backup(&mut conn, std::path::Path::new(&input_path), &state.app_dir.join("assets"))?;
    db::list_campaigns(&conn)
}



#[tauri::command]
fn manual_patch_entity(
    campaign_id: String,
    entity_id: String,
    patch: serde_json::Value,
    expected_entity_version: i64,
    reason: String,
    visibility: String,
    override_immutable: Option<bool>,
    state: State<'_, DbState>,
) -> Result<ManualCorrectionResult, KitabaError> {
    let mut conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    let path = auto_backup_path(&state.app_dir, "pre-manual-correction")?;
    db::create_technical_backup(&conn, Some(&campaign_id), &path, "automatic_pre_manual_correction", &state.app_dir.join("assets"))?;
    prune_auto_backups(&state.app_dir, 30)?;
    db::manual_patch_entity(
        &mut conn, &campaign_id, &entity_id, patch, expected_entity_version, &reason, &visibility, override_immutable.unwrap_or(false)
    )
}

#[tauri::command]
fn record_context_export(campaign_id: String, mode: String, state: State<'_, DbState>) -> Result<(), KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::record_context_export(&conn, &campaign_id, &mode)
}

#[tauri::command]
fn save_kitaba_context(campaign_id: String, mode: String, output_path: String, state: State<'_, DbState>) -> Result<(), KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    let text = db::export_context(&conn, &campaign_id, &mode)?;
    let path = std::path::Path::new(&output_path);
    if let Some(parent) = path.parent() { std::fs::create_dir_all(parent)?; }
    std::fs::write(path, text)?;
    Ok(())
}

#[tauri::command]
fn read_text_file(input_path: String) -> Result<String, KitabaError> {
    let path = std::path::Path::new(&input_path);
    let meta = std::fs::metadata(path)?;
    if meta.len() > 10 * 1024 * 1024 { return Err(KitabaError::Validation("file is too large".into())); }
    Ok(std::fs::read_to_string(path)?)
}

#[tauri::command]
fn list_assets(campaign_id: String, state: State<'_, DbState>) -> Result<Vec<AssetSummary>, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::list_assets(&conn, &campaign_id)
}

#[tauri::command]
fn import_campaign_asset(campaign_id: String, kind: String, input_path: String, state: State<'_, DbState>) -> Result<AssetSummary, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::import_asset(&conn, &campaign_id, &kind, std::path::Path::new(&input_path), &state.app_dir.join("assets"))
}

#[tauri::command]
fn read_asset_data_url(campaign_id: String, asset_id: String, state: State<'_, DbState>) -> Result<String, KitabaError> {
    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;
    db::read_asset_data_url(&conn, &campaign_id, &asset_id, &state.app_dir.join("assets"))
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let app_dir: PathBuf = app.path().app_data_dir()?;
            fs::create_dir_all(&app_dir)?;
            let db_path = app_dir.join("kitaba.sqlite");
            let existed = db_path.exists() && std::fs::metadata(&db_path).map(|m| m.len() > 0).unwrap_or(false);
            let conn = Connection::open(&db_path)?;
            conn.execute_batch("PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL;")?;
            let schema_version = db::current_schema_version(&conn).map_err(|e| std::io::Error::other(e.to_string()))?;
            if existed && schema_version > 0 && schema_version < db::CURRENT_SCHEMA_VERSION {
                let path = auto_backup_path(&app_dir, "pre-migration").map_err(|e| std::io::Error::other(e.to_string()))?;
                db::create_technical_backup(&conn, None, &path, "automatic_pre_migration", &app_dir.join("assets"))
                    .map_err(|e| std::io::Error::other(e.to_string()))?;
                prune_auto_backups(&app_dir, 30).map_err(|e| std::io::Error::other(e.to_string()))?;
            }
            db::migrate(&conn).map_err(|e| std::io::Error::other(e.to_string()))?;
            app.manage(DbState { conn: Mutex::new(conn), app_dir });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![list_campaigns, create_campaign, list_archived_campaigns, set_campaign_archived, delete_campaign_permanently, campaign_integrity_report, preview_kitaba_update, import_kitaba_update, export_kitaba_context, list_entities, list_rest_points, list_audit_events, rollback_death, create_technical_backup, restore_technical_backup, save_kitaba_context, manual_patch_entity, record_context_export, read_text_file, list_assets, import_campaign_asset, read_asset_data_url])
        .run(tauri::generate_context!())
        .expect("error while running Kitaba Companion");
}
