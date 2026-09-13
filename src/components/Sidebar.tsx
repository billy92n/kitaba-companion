import type { CampaignSummary, EntityDocument, SectionKey } from "../lib/types";

type Props = {
  campaign: CampaignSummary | null;
  entities: EntityDocument[];
  active: SectionKey;
  onNavigate: (section: SectionKey) => void;
  portraitUrl?: string | null;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
};

type NavItem = [SectionKey, string, "play" | "memory" | "manage"];

const nav: NavItem[] = [
  ["overview", "Accueil", "play"],
  ["character", "Personnage", "play"],
  ["inventory", "Inventaire", "play"],
  ["skills", "Compétences", "play"],
  ["magic", "Magie", "play"],
  ["relations", "Relations", "memory"],
  ["journal", "Journal", "memory"],
  ["missions", "Missions", "memory"],
  ["map", "Carte", "memory"],
  ["media", "Portraits & images", "manage"],
  ["sync", "Mettre à jour la partie", "manage"],
];

const preCreationNav: NavItem[] = [
  ["overview", "Accueil", "play"],
  ["sync", "Mettre à jour la partie", "manage"],
];

const discoveryTypes: Partial<Record<SectionKey, string[]>> = {
  skills: ["skill", "mastery", "characteristic", "specialized_stat"],
  magic: ["magic", "spell", "affinity", "invocation", "contract", "enchantment", "known_aptitude"],
  missions: ["mission", "quest"],
  map: ["place", "map_marker", "map", "current_location", "settlement", "state", "region", "route", "dungeon"],
};

const groupLabels = {
  play: "Jouer",
  memory: "Mémoire",
  manage: "Gestion",
} as const;

function text(data: Record<string, unknown>, ...keys: string[]) {
  for (const key of keys) {
    const value = data[key];
    if (typeof value === "string" || typeof value === "number") return String(value);
  }
  return null;
}

export function Sidebar({ campaign, entities, active, onNavigate, portraitUrl, mobileOpen = false, onCloseMobile }: Props) {
  const pcEntity = entities.find((e) => e.entity_type === "player_character");
  const pc = pcEntity?.data ?? {};
  const firstName = text(pc, "first_name", "prenom", "name");
  const displayName = firstName ?? (campaign ? "Personnage à créer" : "—");
  const portraitInitial = firstName ? firstName.slice(0, 1).toUpperCase() : "?";
  const species = text(pc, "species", "espece");
  const age = text(pc, "age");
  const rank = text(pc, "official_rank", "rank");
  const hpCurrent = text(pc, "hp_current", "hp");
  const hpMax = text(pc, "hp_max");
  const manaCurrent = text(pc, "mana_current", "mana");
  const manaMax = text(pc, "mana_max");
  const entityTypes = new Set(entities.map((entity) => entity.entity_type));
  const navigation = pcEntity ? nav.filter(([key]) => {
    const required = discoveryTypes[key];
    if (!required) return true;
    if (key === "magic" && (manaCurrent !== null || manaMax !== null)) return true;
    return required.some((type) => entityTypes.has(type));
  }) : preCreationNav;

  const groups = (["play", "memory", "manage"] as const)
    .map((group) => ({ group, items: navigation.filter(([, , itemGroup]) => itemGroup === group) }))
    .filter(({ items }) => items.length > 0);

  return (
    <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`} aria-label="Navigation de campagne">
      <div className="brand">KITABA</div>
      {portraitUrl ? <img className="portrait-image" src={portraitUrl} alt={firstName ? `Portrait de ${firstName}` : "Portrait du personnage"} /> : <div className="portrait-placeholder">{portraitInitial}</div>}
      <div className="identity">
        <strong>{displayName}</strong>
        <span>{species !== null || age !== null ? `${species ?? "Espèce non renseignée"}${age !== null ? ` • ${age} ans` : ""}` : "Personnage non initialisé"}</span>
      </div>
      {rank !== null && <div className="sidebar-stat"><span>Rang</span><strong>{rank}</strong></div>}
      {(hpCurrent !== null || hpMax !== null) && <div className="sidebar-stat"><span>PV</span><strong>{hpCurrent ?? "—"}{hpMax !== null ? ` / ${hpMax}` : ""}</strong></div>}
      {(manaCurrent !== null || manaMax !== null) && <div className="sidebar-stat"><span>Mana</span><strong>{manaCurrent ?? "—"}{manaMax !== null ? ` / ${manaMax}` : ""}</strong></div>}
      <div className="sidebar-stat"><span>Révision</span><strong>{campaign?.current_revision ?? "—"}</strong></div>
      <div className="sidebar-stat"><span>Temps en jeu</span><strong>{campaign?.game_time ?? "—"}</strong></div>
      <nav>
        {groups.map(({ group, items }) => <div className="nav-group" key={group}>
          <div className="nav-group-title">{groupLabels[group]}</div>
          {items.map(([key, label]) => (
            <button key={key} className={`nav-item ${active === key ? "active" : ""}`} onClick={() => { onNavigate(key); onCloseMobile?.(); }}>
              {label}
            </button>
          ))}
        </div>)}
      </nav>
      {pcEntity && <button className={`gm-entry ${active === "gm_vault" ? "active" : ""}`} onClick={() => { onNavigate("gm_vault"); onCloseMobile?.(); }}>Coffre MJ</button>}
    </aside>
  );
}
