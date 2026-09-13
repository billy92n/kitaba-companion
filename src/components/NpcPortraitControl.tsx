import { useCallback, useEffect, useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { backend } from "../lib/backend";
import "../npc-portrait-control.css";

const VISUAL_BINDINGS_CHANGED_EVENT = "kitaba-visual-bindings-changed";

type Props = {
  subjectEntityId: string;
  name: string;
};

async function resolveCampaignId(): Promise<string | null> {
  const selected = document.querySelector<HTMLSelectElement>(".campaign-select")?.value;
  if (selected) return selected;
  const campaigns = await backend.listCampaigns();
  return campaigns[0]?.id ?? null;
}

export function NpcPortraitControl({ subjectEntityId, name }: Props) {
  const [url, setUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [hasPortrait, setHasPortrait] = useState(false);

  const reload = useCallback(async () => {
    const campaignId = await resolveCampaignId();
    if (!campaignId) {
      setUrl(null);
      setHasPortrait(false);
      return;
    }
    const bindings = await backend.listVisualAssetBindings(campaignId);
    const binding = bindings
      .filter((row) => row.subject_entity_id === subjectEntityId && row.role === "primary_reference")
      .sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0];
    if (!binding) {
      setUrl(null);
      setHasPortrait(false);
      return;
    }
    try {
      setUrl(await backend.readAssetDataUrl(campaignId, binding.asset_id));
      setHasPortrait(true);
    } catch {
      setUrl(null);
      setHasPortrait(false);
    }
  }, [subjectEntityId]);

  useEffect(() => {
    reload().catch(() => undefined);
    const refresh = () => reload().catch(() => undefined);
    window.addEventListener(VISUAL_BINDINGS_CHANGED_EVENT, refresh);
    return () => window.removeEventListener(VISUAL_BINDINGS_CHANGED_EVENT, refresh);
  }, [reload]);

  async function choosePortrait() {
    if (busy) return;
    setBusy(true);
    try {
      const campaignId = await resolveCampaignId();
      if (!campaignId) return;
      const path = await open({
        title: hasPortrait ? `Changer le portrait de ${name}` : `Ajouter le portrait de ${name}`,
        multiple: false,
        directory: false,
        filters: [{ name: "Image", extensions: ["png", "jpg", "jpeg", "webp"] }],
      });
      if (!path || Array.isArray(path)) return;
      const asset = await backend.importCampaignAsset(campaignId, "npc_portrait", path);
      await backend.bindVisualAsset(
        campaignId,
        asset.id,
        subjectEntityId,
        "primary_reference",
        "normal",
        `Portrait de ${name}`,
      );
      window.dispatchEvent(new CustomEvent(VISUAL_BINDINGS_CHANGED_EVENT, { detail: { campaignId } }));
      await reload();
    } finally {
      setBusy(false);
    }
  }

  return <div className="npc-portrait-control">
    {url
      ? <img className="npc-avatar-image" src={url} alt={`Portrait de ${name}`} />
      : <div className="npc-avatar" aria-label={`Aucun portrait pour ${name}`}>{name.slice(0, 1).toUpperCase()}</div>}
    <button className="ghost small npc-portrait-action" onClick={choosePortrait} disabled={busy}>
      {hasPortrait ? "Changer" : "Ajouter un portrait"}
    </button>
  </div>;
}
