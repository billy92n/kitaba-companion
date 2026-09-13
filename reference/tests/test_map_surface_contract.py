from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_approximate_locations_render_as_uncertainty_areas():
    component = source("src/components/InteractiveMap.tsx")
    css = source("src/interactive-map-mvp.css")

    assert "function isApproximate" in component
    assert "uncertainty_radius_x" in component
    assert "uncertainty_radius_y" in component
    assert "<ellipse" in component
    assert "map-uncertainty-area" in component
    assert ".map-uncertainty-area" in css


def test_route_distance_is_displayed_only_from_explicit_distance_km():
    component = source("src/components/InteractiveMap.tsx")
    contract = source("docs/MAP_DATA_CONTRACT_MVP.md")

    assert 'numberField(selected.data, "distance_km")' in component
    assert "Distance de route" in component
    assert "ne représentent jamais automatiquement une distance" in contract
    assert "distance_km" in contract
    assert "refuse une route sans distance explicite" in contract
