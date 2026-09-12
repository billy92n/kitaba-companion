import { useEffect, useMemo, useRef, useState } from "react";
import { open, save } from "@tauri-apps/plugin-dialog";
import { Sidebar } from "./components/Sidebar";
import { EntityList } from "./components/EntityList";
import { CharacterView, InventoryView, JournalView, KnowledgeView, MissionsView, RelationsView } from "./components/RpgViews";
import { AdventurerCardView, MagicView, SkillsView, TimelineView } from "./components/ProgressionViews";
import { InteractiveMap } from "./components/InteractiveMap";
import { backend } from "./lib/backend";
import type {
  AssetSummary,
  AuditEvent,
  CampaignSummary,
  ContextMode,
  EntityDocument,
  ImportResult,
  IntegrityReport,
  RestPointSummary,
  SectionKey,
  UpdatePreview,
} from "./lib/types";
import "./styles.css";

const sectionTypes: Record<SectionKey, string[]> = {
  overview: [],
  character: ["player_character", "characteristic", "specialized_stat", "injury", "status_effect", "awakening"],
  skills: ["skill", "mastery"],
  magic: ["magic", "spell", "affinity", "invocation", "contract", "enchantment", "known_aptitude"],
  inventory: ["item", "inventory_item", "equipment", "wallet", "currency", "debt"],
  relations: ["npc", "relationship", "reputation"],
  journal: ["journal_entry"],
  missions: ["mission", "quest"],
  knowledge: ["knowledge", "rumor", "belief"],
  world: ["faction", "organization", "settlement", "state", "market", "economy_state", "conflict", "world_event", "environment_state", "resource_state", "infrastructure", "law", "political_state"],
  media: [],
  map: ["place", "map_marker", "map", "current_location", "settlement", "state", "region", "route", "dungeon"],
  timeline: ["timeline_event", "historical_event"],
  adventurer_card: ["adventurer_card", "evaluation", "certification"],
  checkpoints: [],
  sync: [],
  gm_vault: [],
};

const labels: Record<SectionKey, string> = {
  overview: "Vue d'ensemble",
  character: "Personnage",
  skills: "Compétences",
  magic: "Magie",
  inventory: "Inventaire",
  relations: "Relations",
  journal: "Journal",
  missions: "Missions",
  knowledge: "Connaissances",
  world: "Monde",
  media: "Médiathèque",
  map: "Carte",
  timeline: "Chronologie",
  adventurer_card: "Carte d'aventurier",
  checkpoints: "Checkpoints",
  sync: "Synchronisation",
  gm_vault: "Coffre MJ",
};

export default function App() {
  const [campaigns, setCampaigns] = useState<CampaignSummary[]>([]);
  const [archivedCampaigns, setArchivedCampaigns] = useState<CampaignSummary[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [newCampaignName, setNewCampaignName] = useState("Kitaba Solo — Nouvelle campagne");
  const [entities, setEntities] = useState<EntityDocument[]>([]);
  const [gmEntities, setGmEntities] = useState<EntityDocument[]>([]);
  const [restPoints, setRestPoints] = useState<RestPointSummary[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [active, setActive] = useState<SectionKey>("overview");
  const [jsonText, setJsonText] = useState("");
  const [rawUpdateVisible, setRawUpdateVisible] = useState(false);
  const [preview, setPreview] = useState<UpdatePreview | null>(null);
  const [status, setStatus] = useState("Prêt.");
  const [busy, setBusy] = useState(false);
  const [lastImport, setLastImport] = useState<ImportResult | null>(null);
  const [gmUnlocked, setGmUnlocked] = useState(false);
  const [rollbackTarget, setRollbackTarget] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [mapZoom, setMapZoom] = useState(1);
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [worldMapUrl, setWorldMapUrl] = useState<string | null>(null);
  const [portraitUrl, setPortraitUrl] = useState<string | null>(null);
  const [mediaPreviewUrl, setMediaPreviewUrl] = useState<string | null>(null);
  const [mediaPreviewAssetId, setMediaPreviewAssetId] = useState<string | null>(null);
  const [manualPlayerEntityId, setManualPlayerEntityId] = useState("");
  const [manualPlayerPatch, setManualPlayerPatch] = useState("{}");
  const [manualPlayerReason, setManualPlayerReason] = useState("");
  const [manualGmEntityId, setManualGmEntityId] = useState("");
  const [manualGmPatch, setManualGmPatch] = useState("{}");
  const [manualGmReason, setManualGmReason] = useState("");
  const [gmMapZoom, setGmMapZoom] = useState(1);
  const [integrity, setIntegrity] = useState<IntegrityReport | null>(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const mapFrameRef = useRef<HTMLDivElement | null>(null);

  const campaign = useMemo(
    () => campaigns.find((c) => c.id === selectedId) ?? campaigns[0] ?? null,
    [campaigns, selectedId]
  );

  const sectionEntities = useMemo(() => {
    const types = sectionTypes[active];
    if (!types.length) return [];
    return entities.filter((e) => types.includes(e.entity_type));
  }, [active, entities]);

  const searchableEntities = useMemo(() => entities.map((entity) => ({
    entity,
    text: `${entity.entity_type} ${JSON.stringify(entity.data)}`.toLocaleLowerCase("fr"),
  })), [entities]);

  const searchResults = useMemo(() => {
    const q = searchQuery.trim().toLocaleLowerCase("fr");
    if (!q) return [];
    return searchableEntities.filter((row) => row.text.includes(q)).slice(0, 24).map((row) => row.entity);
  }, [searchQuery, searchableEntities]);

  const pc: Record<string, unknown> = entities.find((e) => e.entity_type === "player_character")?.data ?? {};
  const currentLocation = entities.find((e) => e.entity_type === "current_location")?.data;
  const characterInitialized = entities.some((e) => e.entity_type === "player_character");

  function entityLabel(entity: EntityDocument) {
    const data = entity.data;
    const label = data.name ?? data.first_name ?? data.title ?? data.label ?? data.known_name ?? entity.id;
    return `${entity.entity_type} · ${String(label)} · v${entity.entity_version}`;
  }

  async function refreshCampaigns() {
    const [rows, archived] = await Promise.all([backend.listCampaigns(), backend.listArchivedCampaigns()]);
    setCampaigns(rows);
    setArchivedCampaigns(archived);
    if (!rows.some((c) => c.id === selectedId)) setSelectedId(rows[0]?.id ?? "");
  }

  async function refreshCampaignData(campaignId: string) {
    const [player, rests, audit, assetRows, integrityReport] = await Promise.all([
      backend.listEntities(campaignId, false),
      backend.listRestPoints(campaignId),
      backend.listAuditEvents(campaignId, 30),
      backend.listAssets(campaignId),
      backend.campaignIntegrityReport(campaignId),
    ]);
    setEntities(player);
    setRestPoints(rests);
    setAuditEvents(audit);
    setAssets(assetRows);
    setIntegrity(integrityReport);
    const mapAsset = assetRows.find((a) => a.kind === "world_map");
    const portraitAsset = assetRows.find((a) => a.kind === "player_portrait");
    const [mapUrl, portrait] = await Promise.all([
      mapAsset ? backend.readAssetDataUrl(campaignId, mapAsset.id) : Promise.resolve(null),
      portraitAsset ? backend.readAssetDataUrl(campaignId, portraitAsset.id) : Promise.resolve(null),
    ]);
    setWorldMapUrl(mapUrl);
    setPortraitUrl(portrait);
    setGmEntities([]);
    setGmUnlocked(false);
    setMediaPreviewUrl(null);
    setMediaPreviewAssetId(null);
  }

  useEffect(() => {
    refreshCampaigns().catch((e) => setStatus(`Erreur d'initialisation : ${String(e)}`));
  }, []);

  useEffect(() => {
    if (campaign?.id) refreshCampaignData(campaign.id).catch((e) => setStatus(`Erreur de chargement : ${String(e)}`));
  }, [campaign?.id, campaign?.current_revision]);

  async function createCampaign() {
    const name = newCampaignName.trim();
    if (!name) { setStatus("Indique un nom de campagne avant de la créer."); return; }
    setBusy(true);
    try {
      const created = await backend.createCampaign(name);
      await refreshCampaigns();
      setSelectedId(created.id);
      setActive("sync");
      setStatus("Campagne vierge créée. Exporte le contexte complet MJ puis effectue la création du personnage avec le MJ avant toute narration.");
    } catch (e) { setStatus(`Erreur : ${String(e)}`); }
    finally { setBusy(false); }
  }

  async function createAnotherCampaign() {
    const suggested = "Kitaba Solo — Nouvelle campagne";
    const value = window.prompt("Nom de la nouvelle campagne", suggested);
    if (value === null) return;
    const name = value.trim();
    if (!name) { setStatus("Création annulée : le nom de campagne ne peut pas être vide."); return; }
    setBusy(true);
    try {
      const created = await backend.createCampaign(name);
      await refreshCampaigns();
      setSelectedId(created.id);
      setSearchQuery("");
      setActive("sync");
      setStatus("Nouvelle campagne vierge créée. Exporte son contexte complet MJ puis termine la création du personnage avant toute narration.");
    } catch (e) { setStatus(`Création impossible : ${String(e)}`); }
    finally { setBusy(false); }
  }

  async function analyzeUpdate() {
    if (!jsonText.trim()) return;
    setBusy(true);
    try {
      const next = await backend.previewUpdate(jsonText);
      setPreview(next);
      setRawUpdateVisible(false);
      setStatus("Structure, révision et timeline validées. Le contenu brut reste masqué pour éviter les spoilers MJ.");
    } catch (e) {
      setPreview(null);
      setStatus(`Analyse refusée : ${String(e)}`);
    } finally { setBusy(false); }
  }

  async function loadUpdateFile() {
    try {
      const path = await open({
        title: "Charger un KITABA_UPDATE",
        multiple: false,
        directory: false,
        filters: [
          { name: "Mise à jour Kitaba", extensions: ["kitaba-update", "json"] },
        ],
      });
      if (!path || Array.isArray(path)) return;
      const text = await backend.readTextFile(path);
      setJsonText(text);
      setRawUpdateVisible(false);
      setPreview(null);
      setStatus("Fichier KITABA_UPDATE chargé. Son contenu brut est masqué ; clique sur Analyser avant application.");
    } catch (e) { setStatus(`Lecture impossible : ${String(e)}`); }
  }

  async function importUpdate() {
    setBusy(true);
    try {
      const result = await backend.importUpdate(jsonText);
      setLastImport(result);
      setPreview(null);
      setJsonText("");
      setRawUpdateVisible(false);
      const note = result.notifications.length ? ` — ${result.notifications.map((n) => n.message).join(" · ")}` : "";
      setStatus(`Mise à jour appliquée atomiquement. Révision ${result.revision}. ${result.gm_operation_count} opération(s) MJ masquée(s).${note}`);
      await refreshCampaigns();
    } catch (e) { setStatus(`Import refusé : ${String(e)}`); }
    finally { setBusy(false); }
  }

  async function exportContext(mode: ContextMode) {
    if (!campaign) return;
    setBusy(true);
    try {
      const isGm = mode === "GM_FULL";
      const path = await save({
        title: isGm ? "Exporter le contexte complet pour ChatGPT" : "Exporter le contexte joueur",
        defaultPath: `${campaign.name.replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "") || "Kitaba"}_${isGm ? "Context_MJ" : "Context_Joueur"}.json`,
        filters: [{ name: isGm ? "Contexte Kitaba complet" : "Contexte Kitaba joueur", extensions: ["json"] }],
      });
      if (!path) return;
      await backend.saveContext(campaign.id, mode, path);
      await backend.recordContextExport(campaign.id, mode);
      await refreshCampaigns();
      setStatus(isGm ? "Contexte MJ exporté pour ChatGPT. Son ouverture manuelle peut spoiler la campagne." : "Contexte joueur exporté sans données MJ.");
    } catch (e) { setStatus(`Export impossible : ${String(e)}`); }
    finally { setBusy(false); }
  }

  async function copyPlayerContext() {
    if (!campaign) return;
    try {
      const text = await backend.exportContext(campaign.id, "PLAYER");
      await navigator.clipboard.writeText(text);
      await backend.recordContextExport(campaign.id, "PLAYER");
      await refreshCampaigns();
      setStatus("Contexte joueur copié dans le presse-papiers.");
    } catch (e) { setStatus(`Copie impossible : ${String(e)}`); }
  }

  async function unlockGm() {
    if (!campaign) return;
    const ok = window.confirm("ATTENTION — Cette section contient des spoilers majeurs de la campagne. Ouvrir le Coffre MJ ?");
    if (!ok) return;
    const rows = await backend.listEntities(campaign.id, true);
    setGmEntities(rows.filter((e) => e.visibility === "GM"));
    setGmUnlocked(true);
  }

  async function confirmRollback(restPointId: string) {
    if (!campaign) return;
    if (!campaign.death_pending) { setStatus("Rollback refusé : aucune mort du personnage n'a été confirmée par le MJ."); return; }
    const ok = window.confirm("Rollback après mort : l'état canonique reviendra à ce Rest Point et une nouvelle timeline sera créée. Continuer ?");
    if (!ok) return;
    setRollbackTarget(restPointId);
    try {
      const result = await backend.rollbackDeath(campaign.id, restPointId, "Rollback déclenché depuis le Companion");
      setStatus(`Rollback effectué. Nouvelle timeline, révision ${result.revision}.`);
      await refreshCampaigns();
      setActive("overview");
    } catch (e) { setStatus(`Rollback impossible : ${String(e)}`); }
    finally { setRollbackTarget(null); }
  }


  async function createBackup() {
    if (!campaign) return;
    try {
      const path = await save({
        title: "Sauvegarder la campagne Kitaba",
        defaultPath: `Kitaba-${campaign.name.replace(/[^a-z0-9_-]+/gi, "-")}.kitaba`,
        filters: [{ name: "Sauvegarde Kitaba", extensions: ["kitaba"] }],
      });
      if (!path) return;
      await backend.createTechnicalBackup(campaign.id, path, "manual");
      setStatus("Sauvegarde technique créée. Elle ne constitue pas un Rest Point de gameplay.");
    } catch (e) { setStatus(`Sauvegarde impossible : ${String(e)}`); }
  }

  async function restoreBackup() {
    const path = await open({
      title: "Restaurer une sauvegarde Kitaba",
      multiple: false,
      directory: false,
      filters: [{ name: "Sauvegarde Kitaba", extensions: ["kitaba"] }],
    });
    if (!path || Array.isArray(path)) return;
    const ok = window.confirm("Restaurer cette sauvegarde technique ? Une sauvegarde automatique de l'état actuel sera créée avant restauration.");
    if (!ok) return;
    try {
      const rows = await backend.restoreTechnicalBackup(path);
      setCampaigns(rows);
      if (rows[0]) setSelectedId(rows[0].id);
      setStatus("Sauvegarde restaurée avec contrôle d'intégrité.");
    } catch (e) { setStatus(`Restauration impossible : ${String(e)}`); }
  }

  async function importVisual(kind: "world_map" | "player_portrait" | "npc_portrait" | "other_image") {
    if (!campaign) return;
    const titles: Record<typeof kind, string> = {
      world_map: "Importer le fond de carte",
      player_portrait: "Importer le portrait du personnage",
      npc_portrait: "Importer un portrait de PNJ",
      other_image: "Importer une image de campagne",
    };
    try {
      const path = await open({
        title: titles[kind],
        multiple: false,
        directory: false,
        filters: [{ name: "Image", extensions: ["png", "jpg", "jpeg", "webp"] }],
      });
      if (!path || Array.isArray(path)) return;
      await backend.importCampaignAsset(campaign.id, kind, path);
      await refreshCampaignData(campaign.id);
      setStatus(kind === "world_map" ? "Fond de carte importé et intégré aux sauvegardes de campagne." : kind === "player_portrait" ? "Portrait du personnage importé et intégré aux sauvegardes de campagne." : kind === "npc_portrait" ? "Portrait de PNJ ajouté à la médiathèque de campagne." : "Image ajoutée à la médiathèque de campagne.");
    } catch (e) {
      setStatus(`Import d'image impossible : ${String(e)}`);
    }
  }

  async function previewMediaAsset(asset: AssetSummary) {
    if (!campaign) return;
    try {
      const url = await backend.readAssetDataUrl(campaign.id, asset.id);
      setMediaPreviewUrl(url);
      setMediaPreviewAssetId(asset.id);
    } catch (e) { setStatus(`Prévisualisation impossible : ${String(e)}`); }
  }

  async function applyManualCorrection(scope: "PLAYER" | "GM") {
    if (!campaign) return;
    const entityId = scope === "PLAYER" ? manualPlayerEntityId : manualGmEntityId;
    const patchText = scope === "PLAYER" ? manualPlayerPatch : manualGmPatch;
    const reason = scope === "PLAYER" ? manualPlayerReason : manualGmReason;
    const pool = scope === "PLAYER" ? entities : gmEntities;
    const entity = pool.find((e) => e.id === entityId);
    if (!entity) { setStatus("Correction impossible : sélectionne une donnée existante."); return; }
    if (!reason.trim()) { setStatus("Correction impossible : indique la raison de la correction."); return; }
    let patch: Record<string, unknown>;
    try {
      const parsed = JSON.parse(patchText);
      if (!parsed || Array.isArray(parsed) || typeof parsed !== "object" || Object.keys(parsed).length === 0) throw new Error("Le patch doit être un objet JSON non vide.");
      patch = parsed as Record<string, unknown>;
    } catch (e) { setStatus(`Correction impossible : JSON invalide — ${String(e)}`); return; }

    let overrideImmutable = false;
    if (entity.protection === "IMMUTABLE") {
      overrideImmutable = window.confirm("Cette donnée est IMMUTABLE. Forcer sa correction est exceptionnel et sera audité. Continuer ?");
      if (!overrideImmutable) return;
    } else {
      const ok = window.confirm(`Appliquer cette correction manuelle à ${entityLabel(entity)} ? La révision canonique avancera et une sauvegarde technique sera créée avant modification.`);
      if (!ok) return;
    }
    setBusy(true);
    try {
      const result = await backend.manualPatchEntity(campaign.id, entity.id, patch, entity.entity_version, reason.trim(), scope, overrideImmutable);
      setStatus(`Correction manuelle enregistrée et auditée. Révision ${result.campaign_revision}. Réexporte le contexte MJ avant de poursuivre avec ChatGPT.`);
      if (scope === "PLAYER") { setManualPlayerPatch("{}"); setManualPlayerReason(""); }
      else { setManualGmPatch("{}"); setManualGmReason(""); }
      await refreshCampaigns();
    } catch (e) { setStatus(`Correction refusée : ${String(e)}`); }
    finally { setBusy(false); }
  }

  async function runIntegrityCheck() {
    if (!campaign) return;
    setBusy(true);
    try {
      const report = await backend.campaignIntegrityReport(campaign.id);
      setIntegrity(report);
      setStatus(report.ok ? "Diagnostic terminé : aucune incohérence détectée." : "Diagnostic terminé : une incohérence a été détectée. Ne poursuis pas la campagne avant correction.");
    } catch (e) { setStatus(`Diagnostic impossible : ${String(e)}`); }
    finally { setBusy(false); }
  }

  async function archiveCurrentCampaign() {
    if (!campaign) return;
    const ok = window.confirm(`Archiver « ${campaign.name} » ? Aucune donnée ne sera supprimée et la campagne pourra être restaurée.`);
    if (!ok) return;
    try {
      await backend.setCampaignArchived(campaign.id, true);
      setIntegrity(null);
      await refreshCampaigns();
      setStatus("Campagne archivée. Elle peut être restaurée depuis la gestion des campagnes.");
    } catch (e) { setStatus(`Archivage impossible : ${String(e)}`); }
  }

  async function restoreArchivedCampaign(campaignId: string) {
    try {
      await backend.setCampaignArchived(campaignId, false);
      await refreshCampaigns();
      setSelectedId(campaignId);
      setStatus("Campagne restaurée depuis les archives.");
    } catch (e) { setStatus(`Restauration impossible : ${String(e)}`); }
  }

  async function deleteArchivedCampaign(item: CampaignSummary) {
    const typed = window.prompt(`Suppression définitive. Une sauvegarde technique automatique sera créée avant suppression.\n\nTape exactement le nom de la campagne pour confirmer :\n${item.name}`);
    if (typed === null) return;
    if (typed !== item.name) { setStatus("Suppression annulée : le nom saisi ne correspond pas exactement."); return; }
    const finalOk = window.confirm("Dernière confirmation : supprimer définitivement cette campagne du Companion ?");
    if (!finalOk) return;
    try {
      await backend.deleteCampaignPermanently(item.id, item.name);
      await refreshCampaigns();
      setStatus("Campagne supprimée. Une sauvegarde technique pré-suppression a été conservée localement.");
    } catch (e) { setStatus(`Suppression impossible : ${String(e)}`); }
  }

  function renderArchivedCampaigns() {
    if (!archivedCampaigns.length) return null;
    return <section className="panel archived-campaigns"><h2>Campagnes archivées</h2><p className="muted">Une archive conserve l'intégralité de la campagne mais la retire de la liste active.</p><div className="archived-list">{archivedCampaigns.map((item) => <article key={item.id} className="archived-row"><div><strong>{item.name}</strong><span>Révision {item.current_revision}</span></div><div className="action-row"><button className="secondary" onClick={() => restoreArchivedCampaign(item.id)}>Restaurer</button><button className="danger" onClick={() => deleteArchivedCampaign(item)}>Supprimer définitivement</button></div></article>)}</div></section>;
  }

  function renderOverview() {
    if (!characterInitialized) return <section className="panel empty-state"><div className="eyebrow">Phase de création</div><h2>Personnage non initialisé</h2><p>Cette campagne est volontairement vierge. Exporte le contexte complet MJ, termine la création du personnage avec le MJ, puis importe le premier KITABA_UPDATE avant de commencer la narration.</p><p className="muted">Le Companion ne doit jamais inventer le nom, l'âge, l'espèce, l'apparence, les proches ou les connaissances de départ.</p><button onClick={() => setActive("sync")}>Ouvrir la synchronisation</button></section>;
    const recentJournal = entities.filter((e) => e.entity_type === "journal_entry").slice(-5).reverse();
    const missions = entities.filter((e) => ["mission", "quest"].includes(e.entity_type));
    const injuries = entities.filter((e) => ["injury", "status_effect"].includes(e.entity_type));
    return (
      <div className="dashboard-grid">
        <article className="panel hero-panel">
          <div className="eyebrow">État canonique</div>
          <h2>{String(pc.first_name ?? pc.name ?? "Personnage non créé")}</h2>
          <div className="hero-stats">
            <div><span>HP</span><strong>{String(pc.hp_current ?? pc.hp ?? "—")}{pc.hp_max ? ` / ${pc.hp_max}` : ""}</strong></div>
            <div><span>Mana</span><strong>{String(pc.mana_current ?? pc.mana ?? "—")}{pc.mana_max ? ` / ${pc.mana_max}` : ""}</strong></div>
            <div><span>Rang officiel</span><strong>{String(pc.official_rank ?? pc.rank ?? "—")}</strong></div>
            <div><span>Lieu</span><strong>{String((currentLocation as any)?.name ?? pc.current_location ?? "—")}</strong></div>
          </div>
        </article>
        <article className="panel"><h2>État physique</h2><EntityList entities={injuries} empty="Aucune blessure ou altération enregistrée." /></article>
        <article className="panel"><h2>Missions actives</h2><EntityList entities={missions.slice(0, 4)} /></article>
        <article className="panel"><h2>Journal récent</h2><EntityList entities={recentJournal} empty="Aucune entrée de journal." /></article>
        <article className="panel"><h2>Dernier Rest Point</h2>{restPoints[0] ? <div className="rest-summary"><strong>{restPoints[0].description}</strong><span>{restPoints[0].location ?? "Lieu non indiqué"}</span><span>{restPoints[0].game_time ?? "Temps inconnu"}</span></div> : <div className="empty-inline">Aucun Rest Point.</div>}</article>
      </div>
    );
  }

  function renderCheckpoints() {
    return <section className="panel"><h2>Rest Points canoniques</h2><p className="muted">Ils ne sont pas des quicksaves. Le rollback n'est prévu qu'après la mort du personnage.</p><div className="rest-list">{restPoints.length === 0 ? <div className="empty-inline">Aucun Rest Point.</div> : restPoints.map((r, index) => <article className="rest-card" key={r.id}><div><strong>{r.description || "Repos sûr"}{index === 0 ? " · dernier Rest Point" : ""}</strong><span>{r.location ?? "Lieu non indiqué"}</span><span>{r.game_time ?? "Temps inconnu"} · révision {r.snapshot_revision}</span></div><button className="danger" disabled={index !== 0 || !campaign?.death_pending || rollbackTarget === r.id} onClick={() => confirmRollback(r.id)}>{index === 0 ? "Rollback après mort" : "Historique"}</button></article>)}</div></section>;
  }

  function renderSync() {
    return <>
      {!characterInitialized && <section className="panel onboarding-panel"><div className="eyebrow">Démarrage d'une campagne neuve</div><h2>Création du personnage avant la scène 1</h2><p>1. Exporte le contexte complet MJ de cette campagne vierge. 2. Dans le chat de jeu, crée le personnage et fixe son apparence ainsi que son ancrage immédiat. 3. Importe le premier KITABA_UPDATE d'initialisation. 4. Commence seulement ensuite la narration.</p><div className="warning">Aucun concept du monde ne doit être supposé connu du joueur. Le MJ doit introduire naturellement le vocabulaire, les lieux, les proches et les règles découvertes.</div></section>}
      <section className="grid two">
        <article className="panel">
          <h2>Importer depuis ChatGPT</h2>
          <p>Colle un <code>KITABA_UPDATE</code>. Rien n'est écrit avant validation et confirmation.</p>
          {rawUpdateVisible ? <><div className="warning">Mode collage manuel : le JSON peut contenir des données MJ. Préfère « Charger un fichier » pour conserver les secrets masqués.</div><textarea value={jsonText} onChange={(e) => { setJsonText(e.target.value); setPreview(null); }} placeholder={'{ "format": "KITABA_UPDATE", ... }'} /></> : jsonText ? <div className="preview-box"><strong>Payload chargé — contenu brut masqué</strong><p className="muted">Le Companion conserve le fichier en mémoire pour l'analyse sans afficher les opérations MJ.</p><div className="action-row"><button className="ghost" onClick={() => { setRawUpdateVisible(true); setPreview(null); }}>Afficher / modifier le JSON</button><button className="ghost" onClick={() => { setJsonText(""); setPreview(null); setRawUpdateVisible(false); }}>Retirer</button></div></div> : <div className="empty-inline">Charge directement le fichier KITABA_UPDATE. Le contenu brut restera masqué.</div>}
          <div className="action-row"><button className="ghost" onClick={loadUpdateFile} disabled={busy || Boolean(campaign?.death_pending)}>Charger un fichier</button><button className="ghost" onClick={() => setRawUpdateVisible(true)} disabled={busy || Boolean(campaign?.death_pending) || Boolean(jsonText)}>Collage manuel (avancé)</button><button className="secondary" onClick={analyzeUpdate} disabled={busy || !jsonText.trim() || Boolean(campaign?.death_pending)}>Analyser</button>{preview && <button onClick={importUpdate} disabled={busy || Boolean(campaign?.death_pending)}>Appliquer la mise à jour</button>}</div>
          {preview && <div className="preview-box"><h3>Résumé avant import</h3><div className="preview-grid"><span>Révision</span><strong>{preview.base_revision} → {preview.target_revision}</strong><span>Changements joueur</span><strong>{preview.player_operation_count}</strong><span>Entrées journal</span><strong>{preview.journal_entry_count}</strong><span>Données MJ</span><strong>{preview.gm_operation_count + preview.gm_link_operation_count} opération(s) masquée(s)</strong><span>Liens joueur</span><strong>{preview.player_link_operation_count}</strong><span>Résolutions timeline morte</span><strong>{preview.dead_resolution_count} masquée(s)</strong><span>Rest Point</span><strong>{preview.creates_checkpoint ? "Oui" : "Non"}</strong><span>Mort confirmée</span><strong>{preview.marks_death ? "Oui" : "Non"}</strong></div>{preview.player_changes.length > 0 && <ul>{preview.player_changes.map((x, i) => <li key={i}>{x}</li>)}</ul>}</div>}
        </article>
        <article className="panel">
          <h2>Exporter vers ChatGPT</h2>
          <p>Le contexte complet MJ permet de reprendre la campagne dans une autre conversation sans perdre les secrets.</p>
          <div className="button-stack"><button onClick={() => exportContext("GM_FULL")} disabled={busy}>Exporter contexte complet MJ</button><button className="secondary" onClick={() => exportContext("PLAYER")} disabled={busy}>Exporter contexte joueur</button><button className="ghost" onClick={copyPlayerContext} disabled={busy}>Copier contexte joueur</button></div>
          <div className="warning">Le fichier MJ contient des spoilers. Ne l'ouvre pas manuellement si tu veux préserver la découverte.</div>
        </article>
      </section>
      <section className="grid two lower-grid"><article className="panel"><h2>Sauvegardes techniques</h2><p className="muted">Protection contre corruption ou problème technique. Une sauvegarde technique n'autorise jamais à annuler une conséquence de gameplay.</p><div className="action-row"><button className="secondary" onClick={createBackup}>Sauvegarder la campagne</button><button className="ghost" onClick={restoreBackup}>Restaurer un fichier .kitaba</button></div></article><article className="panel status-panel"><h2>État de synchronisation</h2><dl><div><dt>Campaign ID</dt><dd>{campaign?.id}</dd></div><div><dt>Timeline ID</dt><dd>{campaign?.current_timeline_id}</dd></div><div><dt>Révision</dt><dd>{campaign?.current_revision}</dd></div><div><dt>Temps en jeu</dt><dd>{campaign?.game_time ?? "—"}</dd></div><div><dt>Dernier export MJ</dt><dd>{campaign?.last_gm_export_revision == null ? "Jamais" : `Révision ${campaign.last_gm_export_revision}${campaign.last_gm_export_at ? ` · ${new Date(campaign.last_gm_export_at).toLocaleString("fr-FR")}` : ""}`}</dd></div><div><dt>État</dt><dd>{campaign?.last_gm_export_revision === campaign?.current_revision ? "À jour pour ChatGPT" : "Contexte MJ à réexporter"}</dd></div></dl>{lastImport && <p className="muted">Dernier update de cette session : {lastImport.update_id}</p>}</article></section>
      <section className="grid two lower-grid"><article className="panel"><h2>Diagnostic d'intégrité</h2><p className="muted">Vérifie SQLite, les clés étrangères, la timeline active, les Rest Points, les timelines mortes et les fichiers visuels, sans afficher le contenu du Coffre MJ.</p><button className="secondary" onClick={runIntegrityCheck} disabled={busy}>Vérifier l'intégrité</button>{integrity && <div className={`integrity-report ${integrity.ok ? "ok" : "bad"}`}><strong>{integrity.ok ? "Intégrité validée" : "Anomalie détectée"}</strong><span>{new Date(integrity.checked_at).toLocaleString("fr-FR")}</span><ul>{integrity.checks.map((check) => <li key={check.code} className={check.ok ? "ok" : "bad"}>{check.ok ? "✓" : "✕"} {check.message}</li>)}</ul></div>}</article><article className="panel"><h2>Gestion de la campagne</h2><p className="muted">Tu peux créer une nouvelle campagne indépendante sans modifier la campagne active. Archiver masque une campagne sans supprimer ses données.</p><div className="action-row"><button className="secondary" onClick={createAnotherCampaign} disabled={busy}>Nouvelle campagne</button><button className="ghost" onClick={archiveCurrentCampaign} disabled={busy}>Archiver cette campagne</button></div></article></section>
      {renderArchivedCampaigns()}
      <section className="panel manual-correction"><h2>Correction manuelle exceptionnelle</h2><p className="muted">À utiliser uniquement pour corriger une erreur de saisie ou de synchronisation. Chaque correction crée d'abord une sauvegarde technique, avance la révision canonique et laisse une trace d'audit.</p><div className="manual-grid"><label>Donnée visible à corriger<select value={manualPlayerEntityId} onChange={(e) => setManualPlayerEntityId(e.target.value)}><option value="">Sélectionner…</option>{entities.map((e) => <option key={e.id} value={e.id}>{entityLabel(e)}</option>)}</select></label><label>Raison<input value={manualPlayerReason} onChange={(e) => setManualPlayerReason(e.target.value)} placeholder="Ex. erreur de saisie dans l'âge" /></label><label className="manual-json">Patch JSON<textarea value={manualPlayerPatch} onChange={(e) => setManualPlayerPatch(e.target.value)} spellCheck={false} placeholder={'{ "champ": "nouvelle valeur" }'} /></label></div><button className="secondary" disabled={busy || !manualPlayerEntityId || Boolean(campaign?.death_pending)} onClick={() => applyManualCorrection("PLAYER")}>Appliquer la correction auditée</button></section>
      <section className="panel asset-panel"><h2>Visuels de campagne</h2><p className="muted">Les visuels importés sont copiés dans le stockage local de Kitaba et inclus dans les sauvegardes <code>.kitaba</code>. Pour les personnages importants, conserve une image de référence et ajoute ensuite des variantes cohérentes plutôt que de réinventer leur apparence.</p><div className="asset-actions"><button className="secondary" onClick={() => importVisual("player_portrait")}>Importer / remplacer le portrait</button><button className="secondary" onClick={() => importVisual("world_map")}>Importer / remplacer la carte</button><button className="secondary" onClick={() => importVisual("npc_portrait")}>Ajouter portrait PNJ</button><button className="secondary" onClick={() => importVisual("other_image")}>Ajouter image</button><span>{assets.length} visuel(s) géré(s) par la campagne</span></div></section>
      <section className="panel audit-panel"><h2>Historique technique récent</h2><p className="muted">Cet historique n'affiche jamais le contenu du Coffre MJ.</p>{auditEvents.length === 0 ? <div className="empty-inline">Aucun événement technique.</div> : <div className="audit-list">{auditEvents.map((event) => <div className="audit-row" key={event.id}><div><strong>{event.event_type.replaceAll("_", " ")}</strong><span>{event.summary}</span></div><time>{new Date(event.created_at).toLocaleString("fr-FR")}</time></div>)}</div>}</section>
    </>;
  }

  function renderMedia() {
    return <div className="media-stack"><section className="panel visual-continuity"><div className="eyebrow">Continuité visuelle</div><h2>Références de campagne</h2><p>Les portraits et illustrations canoniques servent de références visuelles. Le MJ doit conserver les traits stables d'un personnage et créer des variantes cohérentes lorsque son état change : blessure, maladie, fatigue, nouvelle tenue, entrée héroïque ou autre moment marquant.</p><div className="visual-rule-grid"><span><b>1.</b> Identité visuelle textuelle fixée</span><span><b>2.</b> Image de référence importée</span><span><b>3.</b> Variantes = même personnage, nouvel état</span><span><b>4.</b> Scènes de groupe = références déjà établies</span></div></section><section className="panel"><h2>Médiathèque de campagne</h2><p className="muted">Portraits et illustrations conservés localement et inclus dans les sauvegardes. Une image ne crée jamais seule un fait canonique : le texte et l'état du personnage restent prioritaires.</p><div className="action-row"><button className="secondary" onClick={() => importVisual("npc_portrait")}>Ajouter un portrait PNJ</button><button className="secondary" onClick={() => importVisual("other_image")}>Ajouter une illustration</button><button className="ghost" onClick={() => importVisual("player_portrait")}>Portrait du personnage</button><button className="ghost" onClick={() => importVisual("world_map")}>Carte du monde</button></div>{assets.length === 0 ? <div className="empty-inline">Aucun visuel importé.</div> : <div className="audit-list">{assets.map((asset) => <div className="audit-row" key={asset.id}><div><strong>{asset.kind.replaceAll("_", " ")}</strong><span>{new Date(asset.created_at).toLocaleString("fr-FR")}</span></div><button className="ghost small" onClick={() => previewMediaAsset(asset)}>{mediaPreviewAssetId === asset.id ? "Actualiser" : "Voir"}</button></div>)}</div>}{mediaPreviewUrl && <div className="media-preview"><img src={mediaPreviewUrl} alt="Prévisualisation du visuel sélectionné" /></div>}</section></div>;
  }

  function renderGmVault() {
    if (!gmUnlocked) return <section className="panel vault-lock"><div className="vault-icon">◆</div><h2>Coffre MJ verrouillé</h2><p>Cette section contient les vérités cachées, motivations, secrets, événements hors champ et données de continuité destinées au MJ.</p><button className="danger" onClick={unlockGm}>Afficher les spoilers MJ</button></section>;
    const hiddenMarkers = gmEntities.filter((e) => ["map_marker", "place", "current_location", "gm_place", "gm_map_marker", "dungeon", "canon_fact"].includes(e.entity_type)).filter((e) => {
      const x = Number(e.data.x ?? e.data.map_x);
      const y = Number(e.data.y ?? e.data.map_y);
      return Number.isFinite(x) && Number.isFinite(y) && x >= 0 && x <= 1 && y >= 0 && y <= 1;
    });
    return <div className="vault-stack"><section className="panel vault-open"><div className="warning danger-warning">COFFRE MJ OUVERT — SPOILERS MAJEURS</div><h2>Carte MJ cachée</h2><p className="muted">Cette couche n'est jamais envoyée à l'interface joueur. Elle peut contenir des lieux inconnus, clandestins ou des vérités cartographiques.</p><div className="map-controls"><button className="ghost small" onClick={() => setGmMapZoom((z) => Math.max(.75, Number((z - .25).toFixed(2))))}>−</button><button className="ghost small" onClick={() => setGmMapZoom(1)}>{Math.round(gmMapZoom * 100)} %</button><button className="ghost small" onClick={() => setGmMapZoom((z) => Math.min(3, Number((z + .25).toFixed(2))))}>+</button></div><div className="map-frame gm-map"><div className="map-canvas" style={{width: `${gmMapZoom * 100}%`}}><img src={worldMapUrl ?? "/kitaba-world-map.png"} alt="Carte MJ de Kitaba" />{hiddenMarkers.map((m) => { const x = Number(m.data.x ?? m.data.map_x) * 100; const y = Number(m.data.y ?? m.data.map_y) * 100; const label = String(m.data.name ?? m.data.label ?? m.data.secret_name ?? "Lieu MJ"); return <div key={m.id} className="map-marker gm-secret" style={{left:`${x}%`,top:`${y}%`}} title={label}><span></span><b>{label}</b></div>; })}</div></div></section><section className="panel vault-open"><h2>Données MJ</h2><EntityList entities={gmEntities} empty="Aucune donnée MJ enregistrée." /></section><section className="panel manual-correction gm-manual"><h2>Correction manuelle MJ</h2><p className="muted">Le contenu de la correction et sa raison restent hors de l'historique joueur. Une sauvegarde technique est créée avant toute modification.</p><div className="manual-grid"><label>Donnée MJ<select value={manualGmEntityId} onChange={(e) => setManualGmEntityId(e.target.value)}><option value="">Sélectionner…</option>{gmEntities.map((e) => <option key={e.id} value={e.id}>{entityLabel(e)}</option>)}</select></label><label>Raison confidentielle<input value={manualGmReason} onChange={(e) => setManualGmReason(e.target.value)} placeholder="Raison de la correction" /></label><label className="manual-json">Patch JSON<textarea value={manualGmPatch} onChange={(e) => setManualGmPatch(e.target.value)} spellCheck={false} /></label></div><button className="danger" disabled={busy || !manualGmEntityId || Boolean(campaign?.death_pending)} onClick={() => applyManualCorrection("GM")}>Appliquer la correction MJ auditée</button></section></div>;
  }


  function renderMap() {
    const mapEntities = entities.filter((e) => ["map_marker", "place", "current_location", "settlement", "state", "region", "route", "dungeon"].includes(e.entity_type));
    return <section className="panel"><div className="map-header"><div><h2>Carte du monde</h2><p className="muted">Carte vivante de la campagne : zoom, déplacement et lieux cliquables. Chaque KITABA_UPDATE peut révéler de nouveaux repères sans afficher les lieux encore inconnus du personnage.</p></div><button className="ghost small" onClick={() => importVisual("world_map")}>Remplacer la carte</button></div><InteractiveMap imageUrl={worldMapUrl ?? "/kitaba-world-map.png"} entities={mapEntities} /><div className="map-known"><h3>Lieux connus</h3><EntityList entities={mapEntities} empty="Aucun lieu connu n'est encore positionné sur la carte." /></div></section>;
  }

  function navigateTo(section: SectionKey) {
    if (section !== "gm_vault" && gmUnlocked) {
      setGmUnlocked(false);
      setGmEntities([]);
      setManualGmEntityId("");
      setManualGmPatch("{}");
      setManualGmReason("");
    }
    setActive(section);
  }

  function renderSection() {
    if (active === "overview") return renderOverview();
    if (active === "sync") return renderSync();
    if (active === "checkpoints") return renderCheckpoints();
    if (active === "gm_vault") return renderGmVault();
    if (active === "map") return renderMap();
    if (active === "world") return <section className="panel"><h2>État du monde connu</h2><p className="muted">Factions, institutions, marchés, conflits, villes et autres changements durables que le personnage peut légitimement connaître. Les évolutions hors champ inconnues restent dans le Coffre MJ.</p><EntityList entities={sectionEntities} empty="Aucun état mondial connu n'est encore enregistré." /></section>;
    if (active === "media") return renderMedia();
    if (active === "character") return <><CharacterView entities={sectionEntities} /><section className="panel portrait-tools"><h2>Portrait</h2><p className="muted">Le portrait est purement visuel et n'altère jamais le canon narratif.</p><button className="secondary" onClick={() => importVisual("player_portrait")}>{portraitUrl ? "Remplacer le portrait" : "Importer un portrait"}</button></section></>;
    if (active === "inventory") return <InventoryView entities={sectionEntities} />;
    if (active === "relations") return <RelationsView entities={sectionEntities} />;
    if (active === "knowledge") return <KnowledgeView entities={sectionEntities} />;
    if (active === "journal") return <JournalView entities={sectionEntities} />;
    if (active === "missions") return <MissionsView entities={sectionEntities} />;
    if (active === "skills") return <SkillsView entities={sectionEntities} />;
    if (active === "magic") return <MagicView entities={sectionEntities} />;
    if (active === "timeline") return <TimelineView entities={sectionEntities} />;
    if (active === "adventurer_card") return <AdventurerCardView entities={sectionEntities} />;
    return <section className="panel"><h2>{labels[active]}</h2><EntityList entities={sectionEntities} /></section>;
  }

  return (
    <div className="app-shell">
      <Sidebar campaign={campaign} entities={entities} active={active} onNavigate={navigateTo} portraitUrl={portraitUrl} mobileOpen={mobileNavOpen} onCloseMobile={() => setMobileNavOpen(false)} />
      {mobileNavOpen && <button className="mobile-backdrop" aria-label="Fermer la navigation" onClick={() => setMobileNavOpen(false)} />}
      <main>
        <header className="topbar"><div className="topbar-title"><button className="mobile-menu-button" aria-label="Ouvrir la navigation" onClick={() => setMobileNavOpen(true)}>☰</button><div><h1>{labels[active]}</h1><p>Mémoire canonique locale de Kitaba Solo</p></div></div><div className="top-actions">{campaigns.length > 1 && <select className="campaign-select" value={campaign?.id ?? ""} onChange={(e) => { setSelectedId(e.target.value); setSearchQuery(""); setActive("overview"); }}>{campaigns.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select>}{campaign && <input className="global-search" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Rechercher dans les connaissances du personnage…" />}<div className={`sync-pill ${campaign && campaign.last_gm_export_revision !== campaign.current_revision ? "needs-export" : "synced"}`}>{campaign ? (campaign.last_gm_export_revision === campaign.current_revision ? `Révision ${campaign.current_revision} · contexte MJ exporté` : `Révision ${campaign.current_revision} · contexte MJ à exporter`) : "Aucune campagne"}</div></div></header>
        {searchQuery.trim() && campaign && <section className="panel search-panel"><div className="search-head"><h2>Résultats de recherche</h2><button className="ghost small" onClick={() => setSearchQuery("")}>Fermer</button></div><EntityList entities={searchResults} empty="Aucun résultat dans les connaissances visibles du joueur." /></section>}
        {campaign?.death_pending && <section className="death-banner"><strong>Le personnage est mort dans la timeline active.</strong><span>{campaign.death_summary ?? "Mort confirmée par le MJ."} Le gameplay est verrouillé jusqu'au rollback vers un Rest Point autorisé.</span></section>}
        {!campaign ? <><section className="panel empty-state"><h2>Nouvelle campagne Kitaba Solo</h2><p>Crée uniquement un conteneur canonique vierge. La création du personnage se fera ensuite avec le MJ avant toute narration.</p><label style={{display:"grid",gap:".45rem",maxWidth:"34rem",margin:"1rem auto"}}>Nom de campagne<input value={newCampaignName} onChange={(e) => setNewCampaignName(e.target.value)} placeholder="Ex. Kitaba Solo — Playtest" /></label><div className="action-row"><button onClick={createCampaign} disabled={busy || !newCampaignName.trim()}>Créer la campagne vierge</button><button className="secondary" onClick={restoreBackup}>Restaurer un fichier .kitaba</button></div></section>{renderArchivedCampaigns()}</> : renderSection()}
        <div className="global-status" aria-live="polite">{status}</div>
      </main>
    </div>
  );
}
