import { useEffect, useMemo, useState } from "react";
import type { AssetSummary, EntityDocument, VisualAssetBinding } from "../lib/types";
import { backend } from "../lib/backend";
import { fieldLabelFr, valueFr } from "../lib/frenchUi";
import "../visual-library-mvp.css";

type VisualKind = "world_map" | "player_portrait" | "npc_portrait" | "other_image";

type Props = {
  campaignId: string;
  entities: EntityDocument[];
  assets: AssetSummary[];
  previewUrl: string | null;
  previewAssetId: string | null;
  onImport: (kind: VisualKind) => void | Promise<void>;
  onPreview: (asset: AssetSummary) => void | Promise<void>;
  onStatus: (message: string) => void;
};

const ROLE_OPTIONS = [
  ["primary_reference", "Référence principale"],
  ["state_variant", "Variante d’état"],
  ["scene_reference", "Scène / souvenir"],
  ["place_reference", "Référence de lieu"],
  ["historical_reference", "Référence historique"],
] as const;

const BINDABLE_TYPES = new Set(["player_character", "npc", "place", "settlement", "region", "state"]);
const VISUAL_BINDINGS_CHANGED_EVENT = "kitaba-visual-bindings-changed";

function textField(entity: EntityDocument, ...keys: string[]) {
  for (const key of keys) {
    const value = entity.data[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return entity.id;
}

function subjectLabel(entity: EntityDocument) {
  const name = textField(entity, "name", "first_name", "known_name", "title", "label");
  const kind: Record<string, string> = {
    player_character: "Personnage",
    npc: "PNJ",
    place: "Lieu",
    settlement: "Localité",
    region: "Région",
    state: "État",
  };
  return `${kind[entity.entity_type] ?? fieldLabelFr(entity.entity_type)} · ${name}`;
}

function assetLabel(asset: AssetSummary) {
  const labels: Record<string, string> = {
    player_portrait: "Portrait du personnage",
    npc_portrait: "Portrait PNJ",
    other_image: "Illustration",
    world_map: "Carte du monde",
  };
  return labels[asset.kind] ?? fieldLabelFr(asset.kind);
}

function roleLabel(role: string) {
  return ROLE_OPTIONS.find(([key]) => key === role)?.[1] ?? fieldLabelFr(role);
}

function notifyVisualBindingsChanged(campaignId: string) {
  window.dispatchEvent(new CustomEvent(VISUAL_BINDINGS_CHANGED_EVENT, { detail: { campaignId } }));
}

export function VisualLibrary({ campaignId, entities, assets, previewUrl, previewAssetId, onImport, onPreview, onStatus }: Props) {
  const [bindings, setBindings] = useState<VisualAssetBinding[]>([]);
  const [bindingAssetId, setBindingAssetId] = useState<string | null>(null);
  const [subjectId, setSubjectId] = useState("");
  const [role, setRole] = useState("primary_reference");
  const [visualState, setVisualState] = useState("normal");
  const [caption, setCaption] = useState("");
  const [busy, setBusy] = useState(false);

  const subjects = useMemo(() => entities.filter((entity) => BINDABLE_TYPES.has(entity.entity_type)), [entities]);
  const subjectsById = useMemo(() => new Map(subjects.map((entity) => [entity.id, entity])), [subjects]);
  const bindingsByAsset = useMemo(() => new Map(bindings.map((binding) => [binding.asset_id, binding])), [bindings]);
  const bindableAssets = assets.filter((asset) => asset.kind !== "world_map");

  async function reloadBindings() {
    try {
      setBindings(await backend.listVisualAssetBindings(campaignId));
    } catch (error) {
      onStatus(`Références visuelles indisponibles : ${String(error)}`);
    }
  }

  useEffect(() => {
    reloadBindings();
    setBindingAssetId(null);
    setSubjectId("");
  }, [campaignId]);

  function startBinding(asset: AssetSummary) {
    const existing = bindingsByAsset.get(asset.id);
    const defaultSubject = existing?.subject_entity_id ?? subjects[0]?.id ?? "";
    const defaultRole = existing?.role ?? (asset.kind === "other_image" ? "scene_reference" : "primary_reference");
    setBindingAssetId(asset.id);
    setSubjectId(defaultSubject);
    setRole(defaultRole);
    setVisualState(existing?.state ?? "normal");
    setCaption(existing?.caption ?? "");
  }

  async function saveBinding() {
    if (!bindingAssetId || !subjectId) return;
    setBusy(true);
    try {
      const result = await backend.bindVisualAsset(campaignId, bindingAssetId, subjectId, role, visualState.trim() || "normal", caption.trim() || undefined);
      setBindings((current) => [...current.filter((binding) => binding.asset_id !== result.asset_id), result]);
      setBindingAssetId(null);
      notifyVisualBindingsChanged(campaignId);
      onStatus("Référence visuelle associée. Elle sera conservée dans les sauvegardes .kitaba sans modifier le canon narratif.");
    } catch (error) {
      onStatus(`Association visuelle impossible : ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }

  async function removeBinding(assetId: string) {
    setBusy(true);
    try {
      await backend.unbindVisualAsset(campaignId, assetId);
      setBindings((current) => current.filter((binding) => binding.asset_id !== assetId));
      if (bindingAssetId === assetId) setBindingAssetId(null);
      notifyVisualBindingsChanged(campaignId);
      onStatus("Association visuelle retirée. L’image reste dans la médiathèque.");
    } catch (error) {
      onStatus(`Impossible de retirer l’association : ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }

  return <div className="media-stack">
    <section className="panel visual-continuity">
      <div className="eyebrow">Continuité visuelle</div>
      <h2>Références de campagne</h2>
      <p>Une image peut être reliée à un personnage ou à un lieu connu. La référence principale fixe son identité visuelle ; les variantes conservent cette identité et ne changent que l’état justifié par l’histoire.</p>
      <div className="visual-rule-grid"><span><b>1.</b> Identité textuelle canonique</span><span><b>2.</b> Référence visuelle associée</span><span><b>3.</b> Variantes = même identité</span><span><b>4.</b> Scènes de groupe = références réutilisées</span></div>
    </section>

    <section className="panel">
      <div className="visual-library-head"><div><h2>Médiathèque de campagne</h2><p className="muted">Les associations restent locales, sont incluses dans les sauvegardes techniques et ne peuvent cibler que des entités visibles du joueur.</p></div><div className="action-row"><button className="secondary" onClick={() => onImport("npc_portrait")}>Ajouter portrait PNJ</button><button className="secondary" onClick={() => onImport("other_image")}>Ajouter illustration</button><button className="ghost" onClick={() => onImport("player_portrait")}>Portrait du personnage</button></div></div>

      {bindableAssets.length === 0 ? <div className="empty-inline">Aucun portrait ou illustration importé.</div> : <div className="visual-asset-grid">{bindableAssets.map((asset) => {
        const binding = bindingsByAsset.get(asset.id);
        const subject = binding ? subjectsById.get(binding.subject_entity_id) : null;
        return <article className={`visual-asset-card ${binding ? "bound" : ""}`} key={asset.id}>
          <div><strong>{assetLabel(asset)}</strong><span>{new Date(asset.created_at).toLocaleString("fr-FR")}</span></div>
          {binding ? <div className="visual-binding-summary"><b>{subject ? subjectLabel(subject) : "Sujet indisponible"}</b><span>{roleLabel(binding.role)} · {valueFr(binding.state)}</span>{binding.caption && <small>{binding.caption}</small>}</div> : <div className="visual-unbound">Non associée — l’image n’a pas encore d’identité persistante.</div>}
          <div className="action-row"><button className="ghost small" onClick={() => onPreview(asset)}>{previewAssetId === asset.id ? "Actualiser" : "Voir"}</button><button className="secondary small" disabled={subjects.length === 0 || busy} onClick={() => startBinding(asset)}>{binding ? "Modifier l’association" : "Associer à…"}</button>{binding && <button className="ghost small" disabled={busy} onClick={() => removeBinding(asset.id)}>Dissocier</button>}</div>
        </article>;
      })}</div>}

      {bindingAssetId && <div className="visual-binding-editor">
        <div><div className="eyebrow">Association visuelle</div><h3>{assetLabel(assets.find((asset) => asset.id === bindingAssetId) ?? { kind: "other_image" } as AssetSummary)}</h3></div>
        <label>Sujet connu<select value={subjectId} onChange={(event) => setSubjectId(event.target.value)}>{subjects.map((entity) => <option value={entity.id} key={entity.id}>{subjectLabel(entity)}</option>)}</select></label>
        <label>Rôle<select value={role} onChange={(event) => setRole(event.target.value)}>{ROLE_OPTIONS.map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
        <label>État visuel<input value={visualState} onChange={(event) => setVisualState(event.target.value)} placeholder="normal, blessé, malade…" maxLength={80} /></label>
        <label className="visual-binding-caption">Légende / précision<input value={caption} onChange={(event) => setCaption(event.target.value)} placeholder="Ex. tenue habituelle, après le combat…" maxLength={240} /></label>
        <div className="action-row"><button onClick={saveBinding} disabled={busy || !subjectId}>Enregistrer la référence</button><button className="ghost" onClick={() => setBindingAssetId(null)} disabled={busy}>Annuler</button></div>
      </div>}

      {previewUrl && <div className="media-preview"><img src={previewUrl} alt="Prévisualisation du visuel sélectionné" /></div>}
    </section>
  </div>;
}