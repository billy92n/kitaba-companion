use chrono::Utc;
use rusqlite::{params, Connection, OptionalExtension};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use uuid::Uuid;

use crate::error::KitabaError;

pub const VISUAL_BINDINGS_META_KIND: &str = "visual_bindings_meta";
const VISUAL_BINDINGS_VERSION: u32 = 1;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct VisualAssetBinding {
    pub asset_id: String,
    pub subject_entity_id: String,
    pub role: String,
    pub state: String,
    pub caption: Option<String>,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct VisualBindingsFile {
    version: u32,
    bindings: Vec<VisualAssetBinding>,
}

fn metadata_relative_path(campaign_id: &str) -> String {
    format!("{campaign_id}/visual-bindings.json")
}

fn metadata_path(asset_root: &std::path::Path, campaign_id: &str) -> std::path::PathBuf {
    asset_root.join(metadata_relative_path(campaign_id))
}

fn read_file(asset_root: &std::path::Path, campaign_id: &str) -> Result<VisualBindingsFile, KitabaError> {
    let path = metadata_path(asset_root, campaign_id);
    if !path.exists() {
        return Ok(VisualBindingsFile { version: VISUAL_BINDINGS_VERSION, bindings: Vec::new() });
    }
    let raw = std::fs::read_to_string(path)?;
    let parsed: VisualBindingsFile = serde_json::from_str(&raw)?;
    if parsed.version != VISUAL_BINDINGS_VERSION {
        return Err(KitabaError::Validation(format!("unsupported visual bindings version: {}", parsed.version)));
    }
    Ok(parsed)
}

fn write_file(
    conn: &Connection,
    asset_root: &std::path::Path,
    campaign_id: &str,
    file: &VisualBindingsFile,
) -> Result<(), KitabaError> {
    let path = metadata_path(asset_root, campaign_id);
    if let Some(parent) = path.parent() { std::fs::create_dir_all(parent)?; }
    let bytes = serde_json::to_vec_pretty(file)?;
    let temp = path.with_extension(format!("{}.tmp", Uuid::new_v4()));
    std::fs::write(&temp, &bytes)?;
    if path.exists() { std::fs::remove_file(&path)?; }
    std::fs::rename(&temp, &path)?;

    let digest = hex::encode(Sha256::digest(&bytes));
    let relative = metadata_relative_path(campaign_id);
    let now = Utc::now().to_rfc3339();
    conn.execute(
        "INSERT INTO assets(id,campaign_id,kind,relative_path,mime_type,sha256,created_at) VALUES (?1,?2,?3,?4,'application/json',?5,?6) \
         ON CONFLICT(campaign_id,relative_path) DO UPDATE SET kind=excluded.kind,mime_type=excluded.mime_type,sha256=excluded.sha256",
        params![format!("visual-bindings-meta-{campaign_id}"), campaign_id, VISUAL_BINDINGS_META_KIND, relative, digest, now],
    )?;
    Ok(())
}

pub fn list_bindings(
    conn: &Connection,
    campaign_id: &str,
    asset_root: &std::path::Path,
) -> Result<Vec<VisualAssetBinding>, KitabaError> {
    let exists = conn.query_row("SELECT 1 FROM campaigns WHERE id=?1", [campaign_id], |r| r.get::<_, i64>(0)).optional()?;
    if exists.is_none() { return Err(KitabaError::CampaignNotFound); }
    Ok(read_file(asset_root, campaign_id)?.bindings)
}

pub fn bind_asset(
    conn: &Connection,
    campaign_id: &str,
    asset_id: &str,
    subject_entity_id: &str,
    role: &str,
    state: Option<&str>,
    caption: Option<&str>,
    asset_root: &std::path::Path,
) -> Result<VisualAssetBinding, KitabaError> {
    const ROLES: &[&str] = &["primary_reference", "state_variant", "scene_reference", "place_reference", "historical_reference"];
    if !ROLES.contains(&role) {
        return Err(KitabaError::Validation(format!("unsupported visual binding role: {role}")));
    }
    let asset_kind: Option<String> = conn.query_row(
        "SELECT kind FROM assets WHERE campaign_id=?1 AND id=?2",
        params![campaign_id, asset_id], |r| r.get(0),
    ).optional()?;
    let asset_kind = asset_kind.ok_or_else(|| KitabaError::Validation("visual asset not found in this campaign".into()))?;
    if asset_kind == VISUAL_BINDINGS_META_KIND {
        return Err(KitabaError::Validation("technical visual metadata cannot be bound as an illustration".into()));
    }

    let visibility: Option<String> = conn.query_row(
        "SELECT visibility FROM entity_documents WHERE campaign_id=?1 AND id=?2 AND archived=0",
        params![campaign_id, subject_entity_id], |r| r.get(0),
    ).optional()?;
    match visibility.as_deref() {
        Some("PLAYER") => {}
        Some("GM") => return Err(KitabaError::Validation("player visual bindings cannot target a GM-only entity".into())),
        _ => return Err(KitabaError::Validation("visual subject entity not found".into())),
    }

    let state = state.unwrap_or("normal").trim();
    if state.is_empty() || state.len() > 80 {
        return Err(KitabaError::Validation("visual state must contain 1..80 characters".into()));
    }
    let caption = caption.map(str::trim).filter(|x| !x.is_empty()).map(str::to_owned);
    if caption.as_ref().is_some_and(|x| x.len() > 240) {
        return Err(KitabaError::Validation("visual caption is too long".into()));
    }

    let mut file = read_file(asset_root, campaign_id)?;
    let now = Utc::now().to_rfc3339();
    let binding = VisualAssetBinding {
        asset_id: asset_id.to_owned(),
        subject_entity_id: subject_entity_id.to_owned(),
        role: role.to_owned(),
        state: state.to_owned(),
        caption,
        updated_at: now,
    };
    if let Some(existing) = file.bindings.iter_mut().find(|x| x.asset_id == asset_id) {
        *existing = binding.clone();
    } else {
        file.bindings.push(binding.clone());
    }
    file.bindings.sort_by(|a, b| a.subject_entity_id.cmp(&b.subject_entity_id).then(a.role.cmp(&b.role)).then(a.asset_id.cmp(&b.asset_id)));
    write_file(conn, asset_root, campaign_id, &file)?;
    Ok(binding)
}

pub fn unbind_asset(
    conn: &Connection,
    campaign_id: &str,
    asset_id: &str,
    asset_root: &std::path::Path,
) -> Result<(), KitabaError> {
    let mut file = read_file(asset_root, campaign_id)?;
    let before = file.bindings.len();
    file.bindings.retain(|x| x.asset_id != asset_id);
    if file.bindings.len() != before {
        write_file(conn, asset_root, campaign_id, &file)?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db;
    use std::io::Read;

    fn setup() -> (Connection, String, std::path::PathBuf) {
        let conn = Connection::open_in_memory().unwrap();
        conn.execute_batch("PRAGMA foreign_keys=ON;").unwrap();
        db::migrate(&conn).unwrap();
        let campaign = db::create_campaign(&conn, "Visual test").unwrap();
        let now = Utc::now().to_rfc3339();
        conn.execute(
            "INSERT INTO entity_documents(id,campaign_id,entity_type,visibility,entity_version,data_json,archived,created_at,updated_at) VALUES ('npc-1',?1,'npc','PLAYER',1,'{\"name\":\"Ari\"}',0,?2,?2)",
            params![campaign.id, now],
        ).unwrap();
        conn.execute(
            "INSERT INTO assets(id,campaign_id,kind,relative_path,mime_type,sha256,created_at) VALUES ('asset-1',?1,'npc_portrait',?2,'image/png',NULL,?3)",
            params![campaign.id, format!("{}/asset-1.png", campaign.id), now],
        ).unwrap();
        let root = std::env::temp_dir().join(format!("kitaba-visual-test-{}", Uuid::new_v4()));
        (conn, campaign.id, root)
    }

    #[test]
    fn binding_roundtrip_uses_player_entity_and_registered_asset() {
        let (conn, campaign_id, root) = setup();
        let bound = bind_asset(&conn, &campaign_id, "asset-1", "npc-1", "primary_reference", Some("normal"), Some("Référence"), &root).unwrap();
        assert_eq!(bound.subject_entity_id, "npc-1");
        assert_eq!(list_bindings(&conn, &campaign_id, &root).unwrap(), vec![bound]);
        let meta: String = conn.query_row(
            "SELECT kind FROM assets WHERE campaign_id=?1 AND relative_path=?2",
            params![campaign_id, metadata_relative_path(&campaign_id)], |r| r.get(0),
        ).unwrap();
        assert_eq!(meta, VISUAL_BINDINGS_META_KIND);
        unbind_asset(&conn, &campaign_id, "asset-1", &root).unwrap();
        assert!(list_bindings(&conn, &campaign_id, &root).unwrap().is_empty());
        let _ = std::fs::remove_dir_all(root);
    }

    #[test]
    fn gm_only_subject_is_rejected() {
        let (conn, campaign_id, root) = setup();
        let now = Utc::now().to_rfc3339();
        conn.execute(
            "INSERT INTO entity_documents(id,campaign_id,entity_type,visibility,entity_version,data_json,archived,created_at,updated_at) VALUES ('secret-1',?1,'npc','GM',1,'{}',0,?2,?2)",
            params![campaign_id, now],
        ).unwrap();
        let err = bind_asset(&conn, &campaign_id, "asset-1", "secret-1", "primary_reference", None, None, &root).unwrap_err();
        assert!(err.to_string().contains("GM-only"));
        let _ = std::fs::remove_dir_all(root);
    }

    #[test]
    fn visual_binding_metadata_survives_campaign_backup_and_restore() {
        let (conn, campaign_id, root) = setup();
        let image_path = root.join(&campaign_id).join("asset-1.png");
        std::fs::create_dir_all(image_path.parent().unwrap()).unwrap();
        std::fs::write(&image_path, b"visual-reference-bytes").unwrap();
        let bound = bind_asset(&conn, &campaign_id, "asset-1", "npc-1", "primary_reference", Some("normal"), None, &root).unwrap();

        let backup = std::env::temp_dir().join(format!("kitaba-visual-backup-{}.kitaba", Uuid::new_v4()));
        db::create_technical_backup(&conn, Some(&campaign_id), &backup, "visual-binding-test", &root).unwrap();

        let file = std::fs::File::open(&backup).unwrap();
        let mut archive = zip::ZipArchive::new(file).unwrap();
        let metadata_name = format!("assets/{}/visual-bindings.json", campaign_id);
        let mut metadata = String::new();
        archive.by_name(&metadata_name).unwrap().read_to_string(&mut metadata).unwrap();
        assert!(metadata.contains("primary_reference"));
        drop(archive);

        let mut restored = Connection::open_in_memory().unwrap();
        restored.execute_batch("PRAGMA foreign_keys=ON;").unwrap();
        db::migrate(&restored).unwrap();
        let restored_root = std::env::temp_dir().join(format!("kitaba-visual-restored-{}", Uuid::new_v4()));
        db::restore_technical_backup(&mut restored, &backup, &restored_root).unwrap();
        assert_eq!(list_bindings(&restored, &campaign_id, &restored_root).unwrap(), vec![bound]);

        let _ = std::fs::remove_dir_all(root);
        let _ = std::fs::remove_dir_all(restored_root);
        let _ = std::fs::remove_file(backup);
    }
}
