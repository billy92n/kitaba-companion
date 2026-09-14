import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { backend } from "../lib/backend";
import type { EntityDocument } from "../lib/types";
import { EncyclopediaView } from "./EncyclopediaView";

function selectedCampaignId() {
  return document.querySelector<HTMLSelectElement>(".campaign-select")?.value ?? null;
}

export function EncyclopediaDock() {
  const [navTarget, setNavTarget] = useState<HTMLElement | null>(null);
  const [pageTarget, setPageTarget] = useState<HTMLElement | null>(null);
  const [open, setOpen] = useState(false);
  const [campaignId, setCampaignId] = useState<string | null>(null);
  const [campaignName, setCampaignName] = useState<string>("");
  const [entities, setEntities] = useState<EntityDocument[]>([]);
  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (preferredCampaignId?: string | null) => {
    try {
      const campaigns = await backend.listCampaigns();
      const id = preferredCampaignId ?? selectedCampaignId() ?? campaigns[0]?.id ?? null;
      const campaign = campaigns.find((item) => item.id === id) ?? campaigns[0] ?? null;
      if (!campaign) {
        setCampaignId(null);
        setCampaignName("");
        setEntities([]);
        setReady(false);
        return;
      }
      const rows = await backend.listEntities(campaign.id, false);
      setCampaignId(campaign.id);
      setCampaignName(campaign.name);
      setEntities(rows);
      setReady(rows.some((entity) => entity.entity_type === "player_character"));
      setError(null);
    } catch (reason) {
      setError(String(reason));
      setReady(false);
    }
  }, []);

  useEffect(() => {
    const locateTargets = () => {
      setNavTarget(document.querySelector<HTMLElement>(".encyclopedia-nav-slot"));
      setPageTarget(document.querySelector<HTMLElement>("main"));
    };
    locateTargets();
    const observer = new MutationObserver(locateTargets);
    observer.observe(document.body, { childList: true, subtree: true });
    refresh().catch(() => undefined);
    return () => observer.disconnect();
  }, [refresh]);

  useEffect(() => {
    if (ready) return;
    const timer = window.setInterval(() => refresh(selectedCampaignId()).catch(() => undefined), 1500);
    return () => window.clearInterval(timer);
  }, [ready, refresh]);

  useEffect(() => {
    const onChange = (event: Event) => {
      const target = event.target;
      if (target instanceof HTMLSelectElement && target.classList.contains("campaign-select")) {
        setOpen(false);
        refresh(target.value).catch(() => undefined);
      }
    };
    const onNavigation = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const navButton = target.closest(".sidebar .nav-item");
      if (navButton && !navButton.classList.contains("encyclopedia-nav-item")) setOpen(false);
    };
    document.addEventListener("change", onChange);
    document.addEventListener("click", onNavigation);
    return () => {
      document.removeEventListener("change", onChange);
      document.removeEventListener("click", onNavigation);
    };
  }, [refresh]);

  useEffect(() => {
    document.body.classList.toggle("encyclopedia-open", open);
    return () => document.body.classList.remove("encyclopedia-open");
  }, [open]);

  async function openEncyclopedia() {
    setLoading(true);
    await refresh(campaignId);
    setLoading(false);
    setOpen(true);
    document.querySelector<HTMLButtonElement>(".mobile-backdrop")?.click();
  }

  const navButton = navTarget && ready ? createPortal(
    <button className={`nav-item encyclopedia-nav-item ${open ? "active" : ""}`} onClick={openEncyclopedia} disabled={loading}>
      Encyclopédie
    </button>,
    navTarget,
  ) : null;

  const page = open && pageTarget ? createPortal(
    <div className="encyclopedia-page-portal">
      <header className="encyclopedia-page-header">
        <div><span className="eyebrow">Mémoire écrite du personnage</span><h1>Encyclopédie</h1><p>{campaignName || "Campagne active"}</p></div>
        <button className="ghost" onClick={() => setOpen(false)}>Fermer</button>
      </header>
      {error ? <section className="panel"><h2>Encyclopédie indisponible</h2><p>{error}</p></section> : <EncyclopediaView entities={entities} />}
    </div>,
    pageTarget,
  ) : null;

  return <>{navButton}{page}</>;
}
