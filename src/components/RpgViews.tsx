import type { EntityDocument } from "../lib/types";

function text(value: unknown, fallback = "—"): string {
  if (value === null || value === undefined || value === "") return fallback;
  if (typeof value === "boolean") return value ? "Oui" : "Non";
  if (Array.isArray(value)) return value.map((v) => text(v, "")).filter(Boolean).join(", ") || fallback;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function labelFromData(data: Record<string, unknown>, fallback: string) {
  return text(data.name ?? data.title ?? data.label ?? data.known_name ?? data.first_name, fallback);
}

export function CharacterView({ entities }: { entities: EntityDocument[] }) {
  const pc = entities.find((e) => e.entity_type === "player_character")?.data ?? {};
  const awakening = entities.find((e) => e.entity_type === "awakening")?.data;
  const characteristics = entities.filter((e) => e.entity_type === "characteristic");
  const specialized = entities.filter((e) => e.entity_type === "specialized_stat");
  const injuries = entities.filter((e) => ["injury", "status_effect"].includes(e.entity_type));
  const hpCurrent = pc.hp_current ?? pc.hp;
  const hpMax = pc.hp_max;
  const manaCurrent = pc.mana_current ?? pc.mana;
  const manaMax = pc.mana_max;
  const hasHp = hpCurrent !== undefined && hpCurrent !== null || hpMax !== undefined && hpMax !== null;
  const hasMana = manaCurrent !== undefined && manaCurrent !== null || manaMax !== undefined && manaMax !== null;

  return <div className="character-layout">
    <section className="panel character-identity">
      <div className="eyebrow">Identité</div>
      <h2>{text(pc.first_name ?? pc.name, "Personnage")}</h2>
      <div className="identity-grid">
        <div><span>Espèce</span><strong>{text(pc.species)}</strong></div>
        <div><span>Âge</span><strong>{text(pc.age)}</strong></div>
        <div><span>Sexe</span><strong>{text(pc.sex)}</strong></div>
        <div><span>Stade biologique</span><strong>{text(pc.biological_stage)}</strong></div>
        <div><span>Statut social</span><strong>{text(pc.social_status)}</strong></div>
        <div><span>Profession</span><strong>{text(pc.profession)}</strong></div>
      </div>
      {pc.appearance ? <p className="description-block">{text(pc.appearance)}</p> : null}
    </section>

    {(hasHp || hasMana) && <section className="panel resource-panel">
      <h2>Ressources connues</h2>
      <div className="resource-bars">
        {hasHp && <Resource label="HP" current={hpCurrent} max={hpMax} />}
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
  const npcs = entities.filter((e) => e.entity_type === "npc");
  const relations = entities.filter((e) => e.entity_type === "relationship");
  const reps = entities.filter((e) => e.entity_type === "reputation");
  return <div className="relations-layout">
    <section className="panel full-span"><h2>Personnes connues</h2>{npcs.length === 0 ? <div className="empty-inline">Personne enregistrée.</div> : <div className="npc-grid">{npcs.map((e) => <article className="npc-card" key={e.id}><div className="npc-avatar">{labelFromData(e.data, "?").slice(0,1).toUpperCase()}</div><div><strong>{labelFromData(e.data, "Personne inconnue")}</strong><span>{[text(e.data.species, ""), text(e.data.profession, "")].filter(Boolean).join(" · ")}</span><p>{text(e.data.player_impression ?? e.data.known_information ?? e.data.description, "Aucune impression particulière.")}</p></div></article>)}</div>}</section>
    <section className="panel"><h2>Relations perçues</h2><CompactEntities entities={relations} empty="Aucune relation explicitement perçue." /></section>
    <section className="panel"><h2>Réputation</h2><CompactEntities entities={reps} empty="Aucune réputation enregistrée." /></section>
  </div>;
}

export function KnowledgeView({ entities }: { entities: EntityDocument[] }) {
  const rows = entities.filter((e) => ["knowledge", "rumor", "belief"].includes(e.entity_type));
  if (!rows.length) return <section className="panel"><h2>Connaissances</h2><div className="empty-inline">Aucune connaissance enregistrée ici.</div></section>;
  return <section className="panel"><h2>Connaissances du personnage</h2><div className="knowledge-list">{rows.map((e) => <article key={e.id} className="knowledge-card"><div className="knowledge-head"><strong>{labelFromData(e.data, "Information")}</strong><span className={`knowledge-type ${e.entity_type}`}>{e.entity_type === "rumor" ? "Rumeur" : e.entity_type === "belief" ? "Croyance" : "Connaissance"}</span></div><p>{text(e.data.content ?? e.data.text ?? e.data.description)}</p><div className="knowledge-meta"><span>Source : {text(e.data.source)}</span><span>Confiance : {text(e.data.confidence)}</span></div></article>)}</div></section>;
}

export function JournalView({ entities }: { entities: EntityDocument[] }) {
  const rows = entities.filter((e) => e.entity_type === "journal_entry");
  return <section className="panel"><h2>Journal</h2>{rows.length === 0 ? <div className="empty-inline">Aucune entrée.</div> : <div className="timeline-list">{[...rows].reverse().map((e) => <article key={e.id} className="timeline-card"><div className="timeline-date">{text(e.data.game_time ?? e.data.date)}</div><div><strong>{labelFromData(e.data, "Événement")}</strong><span>{text(e.data.location, "")}</span><p>{text(e.data.summary ?? e.data.details ?? e.data.description)}</p></div></article>)}</div>}</section>;
}

export function MissionsView({ entities }: { entities: EntityDocument[] }) {
  const rows = entities.filter((e) => ["mission", "quest"].includes(e.entity_type));
  return <section className="panel"><h2>Missions</h2>{rows.length === 0 ? <div className="empty-inline">Aucune mission connue.</div> : <div className="mission-grid">{rows.map((e) => <article className="mission-card" key={e.id}><div className="mission-head"><strong>{labelFromData(e.data, "Mission")}</strong><span>{text(e.data.status)}</span></div><p>{text(e.data.description ?? e.data.summary)}</p>{Array.isArray(e.data.objectives) ? <ul>{e.data.objectives.map((o, i) => <li key={i}>{text(o)}</li>)}</ul> : null}<small>Récompense : {text(e.data.reward_announced ?? e.data.reward)}</small></article>)}</div>}</section>;
}

function CompactEntities({ entities, empty }: { entities: EntityDocument[]; empty: string }) {
  if (!entities.length) return <div className="empty-inline">{empty}</div>;
  return <div className="compact-list">{entities.map((e) => <article key={e.id}><strong>{labelFromData(e.data, e.entity_type)}</strong><span>{text(e.data.player_impression ?? e.data.description ?? e.data.status ?? e.data.value)}</span></article>)}</div>;
}
