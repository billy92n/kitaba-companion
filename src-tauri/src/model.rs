use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CampaignSummary {
    pub id: String,
    pub name: String,
    pub current_revision: i64,
    pub current_timeline_id: String,
    pub game_time: Option<String>,
    pub death_pending: bool,
    pub death_summary: Option<String>,
    pub last_gm_export_revision: Option<i64>,
    pub last_gm_export_at: Option<String>,
    pub last_player_export_revision: Option<i64>,
    pub last_player_export_at: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GameTimeUpdate {
    pub set: Option<String>,
    pub elapsed_minutes: Option<i64>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Operation {
    pub op: String,
    pub entity_type: String,
    pub entity_id: String,
    pub expected_entity_version: Option<i64>,
    pub data: Option<Value>,
    pub source_gm_entity_id: Option<String>,
    pub protection: Option<String>,
    pub override_immutable: Option<bool>,
    pub override_reason: Option<String>,
}


#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LinkOperation {
    pub op: String,
    pub link_id: String,
    pub from_entity_id: Option<String>,
    pub to_entity_id: Option<String>,
    pub link_type: Option<String>,
    pub data: Option<Value>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CheckpointRequest {
    pub id: String,
    pub location: Option<String>,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct UpdateNotification {
    pub level: String,
    pub message: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct KitabaUpdate {
    pub format: String,
    pub protocol_version: i64,
    pub campaign_id: String,
    pub timeline_id: String,
    pub update_id: String,
    pub base_revision: i64,
    pub target_revision: i64,
    pub game_time: Option<GameTimeUpdate>,
    pub operations: Vec<Operation>,
    pub gm_operations: Vec<Operation>,
    #[serde(default)]
    pub link_operations: Vec<LinkOperation>,
    #[serde(default)]
    pub gm_link_operations: Vec<LinkOperation>,
    #[serde(default)]
    pub journal_entries: Vec<Value>,
    #[serde(default)]
    pub notifications: Vec<UpdateNotification>,
    #[serde(default)]
    pub dead_timeline_resolutions: Vec<Value>,
    pub checkpoint: Option<CheckpointRequest>,
    pub death: Option<Value>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ImportResult {
    pub revision: i64,
    pub timeline_id: String,
    pub update_id: String,
    pub player_operation_count: usize,
    pub gm_operation_count: usize,
    pub notifications: Vec<UpdateNotification>,
}

#[derive(Debug, Clone, Serialize)]
pub struct UpdatePreview {
    pub campaign_id: String,
    pub timeline_id: String,
    pub update_id: String,
    pub base_revision: i64,
    pub target_revision: i64,
    pub player_operation_count: usize,
    pub gm_operation_count: usize,
    pub player_link_operation_count: usize,
    pub gm_link_operation_count: usize,
    pub journal_entry_count: usize,
    pub notification_count: usize,
    pub dead_resolution_count: usize,
    pub creates_checkpoint: bool,
    pub marks_death: bool,
    pub player_changes: Vec<String>,
}


#[derive(Debug, Clone, Serialize)]
pub struct EntityDocument {
    pub id: String,
    pub entity_type: String,
    pub visibility: String,
    pub entity_version: i64,
    pub protection: String,
    pub data: Value,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct RestPointSummary {
    pub id: String,
    pub timeline_id: String,
    pub snapshot_revision: i64,
    pub game_time: Option<String>,
    pub location: Option<String>,
    pub description: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct AuditEvent {
    pub id: String,
    pub event_type: String,
    pub summary: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct RollbackResult {
    pub revision: i64,
    pub timeline_id: String,
    pub restored_rest_point_id: String,
}


#[derive(Debug, Clone, Serialize)]
pub struct ManualCorrectionResult {
    pub correction_id: String,
    pub campaign_revision: i64,
    pub entity_id: String,
    pub entity_version: i64,
}

#[derive(Debug, Clone, Serialize)]
pub struct AssetSummary {
    pub id: String,
    pub campaign_id: String,
    pub kind: String,
    pub relative_path: String,
    pub mime_type: Option<String>,
    pub sha256: Option<String>,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct IntegrityCheck {
    pub code: String,
    pub ok: bool,
    pub message: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct IntegrityReport {
    pub campaign_id: String,
    pub checked_at: String,
    pub ok: bool,
    pub checks: Vec<IntegrityCheck>,
}
