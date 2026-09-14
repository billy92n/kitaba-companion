import { useCallback, useEffect, useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { backend } from "../lib/backend";
import type { AssetSummary, VisualAssetBinding } from "../lib/types";
import "../npc-portrait-control.css";

const VISUAL_BINDINGS_CHANGED_EVENT = "kitaba-visual-bindings-changed";

type Props = {
  subjectEntityId: string;
  name: string;
  currentState?: string | null;
};

type Candidate = {
  asset: AssetSummary;
  url: string;
};

async function resolveCampaignId(): Promise<string | null> {
  const selected = document.querySelector<HTMLSelectElement>(".campaign-select")?.value;
  if (selected) return selected;
  const campaigns = await backend.listCampaigns();
  return campaigns[0]?.id ?? null;
}

function normalize(value: string | null | undefined) {
  return (value ?? "").trim().toLocaleLowerCase("fr");
}

function displayedPortrait(bindings: VisualAssetBinding[], subjectEntityId: string, currentState?: string | null) {
  const subject = bindings.filter((row) => row.subject_entity_id === subjectEntityId);
  const normalizedState = normalize(currentState);
  if (normalizedState && normalizedState !== "normal") {
    const matchingVariant = subject
      .filter((row) => row.role === "state_variant" && normalize(row.state) === normalizedState)
      .sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0];
    if (matchingVariant) return matchingVariant;
  }
  return subject
    .filter((row) => row.role === "primary_reference")
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0];
}

function hasPrimaryPortrait(bindings: VisualAssetBinding[], subjectEntityId: string) {
  return bindings.some((row) => row.subject_entity_id === subjectEntityId && row.role === "primary_reference");
}

export function NpcPortraitControl({ subjectEntityId, name, currentState }: Props) {
  const [url, setUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [hasPortrait, setHasPortrait] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>([]);

  const reload = useCallback(async () => {
    const campaignId = await resolveCampaignId();
    if (!campaignId) {
      setUrl(null);
      setHasPortrait(false);
      return;
    }
    const bindings = await backend.listVisualAssetBindings(campaignId);
    setHasPortrait(hasPrimaryPortrait(bindings, subjectEntityId));
    const binding = displayedPortrait(bindings, subjectEntityId, currentState);
    if (!binding) {
      setUrl(null);
      return;
    }
    try {
      setUrl(await backend.readAssetDataUrl(campaignId, binding.asset_id));
    } catch {
      setUrl(null);
    }
  }, [subjectEntityId, currentState]);

  useEffect(() => {
    reload().catch(() => undefined);
    const refresh = () => reload().catch(() => undefined);
    window.addEventListener(VISUAL_BINDINGS_CHANGED_EVENT, refresh);
    return () => window.removeEventListener(VISUAL_BINDINGS_CHANGED_EVENT, refresh);
  }, [reload]);

  async function bindPortrait(campaignId: string, assetId: string) {
    const bindings = await backend.listVisualAssetBindings(campaignId);
    const previousPrimary = bindings.filter((binding) =>
      binding.subject_entity_id === subjectEntityId
      && binding.role === "primary_reference"
      && binding.asset_id !== assetId
    );
    for (const binding of previousPrimary) await backend.unbindVisualAsset(campaignId, binding.asset_id);

    await backend.bindVisualAsset(
      campaignId,
      assetId,
      subjectEntityId,
      "primary_reference",
      "normal",
      `Portrait de ${name}`,
    );
    window.dispatchEvent(new CustomEvent(VISUAL_BINDINGS_CHANGED_EVENT, { detail: { campaignId } }));
    setPickerOpen(false);
    setCandidates([]);
    await reload();
  }

  async function importNewPortrait(campaignId: string) {
    const path = await open({
      title: hasPortrait ? `Changer le portrait de ${name}` : `Ajouter le portrait de ${name}`,
      multiple: false,
      directory: false,
      filters: [{ name: "Image", extensions: ["png", "jpg", "jpeg", "webp"] }],
    });
    if (!path || Array.isArray(path)) return;
    const asset = await backend.importCampaignAsset(campaignId, "npc_portrait", path);
    await bindPortrait(campaignId, asset.id);
  }

  async function choosePortrait() {
    if (busy) return;
    setBusy(true);
    try {
      const campaignId = await resolveCampaignId();
      if (!campaignId) return;

      const [assets, bindings] = await Promise.all([
        backend.listAssets(campaignId),
        backend.listVisualAssetBindings(campaignId),
      ]);
      const boundElsewhere = new Set(bindings
        .filter((binding) => binding.role === "primary_reference" && binding.subject_entity_id !== subjectEntityId)
        .map((binding) => binding.asset_id));
      const reusableAssets = assets.filter((asset) => asset.kind === "npc_portrait" && !boundElsewhere.has(asset.id));

      const resolved = (await Promise.all(reusableAssets.map(async (asset) => {
        try {
          return { asset, url: await backend.readAssetDataUrl(campaignId, asset.id) } satisfies Candidate;
        } catch {
          return null;
        }
      }))).filter((candidate): candidate is Candidate => candidate !== null);

      if (resolved.length === 0) {
        await importNewPortrait(campaignId);
        return;
      }
      setCandidates(resolved);
      setPickerOpen(true);
    } finally {
      setBusy(false);
    }
  }

  async function chooseExisting(assetId: string) {
    if (busy) return;
    setBusy(true);
    try {
      const campaignId = await resolveCampaignId();
      if (!campaignId) return;
      await bindPortrait(campaignId, assetId);
    } finally {
      setBusy(false);
    }
  }

  async function importFromPicker() {
    if (busy) return;
    setBusy(true);
    try {
      const campaignId = await resolveCampaignId();
      if (!campaignId) return;
      await importNewPortrait(campaignId);
    } finally {
      setBusy(false);
    }
  }

  const stateLabel = currentState && normalize(currentState) !== "normal" ? ` · ${currentState}` : "";

  return <div className="npc-portrait-control">
    {url
      ? <img className="npc-avatar-image" src={url} alt={`Portrait de ${name}${stateLabel}`} />
      : <button className="npc-avatar npc-avatar-empty" onClick={choosePortrait} disabled={busy} aria-label={`Ajouter un portrait pour ${name}`} title={`Ajouter un portrait pour ${name}`}>{name.slice(0, 1).toUpperCase()}</button>}
    <button className="ghost small npc-portrait-action" onClick={choosePortrait} disabled={busy}>
      {hasPortrait ? "Changer" : "Ajouter"}
    </button>
    {pickerOpen && <div className="npc-portrait-picker" role="dialog" aria-label={`Choisir le portrait de ${name}`}>
      <div className="npc-portrait-picker-head"><strong>Portrait de {name}</strong><button className="ghost small" onClick={() => setPickerOpen(false)}>Fermer</button></div>
      <p>Choisis une image déjà importée ou ajoute-en une nouvelle.</p>
      <div className="npc-portrait-candidates">
        {candidates.map(({ asset, url: candidateUrl }) => <button key={asset.id} className="npc-portrait-candidate" onClick={() => chooseExisting(asset.id)} disabled={busy} aria-label={`Utiliser ce portrait pour ${name}`}>
          <img src={candidateUrl} alt="Portrait PNJ déjà importé" />
        </button>)}
      </div>
      <button className="secondary small" onClick={importFromPicker} disabled={busy}>Importer une nouvelle image</button>
    </div>}
  </div>;
}
