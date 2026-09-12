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

const nav: Array<[SectionKey, string]> = [
  ["overview", "Vue d'ensemble"],
  ["character", "Personnage"],
  ["skills", "Compétences"],
  ["magic", "Magie"],
  ["inventory", "Inventaire"],
  ["relations", "Relations"],
  ["journal", "Journal"],
  ["missions", "Missions"],
  ["knowledge", "Connaissances"],
  ["world", "Monde"],
  ["media", "Médiathèque"],
  ["map", "Carte"],
  ["timeline", "Chronologie"],
  ["adventurer_card", "Carte d'aventurier"],
  ["checkpoints", "Checkpoints"],
  ["sync", "Synchronisation"],
];

const preCreationNav: Array<[SectionKey, string]> = [
  ["overview", "Vue d'ensemble"],
  ["sync", "Synchronisation"],
];

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
  const navigation = pcEntity ? nav : preCreationNav;

  return (
    <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`} aria-label="Navigation de campagne">
      <div className="brand">KITABA</div>
      {portraitUrl ? <img className="portrait-image" src={portraitUrl} alt={firstName ? `Portrait de ${firstName}` : "Portrait du personnage"} /> : <div className="portrait-placeholder">{portraitInitial}</div>}
      <div className="identity">
        <strong>{displayName}</strong>
        <span>{species !== null || age !== null ? `${species ?? "Espèce non renseignée"}${age !== null ? ` • ${age} ans` : ""}` : "Personnage non initialisé"}</span>
      </div>
      {rank !== null && <div className="sidebar-stat"><span>Rang</span><strong>{rank}</strong></div>}
      {(hpCurrent !== null || hpMax !== null) && <div className="sidebar-stat"><span>HP</span><strong>{hpCurrent ?? "—"}{hpMax !== null ? ` / ${hpMax}` : ""}</strong></div>}
      {(manaCurrent !== null || manaMax !== null) && <div className="sidebar-stat"><span>Mana</span><strong>{manaCurrent ?? "—"}{manaMax !== null ? ` / ${manaMax}` : ""}</strong></div>}
      <div className="sidebar-stat"><span>Révision</span><strong>{campaign?.current_revision ?? "—"}</strong></div>
      <div className="sidebar-stat"><span>Temps en jeu</span><strong>{campaign?.game_time ?? "—"}</strong></div>
      <nav>
        {navigation.map(([key, label]) => (
          <button key={key} className={`nav-item ${active === key ? "active" : ""}`} onClick={() => { onNavigate(key); onCloseMobile?.(); }}>
            {label}
          </button>
        ))}
      </nav>
      {pcEntity && <button className={`gm-entry ${active === "gm_vault" ? "active" : ""}`} onClick={() => { onNavigate("gm_vault"); onCloseMobile?.(); }}>Coffre MJ</button>}
    </aside>
  );
}
