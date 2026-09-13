import { useEffect, useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { backend } from "../lib/backend";
import type { AssetSummary, CampaignSummary, EntityDocument } from "../lib/types";
import { VisualLibrary } from "./VisualLibrary";
import "../visual-reference-dock.css";

type VisualKind = "world_map" | "player_portrait" | "npc_portrait" | "other_image";

function selectedCampaignFromMainUi() {
  const select = document.querySelector<HTMLSelectElement>(".campaign-select");
  return select?.value || null;
}

export function VisualReferenceDock() {
  const [openDock, setOpenDock] = useState(false);
  const [campaigns, setCampaigns] = useState<CampaignSummary[]>([]);
  const [campaignId, setCampaignId] = useState("");
  const [entities, setEntities] = useState<EntityDocument[]>([]);
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewAssetId, setPreviewAssetId] = useState<string | null>(null);
  const [status, setStatus] = useState("Prêt.");
  const characterInitialized = entities.some((entity) => entity.entity_type === "player_character");

  async function loadCampaignData(id: string) {
    if (!id) return;
    setEntities([]);
    setAssets([]);
    setPreviewUrl(null);
    setPreviewAssetId(null);
    const [rows, assetRows] = await Promise.all([
      backend.listEntities(id, false),
      backend.listAssets(id),
    ]);
    setEntities(rows);
    setAssets(assetRows);
  }

  async function openPanel() {
    setOpenDock(true);
    setEntities([]);
    setAssets([]);
    try {
      const rows = await backend.listCampaigns();
      setCampaigns(rows);
      const mainSelected = selectedCampaignFromMainUi();
      const nextId = rows.some((row) => row.id === mainSelected) ? mainSelected! : rows[0]?.id ?? "";
      setCampaignId(nextId);
      if (nextId) await loadCampaignData(nextId);
    } catch (error) {
      setStatus(`Chargement impossible : ${String(error)}`);
    }
  }

  useEffect(() => {
    if (!openDock || !campaignId) return;
    loadCampaignData(campaignId).catch((error) => setStatus(`Chargement impossible : ${String(error)}`));
  }, [campaignId]);

  async function importVisual(kind: VisualKind) {
    if (!campaignId) return;
    if (kind !== "world_map" && !characterInitialized) {
      setStatus("Portraits et illustrations restent verrouillés tant que l'apparence du personnage n'a pas été établie dans le canon joueur.");
      return;
    }
    const titles: Record<VisualKind, string> = {
      world_map: "Importer le fond de carte",
      player_portrait: "Importer le portrait du personnage",
      npc_portrait: "Importer un portrait de PNJ",
      other_image: "Importer une illustration",
    };
    try {
      const path = await open({
        title: titles[kind],
        multiple: false,
        directory: false,
        filters: [{ name: "Image", extensions: ["png", "jpg", "jpeg", "webp"] }],
      });
      if (!path || Array.isArray(path)) return;
      await backend.importCampaignAsset(campaignId, kind, path);
      await loadCampaignData(campaignId);
      setStatus("Visuel importé. Associe-le à un personnage ou un lieu pour en faire une référence persistante.");
    } catch (error) {
      setStatus(`Import impossible : ${String(error)}`);
    }
  }

  async function preview(asset: AssetSummary) {
    if (!campaignId) return;
    try {
      setPreviewUrl(await backend.readAssetDataUrl(campaignId, asset.id));
      setPreviewAssetId(asset.id);
    } catch (error) {
      setStatus(`Prévisualisation impossible : ${String(error)}`);
    }
  }

  return <>
    <button className="visual-reference-launcher" onClick={openPanel} aria-label="Ouvrir les références visuelles">Références visuelles</button>
    {openDock && <div className="visual-reference-overlay" role="dialog" aria-modal="true" aria-label="Références visuelles de campagne">
      <div className="visual-reference-modal">
        <header className="visual-reference-modal-head">
          <div><div className="eyebrow">MVP · continuité visuelle</div><h2>Identités & illustrations</h2></div>
          <div className="action-row">
            {campaigns.length > 1 && <select value={campaignId} onChange={(event) => setCampaignId(event.target.value)}>{campaigns.map((campaign) => <option key={campaign.id} value={campaign.id}>{campaign.name}</option>)}</select>}
            <button className="ghost" onClick={() => setOpenDock(false)}>Fermer</button>
          </div>
        </header>
        {!campaignId ? <div className="empty-inline">Aucune campagne active.</div> : !characterInitialized ? <section className="panel">
          <div className="eyebrow">Canon avant image</div>
          <h3>Références visuelles verrouillées pour l'instant</h3>
          <p className="muted">Crée et initialise d'abord le personnage avec le MJ. Les portraits et illustrations deviennent disponibles une fois leur sujet établi dans le canon joueur ; une image ne doit jamais inventer une apparence indécidée.</p>
        </section> : <VisualLibrary
          campaignId={campaignId}
          entities={entities}
          assets={assets}
          previewUrl={previewUrl}
          previewAssetId={previewAssetId}
          onImport={importVisual}
          onPreview={preview}
          onStatus={setStatus}
        />}
        <div className="visual-reference-status" aria-live="polite">{status}</div>
      </div>
    </div>}
  </>;
}
