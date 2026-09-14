import { useMemo, useState } from "react";
import type { EntityDocument } from "../lib/types";
import { fieldLabelFr, valueFr } from "../lib/frenchUi";
import { VisualReferenceGallery } from "./VisualReferenceGallery";

type CategoryKey = "all" | "settlements" | "figures" | "lineages" | "bestiary" | "powers" | "concepts" | "world" | "other";

type Category = {
  key: Exclude<CategoryKey, "all">;
  label: string;
  description: string;
  types: Set<string>;
};

const categories: Category[] = [
  { key: "settlements", label: "Lieux & localités", description: "Villes, villages, régions, routes, donjons et lieux remarquables connus.", types: new Set(["settlement", "place", "region", "dungeon", "route"]) },
  { key: "figures", label: "Figures & relations", description: "PNJ nommés, héros, dirigeants, mentors, rivaux et autres personnes durablement pertinentes.", types: new Set(["npc", "hero", "notable", "leader", "ruler", "mentor", "rival", "character"]) },
  { key: "lineages", label: "Relations & lignées", description: "Liens connus, parentés, maisons, clans, filiations et dynasties.", types: new Set(["relationship", "family_relation", "kinship", "lineage", "dynasty", "house", "clan"]) },
  { key: "bestiary", label: "Bestiaire & troupes", description: "Créatures, monstres, unités et ennemis étudiés, avec forces/faiblesses lorsqu'elles sont connues.", types: new Set(["monster", "creature", "beast", "species", "troop", "unit", "military_unit", "enemy_type", "bestiary_entry"]) },
  { key: "powers", label: "Royaumes & factions", description: "États, royaumes, guildes, organisations, institutions et puissances politiques connues.", types: new Set(["state", "kingdom", "faction", "organization", "guild", "political_state"]) },
  { key: "concepts", label: "Concepts & savoirs", description: "Concepts du monde, rumeurs, croyances, coutumes, lois, religions, langues et savoirs découverts.", types: new Set(["knowledge", "rumor", "belief", "concept", "lore", "magic_concept", "religion", "language", "custom", "law", "title", "profession", "rank_concept"]) },
  { key: "world", label: "Monde & histoire", description: "Histoire, conflits, économie, environnement, peuples et grands changements connus du monde.", types: new Set(["world_event", "historical_event", "timeline_event", "conflict", "environment_state", "economy_state", "market", "infrastructure", "resource_state", "people", "culture", "geography"]) },
  { key: "other", label: "Autres découvertes", description: "Découvertes durables explicitement conservées dans le livre du joueur.", types: new Set(["discovery", "canon_fact", "world_fact", "lore_entry"]) },
];

function categoryFor(entity: EntityDocument): Exclude<CategoryKey, "all"> | null {
  const override = entity.data.encyclopedia_category;
  if (typeof override === "string") {
    const normalized = override.trim().toLowerCase();
    const byKey = categories.find((category) => category.key === normalized);
    if (byKey) return byKey.key;
  }
  const found = categories.find((category) => category.types.has(entity.entity_type));
  if (found) return found.key;
  if (entity.data.encyclopedia_include === true) return "other";
  return null;
}

function textValue(value: unknown): string {
  return valueFr(value);
}

function titleFor(entity: EntityDocument) {
  for (const key of ["name", "title", "first_name", "known_name", "label", "subject"]) {
    const value = entity.data[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return "Découverte";
}

function summaryFor(entity: EntityDocument) {
  for (const key of ["known_summary", "summary", "description", "notes", "knowledge_summary"]) {
    const value = entity.data[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return null;
}

function certaintyFor(entity: EntityDocument) {
  for (const key of ["epistemic_status", "knowledge_status", "certainty", "confidence"]) {
    const value = entity.data[key];
    if (typeof value === "string" && value.trim()) return valueFr(value);
  }
  if (entity.entity_type === "rumor") return "Rumeur";
  if (entity.entity_type === "belief") return "Croyance";
  return null;
}

function supportsInlineVisual(entity: EntityDocument) {
  return ["npc", "hero", "notable", "leader", "ruler", "place", "settlement", "region", "state", "kingdom", "dungeon", "monster", "creature"].includes(entity.entity_type);
}

const hiddenKeys = new Set([
  "name", "title", "first_name", "known_name", "label", "subject",
  "known_summary", "summary", "description", "notes", "knowledge_summary",
  "encyclopedia_category", "encyclopedia_include",
  "epistemic_status", "knowledge_status", "certainty", "confidence",
  "x", "y", "map_x", "map_y", "map_importance", "priority", "importance",
  "current", "place_id", "settlement_id", "map_marker_id", "entity_id", "source_gm_entity_id",
]);

export function EncyclopediaView({ entities }: { entities: EntityDocument[] }) {
  const [activeCategory, setActiveCategory] = useState<CategoryKey>("all");
  const [query, setQuery] = useState("");

  const entries = useMemo(() => entities.map((entity) => ({ entity, category: categoryFor(entity) })).filter((row): row is { entity: EntityDocument; category: Exclude<CategoryKey, "all"> } => Boolean(row.category)), [entities]);

  const counts = useMemo(() => {
    const result = new Map<string, number>();
    for (const row of entries) result.set(row.category, (result.get(row.category) ?? 0) + 1);
    return result;
  }, [entries]);

  const visible = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("fr");
    return entries.filter(({ entity, category }) => {
      if (activeCategory !== "all" && category !== activeCategory) return false;
      if (!normalized) return true;
      return `${titleFor(entity)} ${JSON.stringify(entity.data)}`.toLocaleLowerCase("fr").includes(normalized);
    });
  }, [entries, activeCategory, query]);

  return (
    <div className="encyclopedia-shell">
      <section className="panel encyclopedia-intro">
        <div className="eyebrow">Livre du joueur</div>
        <h2>Encyclopédie de campagne</h2>
        <p>Tout ce qui apparaît ici provient uniquement des connaissances visibles du personnage. Une rumeur reste une rumeur ; une information inconnue du joueur n'est jamais révélée par l'Encyclopédie.</p>
        <div className="encyclopedia-summary"><strong>{entries.length}</strong><span>entrée(s) connue(s)</span></div>
      </section>

      <section className="panel encyclopedia-browser">
        <div className="encyclopedia-toolbar">
          <div className="encyclopedia-tabs" role="tablist" aria-label="Catégories de l'encyclopédie">
            <button className={activeCategory === "all" ? "active" : ""} onClick={() => setActiveCategory("all")}>Tout <span>{entries.length}</span></button>
            {categories.map((category) => <button key={category.key} className={activeCategory === category.key ? "active" : ""} onClick={() => setActiveCategory(category.key)}>{category.label} <span>{counts.get(category.key) ?? 0}</span></button>)}
          </div>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Rechercher dans l'encyclopédie…" aria-label="Rechercher dans l'encyclopédie" />
        </div>

        {activeCategory !== "all" && <p className="muted encyclopedia-category-note">{categories.find((category) => category.key === activeCategory)?.description}</p>}

        {visible.length === 0 ? <div className="empty-inline">Aucune entrée connue dans cette catégorie pour le moment.</div> : <div className="encyclopedia-grid">{visible.map(({ entity, category }) => {
          const summary = summaryFor(entity);
          const certainty = certaintyFor(entity);
          const details = Object.entries(entity.data).filter(([key, value]) => !hiddenKeys.has(key) && value != null);
          return <article className="encyclopedia-entry" key={entity.id}>
            <header><div><span className="encyclopedia-category">{categories.find((item) => item.key === category)?.label ?? "Autres découvertes"}</span><h3>{titleFor(entity)}</h3></div>{certainty && <span className="encyclopedia-certainty">{certainty}</span>}</header>
            {supportsInlineVisual(entity) && <VisualReferenceGallery subjectEntityId={entity.id} currentState={typeof entity.data.current_visual_state === "string" ? entity.data.current_visual_state : null} compact limit={2} />}
            {summary && <p className="encyclopedia-entry-summary">{summary}</p>}
            {details.length > 0 && <dl>{details.map(([key, value]) => <div key={key}><dt>{fieldLabelFr(key)}</dt><dd>{textValue(value)}</dd></div>)}</dl>}
          </article>;
        })}</div>}
      </section>
    </div>
  );
}
