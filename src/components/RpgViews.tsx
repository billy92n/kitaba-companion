import { useEffect, useMemo, useState } from "react";
import type { EntityDocument } from "../lib/types";
import { backend } from "../lib/backend";
import { valueFr } from "../lib/frenchUi";
import { VisualReferenceGallery } from "./VisualReferenceGallery";
import { RelationsNetworkView } from "./RelationsNetworkView";
import { AdventurerCardView, MagicView, SkillsView, TimelineView } from "./ProgressionViews";
import "../player-hubs.css";

function text(value: unknown, fallback = "—"): string {
  if (value === null || value === undefined || value === "") return fallback;
  const localized = valueFr(value);
  return localized === "—" ? fallback : localized;
}

function labelFromData(data: Record<string, unknown>, fallback: string) {
  return text(data.name ?? data.title ?? data.label ?? data.known_name ?? data.first_name, fallback);
}

function shortText(value: unknown, fallback: string, max = 150) {
  const raw = text(value, fallback).trim();
  if (raw.length <= max) return raw;
  const sentence = raw.slice(0, max + 1).match(/^(.{40,150}?[.!?])(?:\s|$)/)?.[1];
  if (sentence) return sentence;
  return `${raw.slice(0, max).trimEnd()}…`;
}

function visualIdentitySummary(value: unknown): string {
  if (!value || typeof value !== "object" || Array.isArray(value)) return typeof value === "string" ? valueFr(value) : "";
  const identity = value as Record<string, unknown>;
  const parts = [
    identity.apparent_age,
    identity.build,
    identity.face,
    identity.hair,
    identity.eyes,
    identity.distinctive_features,
    identity.usual_clothing,
  ].map((item) => text(item, "")).filter(Boolean);
  return parts.join(" · ");
}

function currentVisualState(data: Record<string, unknown>) {
  const value = data.current_visual_state ?? data.visual_state;
  return typeof value === "string" ? value : null;
}

async function selectedCampaignId(): Promise<string | null> {
  const selected = document.querySelector<HTMLSelectElement>(".campaign-select")?.value;
  if (selected) return selected;
  const campaigns = await backend.listCampaigns();
  return campaigns[0]?.id ?? null;
}

function useFullPlayerEntities(seed: EntityDocument[]) {
  const [all, setAll] = useState<EntityDocument[]>(seed);

  useEffect(() => {
    let cancelled = false;
    setAll(seed);
    (async () => {
      const campaignId = await selectedCampaignId();
      if (!campaignId) return;
      const rows = await backend.listEntities(campaignId, false);
      if (!cancelled) setAll(rows);
    })().catch(() => undefined);
    return () => { cancelled = true; };
  }, [seed]);

  return all;
}

type CharacterTab = "profile" | "inventory" | "skills" | "magic" | "card";

export function CharacterView({ entities }: { entities: EntityDocument[] }) {
  const allEntities = useFullPlayerEntities(entities);
  const [tab, setTab] = useState<CharacterTab>("profile");
  const pcEntity = allEntities.find((e) => e.entity_type === "player_character");
  const pc = pcEntity?.data ?? {};
  const awakening = allEntities.find((e) => e.entity_type === "awakening")?.data;
  const characteristics = allEntities.filter((e) => e.entity_type === "characteristic");
  const specialized = allEntities.filter((e) => e.entity_type === "specialized_stat");
  const injuries = allEntities.filter((e) => ["injury", "status_effect"].includes(e.entity_type));
  const hpCurrent = pc.hp_current ?? pc.hp;
  const hpMax = pc.hp_max;
  const manaCurrent = pc.mana_current ?? pc.mana;
  const manaMax = pc.mana_max;
  const hasHp = hpCurrent !== undefined && hpCurrent !== null || hpMax !== undefined && hpMax !== null;
  const hasMana = manaCurrent !== undefined && manaCurrent !== null || manaMax !== undefined && manaMax !== null;
  const visualIdentity = visualIdentitySummary(pc.visual_identity);

  const hasSkills = allEntities.some((e) => ["skill", "mastery"].includes(e.entity_type));
  const hasMagic = hasMana || allEntities.some((e) => ["magic", "spell", "affinity", "invocation", "contract", "enchantment", "known_aptitude"].includes(e.entity_type));
  const hasCard = pc.official_rank != null || pc.rank != null || allEntities.some((e) => ["adventurer_card", "evaluation", "certification"].includes(e.entity_type));

  const tabs = useMemo(() => {
    const rows: Array<[CharacterTab, string]> = [["profile", "Profil"], ["inventory", "Inventaire"]];
    if (hasSkills) rows.push(["skills", "Compétences"]);
    if (hasMagic) rows.push(["magic", "Magie"]);
    if (hasCard) rows.push(["card", "Carte d’aventurier"]);
    return rows;
  }, [hasSkills, hasMagic, hasCard]);

  useEffect(() => {
    if (!tabs.some(([key]) => key === tab)) setTab("profile");
  }, [tabs, tab]);

  return <div className="player-hub">
    <nav className="player-hub-tabs" aria-label="Rubriques du personnage">
      {tabs.map(([key, label]) => <button key={key} className={tab === key ? "active" : ""} onClick={() => setTab(key)}>{label}</button>)}
    </nav>

    {tab === "inventory" ? <InventoryView entities={allEntities} /> : null}
    {tab === "skills" ? <SkillsView entities={allEntities} /> : null}
    {tab === "magic" ? <MagicView entities={allEntities} /> : null}
    {tab === "card" ? <AdventurerCardView entities={allEntities} /> : null}

    {tab === "profile" && <div className="character-layout">
      <section className="panel character-identity">
        <div className="eyebrow">Identité</div>
        <h2>{text(pc.first_name ?? pc.name, "Personnage")}</h2>
        {pcEntity && <VisualReferenceGallery subjectEntityId={pcEntity.id} currentState={currentVisualState(pc)} limit={3} />}
        <div className="identity-grid">
          <div><span>Espèce</span><strong>{text(pc.species)}</strong></div>
          <div><span>Âge</span><strong>{text(pc.age)}</strong></div>
          <div><span>Sexe</span><strong>{text(pc.sex)}</strong></div>
          <div><span>Stade biologique</span><strong>{text(pc.biological_stage)}</strong></div>
          <div><span>Statut social</span><strong>{text(pc.social_status)}</strong></div>
          <div><span>Profession</span><strong>{text(pc.profession)}</strong></div>
        </div>
        {pc.appearance ? <p className="description-block">{text(pc.appearance)}</p> : null}
        {visualIdentity && <p className="visual-identity-summary"><b>Référence visuelle stable</b><span>{visualIdentity}</span></p>}
      </section>

      {(hasHp || hasMana) && <section className="panel resource-panel">
        <h2>Ressources connues</h2>
        <div className="resource-bars">
          {hasHp && <Resource label="PV" current={hpCurrent} max={hpMax} />}
          {hasMana && <Resource label="Mana" current={manaCurrent} max={manaMax} />}
        </div>
      </section>}

      <section className="panel">
        <h2>Caractéristiques</h2>
        {characteristics.length === 0 ? <div className="empty-inline">Aucune évaluation enregistrée.</div> : <div className="stat-table">
          {characteristics.map((e) => <div className="stat-row" key={e.id}>
            <strong>{labelFromData(e.data, "Caractéristique")}</strong>
            <span className="grade-chip">{text(e.data.grade ?? e.data.official_grade)}</span>
            <small>{text(e.data.feeling ?? e.data.observation ?? e.data.qualitative_progress, "")}</small>
          </div>)}
        </div>}
      </section>

      <section className="panel">
        <h2>Caractéristiques spécialisées</h2>
        {specialized.length === 0 ? <div className="empty-inline">Aucune caractéristique spécialisée révélée.</div> : <div className="stat-table">
          {specialized.map((e) => <div className="stat-row" key={e.id}><strong>{labelFromData(e.data, "Spécialisation")}</strong><span className="grade-chip">{text(e.data.grade ?? e.data.level ?? e.data.value)}</span><small>{text(e.data.observation, "")}</small></div>)}
        </div>}
      </section>

      {awakening && <section className="panel full-span">
        <h2>Éveil</h2>
        <div className="identity-grid">
          <div><span>Éveillé</span><strong>{text(awakening.awakened)}</strong></div>
          <div><span>Âge</span><strong>{text(awakening.age)}</strong></div>
          <div><span>Date</span><strong>{text(awakening.date)}</strong></div>
          <div><span>Lieu</span><strong>{text(awakening.location)}</strong></div>
          <div className="wide"><span>Manifestations connues</span><strong>{text(awakening.observed_manifestations ?? awakening.observation)}</strong></div>
        </div>
      </section>}

      <section className="panel full-span">
        <h2>Blessures & états</h2>
        {injuries.length === 0 ? <div className="empty-inline">Aucune blessure ou altération enregistrée.</div> : <div className="compact-list">{injuries.map((e) => <article key={e.id}><strong>{labelFromData(e.data, e.entity_type === "injury" ? "Blessure" : "État")}</strong><span>{text(e.data.status ?? e.data.severity ?? e.data.description)}</span></article>)}</div>}
      </section>
    </div>}
  </div>;
}

function Resource({ label, current, max }: { label: string; current: unknown; max: unknown }) {
  const c = typeof current === "number" ? current : Number(current);
  const m = typeof max === "number" ? max : Number(max);
  const known = Number.isFinite(c) && Number.isFinite(m) && m > 0;
  const pct = known ? Math.max(0, Math.min(100, (c / m) * 100)) : 0;
  return <div className="resource-row"><div className="resource-head"><strong>{label}</strong><span>{text(current)}{max !== undefined && max !== null ? ` / ${text(max)}` : ""}</span></div><div className="resource-track"><div className="resource-fill" style={{ width: `${pct}%` }} /></div></div>;
}

export function InventoryView({ entities }: { entities: EntityDocument[] }) {
  const items = entities.filter((e) => ["item", "inventory_item"].includes(e.entity_type));
  const equipment = entities.filter((e) => e.entity_type === "equipment");
  const wallets = entities.filter((e) => ["wallet", "currency", "debt"].includes(e.entity_type));
  const weight = items.reduce((sum, e) => {
    const qty = Number(e.data.quantity ?? 1);
    const unit = Number(e.data.unit_weight ?? e.data.weight ?? 0);
    return sum + (Number.isFinite(qty) && Number.isFinite(unit) ? qty * unit : 0);
  }, 0);
  return <div className="inventory-layout">
    <section className="panel inventory-summary"><div><span>Objets connus</span><strong>{items.length}</strong></div><div><span>Poids calculé</span><strong>{weight ? `${weight.toFixed(2)} kg` : "—"}</strong></div><div><span>Équipements</span><strong>{equipment.length}</strong></div></section>
    <section className="panel"><h2>Équipement</h2><ItemCards items={equipment} empty="Aucun équipement enregistré." /></section>
    <section className="panel full-span"><h2>Inventaire</h2><ItemCards items={items} empty="Inventaire vide." /></section>
    <section className="panel full-span"><h2>Argent & dettes</h2><ItemCards items={wallets} empty="Aucune monnaie ou dette enregistrée." /></section>
  </div>;
}

function ItemCards({ items, empty }: { items: EntityDocument[]; empty: string }) {
  if (!items.length) return <div className="empty-inline">{empty}</div>;
  return <div className="item-grid">{items.map((e) => <article className="item-card" key={e.id}><div className="item-title"><strong>{labelFromData(e.data, "Objet")}</strong>{e.data.quantity != null ? <span>× {text(e.data.quantity)}</span> : null}</div><p>{text(e.data.description ?? e.data.known_description, "Aucune description connue.")}</p><div className="item-meta"><span>{text(e.data.category, "")}</span>{e.data.equipped === true ? <b>Équipé</b> : null}{e.data.condition ? <span>{text(e.data.condition)}</span> : null}</div></article>)}</div>;
}

export function RelationsView({ entities }: { entities: EntityDocument[] }) {
  return <RelationsNetworkView entities={entities} />;
}

export function KnowledgeView({ entities }: { entities: EntityDocument[] }) {
  const rows = entities.filter((e) => ["knowledge", "rumor", "belief"].includes(e.entity_type));
  if (!rows.length) return <section className="panel"><h2>Connaissances</h2><div className="empty-inline">Aucune connaissance enregistrée ici.</div></section>;
  return <section className="panel"><h2>Connaissances du personnage</h2><div className="knowledge-list">{rows.map((e) => <article key={e.id} className="knowledge-card"><div className="knowledge-head"><strong>{labelFromData(e.data, "Information")}</strong><span className={`knowledge-type ${e.entity_type}`}>{e.entity_type === "rumor" ? "Rumeur" : e.entity_type === "belief" ? "Croyance" : "Connaissance"}</span></div><p>{text(e.data.content ?? e.data.text ?? e.data.description)}</p><div className="knowledge-meta"><span>Source : {text(e.data.source)}</span><span>Confiance : {text(e.data.confidence)}</span></div></article>)}</div></section>;
}

type JournalTab = "journal" | "missions" | "timeline";

export function JournalView({ entities }: { entities: EntityDocument[] }) {
  const allEntities = useFullPlayerEntities(entities);
  const [tab, setTab] = useState<JournalTab>("journal");
  const journal = allEntities.filter((e) => e.entity_type === "journal_entry");
  const missions = allEntities.filter((e) => ["mission", "quest"].includes(e.entity_type));
  const timeline = allEntities.filter((e) => ["timeline_event", "historical_event"].includes(e.entity_type));

  const tabs = useMemo(() => {
    const rows: Array<[JournalTab, string]> = [["journal", "Journal"]];
    if (missions.length) rows.push(["missions", "Quêtes"]);
    if (timeline.length) rows.push(["timeline", "Chronologie"]);
    return rows;
  }, [missions.length, timeline.length]);

  useEffect(() => {
    if (!tabs.some(([key]) => key === tab)) setTab("journal");
  }, [tabs, tab]);

  return <div className="player-hub">
    <nav className="player-hub-tabs" aria-label="Journal et quêtes">
      {tabs.map(([key, label]) => <button key={key} className={tab === key ? "active" : ""} onClick={() => setTab(key)}>{label}</button>)}
    </nav>
    {tab === "journal" ? <JournalEntries entities={journal} /> : null}
    {tab === "missions" ? <MissionsView entities={missions} /> : null}
    {tab === "timeline" ? <TimelineView entities={timeline} /> : null}
  </div>;
}

function JournalEntries({ entities }: { entities: EntityDocument[] }) {
  return <section className="panel"><h2>Journal</h2>{entities.length === 0 ? <div className="empty-inline">Aucune entrée.</div> : <div className="timeline-list">{[...entities].reverse().map((e) => <article key={e.id} className="timeline-card"><div className="timeline-date">{text(e.data.game_time ?? e.data.date)}</div><div><strong>{labelFromData(e.data, "Événement")}</strong><span>{text(e.data.location, "")}</span><p>{text(e.data.summary ?? e.data.details ?? e.data.description)}</p></div></article>)}</div>}</section>;
}

export function MissionsView({ entities }: { entities: EntityDocument[] }) {
  const rows = entities.filter((e) => ["mission", "quest"].includes(e.entity_type));
  return <section className="panel"><h2>Quêtes</h2>{rows.length === 0 ? <div className="empty-inline">Aucune quête connue.</div> : <div className="mission-grid">{rows.map((e) => <article className="mission-card" key={e.id}><div className="mission-head"><strong>{labelFromData(e.data, "Quête")}</strong><span>{text(e.data.status)}</span></div><p>{text(e.data.description ?? e.data.summary)}</p>{Array.isArray(e.data.objectives) ? <ul>{e.data.objectives.map((o, i) => <li key={i}>{text(o)}</li>)}</ul> : null}<small>Récompense : {text(e.data.reward_announced ?? e.data.reward)}</small></article>)}</div>}</section>;
}

function CompactEntities({ entities, empty }: { entities: EntityDocument[]; empty: string }) {
  if (!entities.length) return <div className="empty-inline">{empty}</div>;
  return <div className="compact-list">{entities.map((e) => <article key={e.id}><strong>{labelFromData(e.data, "Élément")}</strong><span>{shortText(e.data.player_impression ?? e.data.description ?? e.data.status ?? e.data.value, "—", 180)}</span></article>)}</div>;
}
