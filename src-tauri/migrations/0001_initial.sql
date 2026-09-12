PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE campaigns (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  current_revision INTEGER NOT NULL DEFAULT 0 CHECK (current_revision >= 0),
  current_timeline_id TEXT NOT NULL,
  game_time TEXT,
  last_update_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT
);

CREATE TABLE timelines (
  id TEXT PRIMARY KEY,
  campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  parent_timeline_id TEXT REFERENCES timelines(id),
  restored_from_rest_point_id TEXT,
  status TEXT NOT NULL CHECK (status IN ('ACTIVE','DEAD','ARCHIVED')),
  started_revision INTEGER NOT NULL,
  ended_revision INTEGER,
  created_at TEXT NOT NULL
);

CREATE TABLE entity_documents (
  id TEXT NOT NULL,
  campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  entity_type TEXT NOT NULL,
  visibility TEXT NOT NULL CHECK (visibility IN ('PLAYER','GM')),
  entity_version INTEGER NOT NULL DEFAULT 1 CHECK (entity_version >= 1),
  data_json TEXT NOT NULL,
  archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0,1)),
  created_by_update_id TEXT,
  updated_by_update_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (campaign_id, id)
);

CREATE INDEX idx_entities_campaign_type ON entity_documents(campaign_id, entity_type, archived);
CREATE INDEX idx_entities_campaign_visibility ON entity_documents(campaign_id, visibility, archived);

CREATE TABLE entity_links (
  id TEXT PRIMARY KEY,
  campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  from_entity_id TEXT NOT NULL,
  to_entity_id TEXT NOT NULL,
  link_type TEXT NOT NULL,
  visibility TEXT NOT NULL CHECK (visibility IN ('PLAYER','GM')),
  data_json TEXT NOT NULL DEFAULT '{}',
  archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0,1)),
  created_by_update_id TEXT,
  updated_by_update_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_links_campaign_from ON entity_links(campaign_id, from_entity_id, archived);
CREATE INDEX idx_links_campaign_to ON entity_links(campaign_id, to_entity_id, archived);

CREATE TABLE applied_updates (
  update_id TEXT PRIMARY KEY,
  campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  timeline_id TEXT NOT NULL REFERENCES timelines(id),
  base_revision INTEGER NOT NULL,
  target_revision INTEGER NOT NULL,
  payload_sha256 TEXT NOT NULL,
  applied_at TEXT NOT NULL
);
CREATE INDEX idx_updates_campaign_revision ON applied_updates(campaign_id, target_revision);

CREATE TABLE rest_points (
  id TEXT PRIMARY KEY,
  campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  timeline_id TEXT NOT NULL REFERENCES timelines(id),
  source_update_id TEXT REFERENCES applied_updates(update_id),
  snapshot_revision INTEGER NOT NULL,
  game_time TEXT,
  location TEXT,
  description TEXT NOT NULL,
  snapshot_json TEXT NOT NULL,
  snapshot_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL,
  invalidated_at TEXT
);
CREATE INDEX idx_rest_campaign_created ON rest_points(campaign_id, created_at);

CREATE TABLE dead_timelines (
  id TEXT PRIMARY KEY,
  campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  timeline_id TEXT NOT NULL REFERENCES timelines(id),
  died_at_revision INTEGER NOT NULL,
  death_summary TEXT,
  state_snapshot_json TEXT NOT NULL,
  state_snapshot_sha256 TEXT NOT NULL,
  rolled_back_to_rest_point_id TEXT REFERENCES rest_points(id),
  created_at TEXT NOT NULL
);

CREATE TABLE dead_timeline_resolutions (
  id TEXT PRIMARY KEY,
  campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  source_timeline_id TEXT NOT NULL,
  checkpoint_id TEXT REFERENCES rest_points(id),
  state_fingerprint TEXT NOT NULL,
  action_fingerprint TEXT NOT NULL,
  context_json TEXT NOT NULL,
  result_json TEXT NOT NULL,
  consequences_json TEXT NOT NULL,
  source_update_id TEXT,
  notes TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(campaign_id, checkpoint_id, state_fingerprint, action_fingerprint)
);
CREATE INDEX idx_dead_resolution_lookup ON dead_timeline_resolutions(
  campaign_id, checkpoint_id, state_fingerprint, action_fingerprint
);

CREATE TABLE technical_backups (
  id TEXT PRIMARY KEY,
  campaign_id TEXT REFERENCES campaigns(id) ON DELETE SET NULL,
  reason TEXT NOT NULL,
  file_name TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE audit_log (
  id TEXT PRIMARY KEY,
  campaign_id TEXT REFERENCES campaigns(id) ON DELETE CASCADE,
  timeline_id TEXT,
  event_type TEXT NOT NULL,
  summary TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);
CREATE INDEX idx_audit_campaign_created ON audit_log(campaign_id, created_at);

CREATE TABLE assets (
  id TEXT PRIMARY KEY,
  campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  mime_type TEXT,
  sha256 TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(campaign_id, relative_path)
);
