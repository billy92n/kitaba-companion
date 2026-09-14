import type { EntityDocument } from "../lib/types";
import { entityTypeLabelFr, fieldLabelFr, valueFr } from "../lib/frenchUi";
import { VisualReferenceGallery } from "./VisualReferenceGallery";

function valueToText(value: unknown): string {
  return valueFr(value);
}

function titleFor(entity: EntityDocument) {
  const d = entity.data;
  for (const key of ["title", "name", "first_name", "known_name", "label", "subject"]) {
    const v = d[key];
    if (typeof v === "string" && v.trim()) return v;
  }
  return entityTypeLabelFr(entity.entity_type);
}

function visualStateFor(entity: EntityDocument) {
  const value = entity.data.current_visual_state ?? entity.data.visual_state;
  return typeof value === "string" ? value : null;
}

function supportsInlineVisual(entity: EntityDocument) {
  return ["player_character", "npc", "place", "settlement", "current_location", "region", "state", "dungeon"].includes(entity.entity_type);
}

export function EntityList({ entities, empty = "Aucune donnée connue." }: { entities: EntityDocument[]; empty?: string }) {
  if (!entities.length) return <div className="empty-inline">{empty}</div>;
  return (
    <div className="entity-grid">
      {entities.map((entity) => (
        <article className="entity-card" key={entity.id}>
          <div className="entity-card-head">
            <h3>{titleFor(entity)}</h3>
            <span>v{entity.entity_version}</span>
          </div>
          {supportsInlineVisual(entity) && <VisualReferenceGallery subjectEntityId={entity.id} currentState={visualStateFor(entity)} compact limit={3} />}
          <div className="data-list">
            {Object.entries(entity.data).map(([key, value]) => (
              <div key={key}><span>{fieldLabelFr(key)}</span><strong>{valueToText(value)}</strong></div>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}