import { invoke } from "@tauri-apps/api/core";
import type {
  AssetSummary,
  AuditEvent,
  CampaignSummary,
  ContextMode,
  EntityDocument,
  ImportResult,
  IntegrityReport,
  ManualCorrectionResult,
  RestPointSummary,
  RollbackResult,
  UpdatePreview,
} from "./types";

export const backend = {
  listCampaigns: () => invoke<CampaignSummary[]>("list_campaigns"),
  createCampaign: (name: string) => invoke<CampaignSummary>("create_campaign", { name }),
  listArchivedCampaigns: () => invoke<CampaignSummary[]>("list_archived_campaigns"),
  setCampaignArchived: (campaignId: string, archived: boolean) => invoke<void>("set_campaign_archived", { campaignId, archived }),
  deleteCampaignPermanently: (campaignId: string, expectedName: string) => invoke<void>("delete_campaign_permanently", { campaignId, expectedName }),
  campaignIntegrityReport: (campaignId: string) => invoke<IntegrityReport>("campaign_integrity_report", { campaignId }),
  previewUpdate: (jsonText: string) => invoke<UpdatePreview>("preview_kitaba_update", { jsonText }),
  importUpdate: (jsonText: string) => invoke<ImportResult>("import_kitaba_update", { jsonText }),
  exportContext: (campaignId: string, mode: ContextMode) =>
    invoke<string>("export_kitaba_context", { campaignId, mode }),
  saveContext: (campaignId: string, mode: ContextMode, outputPath: string) =>
    invoke<void>("save_kitaba_context", { campaignId, mode, outputPath }),
  readTextFile: (inputPath: string) => invoke<string>("read_text_file", { inputPath }),
  listEntities: (campaignId: string, includeGm = false) =>
    invoke<EntityDocument[]>("list_entities", { campaignId, includeGm }),

  listAssets: (campaignId: string) => invoke<AssetSummary[]>("list_assets", { campaignId }),
  importCampaignAsset: (campaignId: string, kind: string, inputPath: string) =>
    invoke<AssetSummary>("import_campaign_asset", { campaignId, kind, inputPath }),
  readAssetDataUrl: (campaignId: string, assetId: string) =>
    invoke<string>("read_asset_data_url", { campaignId, assetId }),
  manualPatchEntity: (campaignId: string, entityId: string, patch: Record<string, unknown>, expectedEntityVersion: number, reason: string, visibility: "PLAYER" | "GM", overrideImmutable = false) =>
    invoke<ManualCorrectionResult>("manual_patch_entity", { campaignId, entityId, patch, expectedEntityVersion, reason, visibility, overrideImmutable }),
  listRestPoints: (campaignId: string) =>
    invoke<RestPointSummary[]>("list_rest_points", { campaignId }),
  listAuditEvents: (campaignId: string, limit = 50) =>
    invoke<AuditEvent[]>("list_audit_events", { campaignId, limit }),
  rollbackDeath: (campaignId: string, restPointId: string, deathSummary?: string) =>
    invoke<RollbackResult>("rollback_death", { campaignId, restPointId, deathSummary: deathSummary ?? null }),
  createTechnicalBackup: (campaignId: string | null, outputPath: string, reason: string) =>
    invoke<void>("create_technical_backup", { campaignId, outputPath, reason }),
  restoreTechnicalBackup: (inputPath: string) =>
    invoke<CampaignSummary[]>("restore_technical_backup", { inputPath }),
  recordContextExport: (campaignId: string, mode: ContextMode) =>
    invoke<void>("record_context_export", { campaignId, mode }),
};
