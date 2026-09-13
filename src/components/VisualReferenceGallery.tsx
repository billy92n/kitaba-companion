import { useEffect, useState } from "react";
import { backend } from "../lib/backend";
import type { VisualAssetBinding } from "../lib/types";
import "../visual-reference-gallery.css";

type VisualItem = {
  binding: VisualAssetBinding;
  url: string;
};

type Props = {
  subjectEntityId: string;
  currentState?: string | null;
  compact?: boolean;
  limit?: number;
};

const VISUAL_BINDINGS_CHANGED_EVENT = "kitaba-visual-bindings-changed";
let campaignRequest: Promise<string | null> | null = null;
let bindingCache: { campaignId: string; rows: VisualAssetBinding[]; loadedAt: number } | null = null;
let bindingRequest: { campaignId: string; promise: Promise<VisualAssetBinding[]> } | null = null;
const assetUrlCache = new Map<string, Promise<string>>();

function normalize(value: string | null | undefined) {
  return (value ?? "").trim().toLocaleLowerCase("fr");
}

async function resolveSelectedCampaignId(): Promise<string | null> {
  const selected = document.querySelector<HTMLSelectElement>(".campaign-select")?.value;
  if (selected) return selected;
  if (!campaignRequest) {
    campaignRequest = backend.listCampaigns().then((campaigns) => campaigns[0]?.id ?? null).finally(() => {
      campaignRequest = null;
    });
  }
  return campaignRequest;
}

async function loadBindings(campaignId: string): Promise<VisualAssetBinding[]> {
  const now = Date.now();
  if (bindingCache?.campaignId === campaignId && now - bindingCache.loadedAt < 1000) return bindingCache.rows;
  if (!bindingRequest || bindingRequest.campaignId !== campaignId) {
    const promise = backend.listVisualAssetBindings(campaignId).then((rows) => {
      bindingCache = { campaignId, rows, loadedAt: Date.now() };
      return rows;
    }).finally(() => {
      if (bindingRequest?.campaignId === campaignId) bindingRequest = null;
    });
    bindingRequest = { campaignId, promise };
  }
  return bindingRequest.promise;
}

function bindingPriority(binding: VisualAssetBinding, currentState: string) {
  if (binding.role === "primary_reference") return 0;
  if (binding.role === "place_reference") return 1;
  if (binding.role === "state_variant" && currentState && normalize(binding.state) === currentState) return 1;
  if (binding.role === "scene_reference") return 2;
  if (binding.role === "historical_reference") return 3;
  return 4;
}

function roleLabel(binding: VisualAssetBinding) {
  if (binding.role === "primary_reference") return "Référence principale";
  if (binding.role === "state_variant") return binding.state && binding.state !== "normal" ? `État · ${binding.state}` : "Variante d'état";
  if (binding.role === "place_reference") return "Référence du lieu";
  if (binding.role === "scene_reference") return "Scène liée";
  if (binding.role === "historical_reference") return "Référence historique";
  return binding.role.replaceAll("_", " ");
}

function selectBindings(bindings: VisualAssetBinding[], subjectEntityId: string, currentState: string, limit: number) {
  return bindings
    .filter((binding) => binding.subject_entity_id === subjectEntityId)
    .filter((binding) => {
      if (binding.role !== "state_variant") return true;
      return Boolean(currentState) && normalize(binding.state) === currentState;
    })
    .sort((a, b) => bindingPriority(a, currentState) - bindingPriority(b, currentState) || a.updated_at.localeCompare(b.updated_at))
    .slice(0, limit);
}

export function VisualReferenceGallery({ subjectEntityId, currentState, compact = false, limit = 3 }: Props) {
  const [items, setItems] = useState<VisualItem[]>([]);
  const [refreshToken, setRefreshToken] = useState(0);
  const normalizedState = normalize(currentState);

  useEffect(() => {
    const refresh = () => {
      bindingCache = null;
      bindingRequest = null;
      setRefreshToken((value) => value + 1);
    };
    window.addEventListener(VISUAL_BINDINGS_CHANGED_EVENT, refresh);
    return () => window.removeEventListener(VISUAL_BINDINGS_CHANGED_EVENT, refresh);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setItems([]);
    (async () => {
      const campaignId = await resolveSelectedCampaignId();
      if (!campaignId) return;
      const bindings = selectBindings(await loadBindings(campaignId), subjectEntityId, normalizedState, limit);
      const resolved = await Promise.all(bindings.map(async (binding) => {
        const cacheKey = `${campaignId}:${binding.asset_id}`;
        let request = assetUrlCache.get(cacheKey);
        if (!request) {
          request = backend.readAssetDataUrl(campaignId, binding.asset_id);
          assetUrlCache.set(cacheKey, request);
        }
        try {
          return { binding, url: await request } satisfies VisualItem;
        } catch {
          assetUrlCache.delete(cacheKey);
          return null;
        }
      }));
      if (!cancelled) setItems(resolved.filter((item): item is VisualItem => item !== null));
    })().catch(() => {
      if (!cancelled) setItems([]);
    });
    return () => { cancelled = true; };
  }, [subjectEntityId, normalizedState, limit, refreshToken]);

  if (!items.length) return null;
  return <div className={`visual-reference-gallery ${compact ? "compact" : ""}`} aria-label="Références visuelles liées">
    {items.map(({ binding, url }) => <figure className="visual-reference-card" key={binding.asset_id}>
      <img src={url} alt={binding.caption ?? roleLabel(binding)} />
      <figcaption><strong>{roleLabel(binding)}</strong>{binding.caption && <span>{binding.caption}</span>}</figcaption>
    </figure>)}
  </div>;
}
