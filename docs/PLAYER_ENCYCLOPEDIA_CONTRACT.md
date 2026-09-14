# Kitaba — Encyclopédie / Codex du joueur

Status: **accepted 0.1.6 MVP addition**. This feature is a player-facing projection of existing canonical entities; it does not add a second persistence authority or a new SQLite migration.

## Purpose

The Encyclopedia gives the player a readable, book-like memory of what their protagonist has genuinely learned during the campaign. It complements the journal, map and relationship views by organizing durable knowledge into a single browsable reference.

The intended feeling is a personal campaign codex that grows with discovery, not a developer database browser.

## Authority rule

The Encyclopedia never creates canon by itself.

- It reads PLAYER-visible entities only.
- GM-only entities are never queried for the Codex surface.
- Rumors, beliefs and uncertain knowledge remain marked as uncertain.
- Updating an existing known subject should enrich/correct the same canonical entity rather than create encyclopedia-specific duplicate truth.
- Missing information stays missing rather than being filled from hidden GM knowledge.
- Encyclopedia entries survive because their underlying canonical entities survive; the view itself requires no new schema.

## Categories

The 0.1.6 surface groups discoveries into:

1. **Colonies & lieux** — settlements, places, regions, routes, dungeons and known landmarks.
2. **Figures & relations** — named or persistently relevant NPCs, heroes, rulers, mentors and rivals.
3. **Relations & lignées** — relationships, kinship, houses, clans, lineages and dynasties known to the player.
4. **Bestiaire & troupes** — creatures, monsters, species, troops and recurring enemy/unit types; discovered strengths, weaknesses, habitat and behavior remain ordinary canonical data fields and are shown only when actually known.
5. **Royaumes & factions** — states, kingdoms, factions, guilds, organizations and political powers.
6. **Concepts & savoirs** — knowledge, rumors, beliefs, religions, languages, customs, laws and world concepts.
7. **Monde & histoire** — historical/world events, conflicts, economy, environment, resources, peoples and culture.
8. **Autres découvertes** — explicit encyclopedia entries or other durable PLAYER knowledge that does not fit a primary category.

## NPC inclusion policy

The Codex should not fill itself with anonymous passers-by.

Persist an NPC entry when at least one of these is true:

- the NPC is named and likely to recur;
- a relationship, family link, debt, favor, rivalry, mission or meaningful consequence connects them to the protagonist;
- the NPC is socially/world-relevant enough that remembering them later has value;
- the player explicitly investigates or asks to remember them.

Minor persistent NPCs may have short entries. Important figures may accumulate richer descriptions, known history, relationships and visual references without changing identity.

## Data-shaping guidance for KITABA_UPDATE

Existing entity types are preferred. Optional fields can improve rendering without changing the schema:

- `encyclopedia_category`: explicit category override when the entity type is ambiguous;
- `encyclopedia_include: true`: include an otherwise uncategorized player-visible entity;
- `known_summary` / `summary` / `description`: readable synopsis;
- `epistemic_status` / `knowledge_status` / `certainty`: explicit fact/rumor/belief/partial-confidence cue;
- ordinary domain fields such as `known_strengths`, `known_weaknesses`, `habitat`, `affiliation`, `family`, `role`, `territory`, `customs`, etc. remain ordinary canonical data and must never be populated with unknown GM truth merely for presentation.

The view deliberately renders generic known fields rather than hard-coding a closed bestiary/world schema.

## Relationship and family-tree direction

0.1.6 provides a dedicated **Relations & lignées** category from known relationship/kinship entities. A later visual family/relationship graph can be built on those stable identities and links without rewriting the Codex or campaign data.

## Search and visuals

The Encyclopedia has its own category navigation and search. Where a known subject already has an allowed persistent visual reference, the entry may display that reference. The canon-before-image and PLAYER/GM boundaries remain unchanged.

## API future

In the future in-app narrative runtime:

1. the narrative authority proposes discoveries/updated knowledge;
2. the canonical update gate validates PLAYER/GM visibility, revision and timeline;
3. accepted PLAYER mutations persist in the existing entity model;
4. the Encyclopedia refreshes from those entities automatically.

The API therefore does not write a separate encyclopedia database.

## 0.1.6 implementation choice

To avoid destabilizing release compatibility, the first Encyclopedia integration is route-neutral: it adds a normal-flow sidebar entry and mounts a dedicated page over the existing player surface without changing the SQLite schema or the central App routing union. It fetches `listEntities(campaign_id, false)` only.

This keeps the feature independently removable/refactorable while the 0.1.6 compatibility gates remain focused on the existing 0.1.5 save model.
