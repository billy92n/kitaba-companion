import { useEffect, useMemo, useState } from "react";
import type { EntityDocument } from "../lib/types";
import { backend } from "../lib/backend";
import { valueFr } from "../lib/frenchUi";
import { NpcPortraitControl } from "./NpcPortraitControl";
import "../relations-network.css";

function text(value: unknown, fallback = ""): string {
  if (value === null || value === undefined || value === "") return fallback;
  const localized = valueFr(value);
  return localized === "—" ? fallback : localized;
}

function entityName(entity: EntityDocument, fallback = "Personne inconnue") {
  return text(entity.data.name ?? entity.data.title ?? entity.data.label ?? entity.data.known_name ?? entity.data.first_name, fallback);
}

function short(value: unknown, fallback = "", max = 165) {
  const raw = text(value, fallback).trim();
  if (raw.length <= max) return raw;
  return `${raw.slice(0, max).trimEnd()}…`;
}

async function selectedCampaignId(): Promise<string | null> {
  const selected = document.querySelector<HTMLSelectElement>(".campaign-select")?.value;
  if (selected) return selected;
  const campaigns = await backend.listCampaigns();
  return campaigns[0]?.id ?? null;
}

function normalize(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("fr");
}

function stringValues(value: unknown): string[] {
  if (typeof value === "string" && value.trim()) return [value.trim()];
  if (!Array.isArray(value)) return [];
  const rows: string[] = [];
  for (const item of value) {
    if (typeof item === "string" && item.trim()) rows.push(item.trim());
    else if (item && typeof item === "object") {
      const record = item as Record<string, unknown>;
      for (const key of ["id", "entity_id", "name", "label"]) {
        const candidate = record[key];
        if (typeof candidate === "string" && candidate.trim()) rows.push(candidate.trim());
      }
    }
  }
  return rows;
}

function relationNarrative(relation: EntityDocument) {
  return text(
    relation.data.player_impression
      ?? relation.data.known_summary
      ?? relation.data.summary
      ?? relation.data.description
      ?? relation.data.known_information
      ?? relation.data.status,
    "",
  );
}

function relationType(relation: EntityDocument) {
  return text(
    relation.data.relationship_type
      ?? relation.data.relation_type
      ?? relation.data.kinship
      ?? relation.data.family_role
      ?? relation.data.relation
      ?? relation.data.role
      ?? relation.data.type,
    "",
  );
}

function directRoleFromNpc(npc: EntityDocument) {
  return text(
    npc.data.relation_to_player
      ?? npc.data.relationship_to_player
      ?? npc.data.player_relation
      ?? npc.data.family_role
      ?? npc.data.kinship_to_player
      ?? npc.data.role_to_player,
    "",
  );
}

function explicitParticipantTokens(relation: EntityDocument): string[] {
  const data = relation.data;
  const tokens = [
    ...stringValues(data.participant_ids),
    ...stringValues(data.subject_ids),
    ...stringValues(data.participants),
  ];
  for (const key of [
    "from_entity_id", "to_entity_id", "source_entity_id", "target_entity_id",
    "subject_entity_id", "object_entity_id", "actor_id", "subject_id", "object_id",
    "npc_id", "player_character_id", "person_a_id", "person_b_id", "character_a_id", "character_b_id",
    "from_name", "to_name", "subject_name", "target_name", "person_a", "person_b",
  ]) {
    tokens.push(...stringValues(data[key]));
  }
  return tokens;
}

function relationSearchText(relation: EntityDocument) {
  return normalize(`${entityName(relation, "")} ${relationType(relation)} ${relationNarrative(relation)} ${JSON.stringify(relation.data)}`);
}

function participantsFor(relation: EntityDocument, people: EntityDocument[]) {
  const tokens = new Set(explicitParticipantTokens(relation).map(normalize));
  const haystack = relationSearchText(relation);
  const matched = people.filter((person) => {
    if (tokens.has(normalize(person.id))) return true;
    const name = entityName(person, "");
    if (!name) return false;
    const n = normalize(name);
    if (tokens.has(n)) return true;
    return n.length >= 3 && haystack.includes(n);
  });
  return matched.filter((person, index) => matched.findIndex((row) => row.id === person.id) === index);
}

function genderHint(npc: EntityDocument) {
  return normalize(text(npc.data.sex ?? npc.data.gender, ""));
}

function kinshipRoleFromText(relation: EntityDocument, npc: EntityDocument, playerName: string) {
  const source = normalize(`${relationType(relation)} ${relationNarrative(relation)} ${entityName(relation, "")}`);
  const female = ["feminin", "female", "femme", "girl", "fille"].some((row) => genderHint(npc).includes(row));
  const male = ["masculin", "male", "homme", "boy", "garcon"].some((row) => genderHint(npc).includes(row));

  if (/\b(mere|maman|mother)\b/.test(source)) return `Mère de ${playerName}`;
  if (/\b(pere|papa|father)\b/.test(source)) return `Père de ${playerName}`;
  if (/\b(soeur|sister)\b/.test(source)) return `Sœur de ${playerName}`;
  if (/\b(frere|brother)\b/.test(source)) return `Frère de ${playerName}`;
  if (/\b(fraternel|fraternelle|fratrie|sibling)\b/.test(source)) return `${female ? "Sœur" : male ? "Frère" : "Fratrie"} de ${playerName}`;
  if (/\b(fille|daughter)\b/.test(source)) return `Fille de ${playerName}`;
  if (/\b(fils|son)\b/.test(source)) return `Fils de ${playerName}`;
  if (/\b(epouse|wife)\b/.test(source)) return `Épouse de ${playerName}`;
  if (/\b(epoux|mari|husband)\b/.test(source)) return `Époux de ${playerName}`;
  if (/\b(conjoint|conjointe|partner|partenaire)\b/.test(source)) return `Partenaire de ${playerName}`;
  if (/\b(famille|familial|familiale|parent)\b/.test(source)) return `Famille de ${playerName}`;
  return "";
}

function roleForNpc(npc: EntityDocument, relations: EntityDocument[], people: EntityDocument[], player: EntityDocument | null) {
  const direct = directRoleFromNpc(npc);
  if (direct) return direct;
  if (!player) return "";
  const playerName = entityName(player, "le personnage");
  for (const relation of relations) {
    const participants = participantsFor(relation, people);
    const containsNpc = participants.some((row) => row.id === npc.id) || relationSearchText(relation).includes(normalize(entityName(npc, "")));
    const containsPlayer = participants.some((row) => row.id === player.id) || relationSearchText(relation).includes(normalize(playerName));
    if (!containsNpc || !containsPlayer) continue;
    const derived = kinshipRoleFromText(relation, npc, playerName);
    if (derived) return derived;
    const structured = relationType(relation);
    if (structured) return `${structured} · ${playerName}`;
  }
  return "";
}

function visualState(npc: EntityDocument) {
  const value = npc.data.current_visual_state ?? npc.data.visual_state;
  return typeof value === "string" ? value : null;
}

function relationshipForPair(npc: EntityDocument, player: EntityDocument | null, relations: EntityDocument[], people: EntityDocument[]) {
  if (!player) return null;
  const playerName = normalize(entityName(player, ""));
  const npcName = normalize(entityName(npc, ""));
  return relations.find((relation) => {
    const participants = participantsFor(relation, people);
    if (participants.some((row) => row.id === npc.id) && participants.some((row) => row.id === player.id)) return true;
    const haystack = relationSearchText(relation);
    return Boolean(playerName && npcName && haystack.includes(playerName) && haystack.includes(npcName));
  }) ?? null;
}

function relationTitle(relation: EntityDocument, participants: EntityDocument[]) {
  const explicit = text(relation.data.name ?? relation.data.title ?? relation.data.label, "");
  if (participants.length >= 2) return participants.map((row) => entityName(row)).join(" ↔ ");
  return explicit || "Lien connu";
}

export function RelationsNetworkView({ entities }: { entities: EntityDocument[] }) {
  const [all, setAll] = useState<EntityDocument[]>(entities);

  useEffect(() => {
    let cancelled = false;
    setAll(entities);
    (async () => {
      const campaignId = await selectedCampaignId();
      if (!campaignId) return;
      const rows = await backend.listEntities(campaignId, false);
      if (!cancelled) setAll(rows);
    })().catch(() => undefined);
    return () => { cancelled = true; };
  }, [entities]);

  const player = all.find((row) => row.entity_type === "player_character") ?? null;
  const npcs = all.filter((row) => row.entity_type === "npc");
  const relations = all.filter((row) => row.entity_type === "relationship");
  const reps = all.filter((row) => row.entity_type === "reputation");
  const people = useMemo(() => [...(player ? [player] : []), ...npcs], [player, npcs]);
  const playerName = player ? entityName(player, "le personnage") : "le personnage";

  return <div className="relations-layout relations-network-layout">
    <section className="panel full-span">
      <h2>Personnes connues</h2>
      <p className="muted">Le rôle connu par rapport à {playerName} et les liens importants avec d'autres personnes sont affichés directement sur chaque fiche.</p>
      {npcs.length === 0 ? <div className="empty-inline">Personne enregistrée.</div> : <div className="npc-grid">{npcs.map((npc) => {
        const name = entityName(npc);
        const role = roleForNpc(npc, relations, people, player);
        const playerRelation = relationshipForPair(npc, player, relations, people);
        const summary = short(npc.data.known_summary ?? npc.data.description ?? npc.data.player_impression ?? npc.data.known_information, "Aucune description connue.");
        const meta = [role, text(npc.data.species), text(npc.data.profession)].filter(Boolean).join(" · ");
        const npcLinks = relations.map((relation) => ({ relation, participants: participantsFor(relation, people) })).filter(({ participants }) => participants.some((row) => row.id === npc.id) && participants.some((row) => row.id !== npc.id && row.id !== player?.id)).slice(0, 4);
        return <article className="npc-card npc-network-card" key={npc.id}>
          <NpcPortraitControl subjectEntityId={npc.id} name={name} currentState={visualState(npc)} />
          <div className="npc-card-body">
            <strong className="npc-name">{name}</strong>
            <span className={role ? "npc-role known" : "npc-role"}>{meta || "Rôle non précisé"}</span>
            <p>{summary}</p>
            {playerRelation && <div className="npc-player-link"><b>Lien avec {playerName}</b><span>{short(relationNarrative(playerRelation) || relationType(playerRelation), role || "Lien connu", 150)}</span></div>}
            {npcLinks.length > 0 && <div className="npc-known-links"><b>Liens connus</b><div>{npcLinks.map(({ relation, participants }) => {
              const others = participants.filter((row) => row.id !== npc.id).map((row) => entityName(row)).join(", ");
              return <span className="relation-chip" key={relation.id}>{others || relationTitle(relation, participants)}{relationType(relation) ? ` · ${relationType(relation)}` : ""}</span>;
            })}</div></div>}
          </div>
        </article>;
      })}</div>}
    </section>

    <section className="panel full-span relation-network-panel">
      <h2>Famille & liens connus</h2>
      <p className="muted">Ce réseau reprend uniquement les relations réellement présentes dans les données joueur ; il n'invente aucun lien manquant.</p>
      {relations.length === 0 ? <div className="empty-inline">Aucun lien explicite enregistré.</div> : <div className="relation-network-list">{relations.map((relation) => {
        const participants = participantsFor(relation, people);
        const type = relationType(relation);
        const description = relationNarrative(relation);
        return <article key={relation.id}>
          <div><strong>{relationTitle(relation, participants)}</strong>{type && <span>{type}</span>}</div>
          {description && <p>{short(description, "", 220)}</p>}
        </article>;
      })}</div>}
    </section>

    {reps.length > 0 && <section className="panel full-span"><h2>Réputation</h2><div className="relation-network-list">{reps.map((rep) => <article key={rep.id}><div><strong>{entityName(rep, "Réputation")}</strong></div><p>{short(rep.data.description ?? rep.data.status ?? rep.data.value, "—", 190)}</p></article>)}</div></section>}
  </div>;
}
