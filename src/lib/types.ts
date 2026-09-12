export type ContextMode = "PLAYER" | "GM_FULL";
export type Visibility = "PLAYER" | "GM";

export interface CampaignSummary {
  id: string;
  name: string;
  current_revision: number;
  current_timeline_id: string;
  game_time: string | null;
  death_pending: boolean;
  death_summary: string | null;
  last_gm_export_revision: number | null;
  last_gm_export_at: string | null;
  last_player_export_revision: number | null;
  last_player_export_at: string | null;
}

export interface UpdateNotification {
  level: "info" | "warning" | "success";
  message: string;
}

export interface ImportResult {
  revision: number;
  timeline_id: string;
  update_id: string;
  player_operation_count: number;
  gm_operation_count: number;
  notifications: UpdateNotification[];
}

export interface EntityDocument {
  id: string;
  entity_type: string;
  visibility: Visibility;
  entity_version: number;
  protection: "NORMAL" | "PROTECTED" | "IMMUTABLE";
  data: Record<string, unknown>;
  updated_at: string;
}

export interface RestPointSummary {
  id: string;
  timeline_id: string;
  snapshot_revision: number;
  game_time: string | null;
  location: string | null;
  description: string;
  created_at: string;
}


export interface AssetSummary {
  id: string;
  campaign_id: string;
  kind: "world_map" | "player_portrait" | "npc_portrait" | "other_image" | string;
  relative_path: string;
  mime_type: string | null;
  sha256: string | null;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  summary: string;
  created_at: string;
}



export interface IntegrityCheck {
  code: string;
  ok: boolean;
  message: string;
}

export interface IntegrityReport {
  campaign_id: string;
  checked_at: string;
  ok: boolean;
  checks: IntegrityCheck[];
}

export interface ManualCorrectionResult {
  correction_id: string;
  campaign_revision: number;
  entity_id: string;
  entity_version: number;
}

export interface RollbackResult {
  revision: number;
  timeline_id: string;
  restored_rest_point_id: string;
}

export interface UpdatePreview {
  campaign_id: string;
  timeline_id: string;
  update_id: string;
  base_revision: number;
  target_revision: number;
  player_operation_count: number;
  gm_operation_count: number;
  player_link_operation_count: number;
  gm_link_operation_count: number;
  journal_entry_count: number;
  notification_count: number;
  dead_resolution_count: number;
  creates_checkpoint: boolean;
  marks_death: boolean;
  player_changes: string[];
}

export type SectionKey =
  | "overview"
  | "character"
  | "skills"
  | "magic"
  | "inventory"
  | "relations"
  | "journal"
  | "missions"
  | "knowledge"
  | "map"
  | "timeline"
  | "adventurer_card"
  | "checkpoints"
  | "sync"
  | "gm_vault";
