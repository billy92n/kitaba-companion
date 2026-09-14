from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_generic_entity_cards_translate_field_names_and_values():
    entity_list = read("src/components/EntityList.tsx")
    french = read("src/lib/frenchUi.ts")
    assert "fieldLabelFr(key)" in entity_list
    assert "valueFr(value)" in entity_list or "valueToText(value)" in entity_list
    for key, label in [("name", "Nom"), ("severity", "Gravité"), ("status", "Statut"), ("description", "Description")]:
        assert f'{key}: "{label}"' in french


def test_rpg_and_progression_views_localize_enum_values():
    rpg = read("src/components/RpgViews.tsx")
    progression = read("src/components/ProgressionViews.tsx")
    assert 'import { valueFr } from "../lib/frenchUi"' in rpg
    assert 'import { valueFr } from "../lib/frenchUi"' in progression
    assert "valueFr(value)" in rpg
    assert "valueFr(value)" in progression


def test_map_does_not_surface_raw_entity_types_and_localizes_displayed_values():
    component = read("src/components/InteractiveMap.tsx")
    assert 'import { entityTypeLabelFr, valueFr } from "../lib/frenchUi"' in component
    assert "entityTypeLabelFr(marker.entity.entity_type)" in component
    assert "entityTypeLabelFr(selected.entity_type)" in component
    assert "valueFr(routeDistance)" in component


def test_french_dictionary_covers_common_player_facing_enums():
    french = read("src/lib/frenchUi.ts")
    for english, french_label in [
        ("wounded", "Blessé"),
        ("sick", "Malade"),
        ("dead", "Mort"),
        ("completed", "Terminée"),
        ("pending", "En attente"),
        ("friendly", "Amical"),
        ("hostile", "Hostile"),
    ]:
        assert f'{english}: "{french_label}"' in french
