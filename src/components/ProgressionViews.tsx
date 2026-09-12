import type { EntityDocument } from "../lib/types";

function text(value: unknown, fallback = "—"): string {
  if (value === null || value === undefined || value === "") return fallback;
  if (typeof value === "boolean") return value ? "Oui" : "Non";
  if (Array.isArray(value)) return value.map((v) => text(v, "")).filter(Boolean).join(", ") || fallback;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function label(data: Record<string, unknown>, fallback: string) {
  return text(data.name ?? data.title ?? data.label ?? data.known_name, fallback);
}

function chip(value: unknown, fallback = "—") {
  const v = text(value, fallback);
  return <span className="grade-chip">{v}</span>;
}

export function SkillsView({ entities }: { entities: EntityDocument[] }) {
  const skills = entities.filter((e) => ["skill", "mastery"].includes(e.entity_type));
  if (!skills.length) {
    return <section className="panel"><h2>Compétences</h2><div className="empty-inline">Aucune compétence enregistrée.</div></section>;
  }
  const categories = new Map<string, EntityDocument[]>();
  for (const skill of skills) {
    const category = text(skill.data.category, "Autres");
    const list = categories.get(category) ?? [];
    list.push(skill);
    categories.set(category, list);
  }
  return <div className="skill-groups">
    {[...categories.entries()].map(([category, rows]) => <section className="panel" key={category}>
      <h2>{category}</h2>
      <div className="skill-list">
        {rows.map((e) => <article className="skill-row" key={e.id}>
          <div className="skill-main">
            <strong>{label(e.data, e.entity_type === "mastery" ? "Maîtrise" : "Compétence")}</strong>
            <span>{text(e.data.description ?? e.data.observation ?? e.data.notes, "")}</span>
          </div>
          <div className="skill-level">{chip(e.data.level ?? e.data.mastery_level ?? e.data.qualitative_level)}</div>
          <small>{text(e.data.progress_feeling ?? e.data.qualitative_progress ?? e.data.last_progress, "")}</small>
        </article>)}
      </div>
    </section>)}
  </div>;
}

export function MagicView({ entities }: { entities: EntityDocument[] }) {
  const groups: Array<[string, string[], string]> = [
    ["Magies & techniques", ["magic", "spell"], "Aucune magie connue."],
    ["Affinités connues", ["affinity"], "Aucune affinité connue."],
    ["Invocations & contrats", ["invocation", "contract"], "Aucune invocation ou contrat connu."],
    ["Enchantements", ["enchantment"], "Aucun enchantement maîtrisé."],
    ["Aptitudes révélées", ["known_aptitude"], "Aucune aptitude singulière révélée."],
  ];

  return <div className="magic-layout">
    {groups.map(([title, types, empty]) => {
      const rows = entities.filter((e) => types.includes(e.entity_type));
      return <section className={`panel ${title === "Magies & techniques" ? "full-span" : ""}`} key={title}>
        <h2>{title}</h2>
        {!rows.length ? <div className="empty-inline">{empty}</div> : <div className="magic-grid">{rows.map((e) => <article className="magic-card" key={e.id}>
          <div className="magic-head"><strong>{label(e.data, "Capacité")}</strong>{e.data.level != null || e.data.grade != null ? chip(e.data.level ?? e.data.grade) : null}</div>
          <p>{text(e.data.description ?? e.data.known_effect ?? e.data.principle, "Aucune description connue.")}</p>
          <div className="magic-meta">
            {e.data.category ? <span>{text(e.data.category)}</span> : null}
            {e.data.cost ? <span>Coût : {text(e.data.cost)}</span> : null}
            {e.data.source ? <span>Source : {text(e.data.source)}</span> : null}
          </div>
        </article>)}</div>}
      </section>;
    })}
  </div>;
}

export function TimelineView({ entities }: { entities: EntityDocument[] }) {
  const rows = entities.filter((e) => ["timeline_event", "historical_event"].includes(e.entity_type));
  return <section className="panel">
    <h2>Chronologie connue</h2>
    <p className="muted">Cette chronologie ne montre que les événements que Sully connaît ou qui sont publics pour lui.</p>
    {!rows.length ? <div className="empty-inline">Aucun événement historique connu.</div> : <div className="timeline-list">
      {rows.map((e) => <article key={e.id} className="timeline-card">
        <div className="timeline-date">{text(e.data.game_time ?? e.data.date ?? e.data.period)}</div>
        <div>
          <strong>{label(e.data, "Événement")}</strong>
          <span>{text(e.data.location ?? e.data.region, "")}</span>
          <p>{text(e.data.summary ?? e.data.description ?? e.data.details)}</p>
        </div>
      </article>)}
    </div>}
  </section>;
}

export function AdventurerCardView({ entities }: { entities: EntityDocument[] }) {
  const card = entities.find((e) => e.entity_type === "adventurer_card")?.data;
  const evaluations = entities.filter((e) => e.entity_type === "evaluation");
  const certifications = entities.filter((e) => e.entity_type === "certification");

  if (!card) {
    return <section className="panel adventurer-empty">
      <div className="card-emblem">◇</div>
      <h2>Aucune carte d'aventurier</h2>
      <p className="muted">Aucun document professionnel d'aventurier n'est enregistré pour Sully.</p>
      {evaluations.length || certifications.length ? <div className="warning">Des évaluations ou certifications existent toutefois dans les données connues.</div> : null}
    </section>;
  }

  return <div className="adventurer-layout">
    <section className="panel adventurer-card-visual">
      <div className="adventurer-card-top"><span>CONCORDAT DES GUILDES</span><b>{text(card.official_rank ?? card.rank)}</b></div>
      <h2>{text(card.name ?? card.holder_name, "Sully")}</h2>
      <div className="identity-grid">
        <div><span>Espèce</span><strong>{text(card.species)}</strong></div>
        <div><span>Âge</span><strong>{text(card.age)}</strong></div>
        <div><span>Guilde</span><strong>{text(card.guild)}</strong></div>
        <div><span>Affiliation</span><strong>{text(card.affiliation)}</strong></div>
        <div><span>Statut</span><strong>{text(card.status ?? card.disciplinary_status)}</strong></div>
        <div><span>Identifiant</span><strong>{text(card.card_number ?? card.identifier)}</strong></div>
      </div>
      {card.official_observations ? <p className="description-block">{text(card.official_observations)}</p> : null}
    </section>
    <section className="panel"><h2>Historique des évaluations</h2>{!evaluations.length ? <div className="empty-inline">Aucune évaluation enregistrée.</div> : <div className="compact-list">{evaluations.map((e) => <article key={e.id}><strong>{text(e.data.date ?? e.data.game_time, "Évaluation")}</strong><span>{[text(e.data.rank ?? e.data.result, ""), text(e.data.observation, "")].filter(Boolean).join(" · ")}</span></article>)}</div>}</section>
    <section className="panel"><h2>Certifications</h2>{!certifications.length ? <div className="empty-inline">Aucune certification enregistrée.</div> : <div className="compact-list">{certifications.map((e) => <article key={e.id}><strong>{label(e.data, "Certification")}</strong><span>{text(e.data.status ?? e.data.description)}</span></article>)}</div>}</section>
  </div>;
}
