from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_relations_surface_resolves_roles_from_player_visible_relationship_entities():
    view = source("src/components/RelationsNetworkView.tsx")

    assert "roleForNpc" in view
    assert "participantsFor" in view
    assert "kinshipRoleFromText" in view
    assert "relation_to_player" in view
    assert "Frère de ${playerName}" in view
    assert "Sœur de ${playerName}" in view
    assert "Mère de ${playerName}" in view
    assert "Père de ${playerName}" in view


def test_relations_surface_replaces_vague_perceived_list_with_named_network():
    view = source("src/components/RelationsNetworkView.tsx")
    rpg = source("src/components/RpgViews.tsx")

    assert "Famille & liens connus" in view
    assert "Liens connus" in view
    assert "Lien avec {playerName}" in view
    assert "Relations perçues" not in view
    assert "Relations perçues" not in rpg
    assert "RelationsNetworkView" in rpg


def test_relations_network_never_invents_links_when_player_data_does_not_support_them():
    view = source("src/components/RelationsNetworkView.tsx")

    assert "Ce réseau reprend uniquement les relations réellement présentes dans les données joueur" in view
    assert "Rôle non précisé" in view
    assert "relations.filter" in view or "const relations = all.filter" in view


def test_npc_cards_can_surface_known_npc_to_npc_links():
    view = source("src/components/RelationsNetworkView.tsx")

    assert "npcLinks" in view
    assert "participants.some((row) => row.id !== npc.id && row.id !== player?.id)" in view
    assert "relation-chip" in view
