from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_approximate_locations_render_as_uncertainty_areas():
    component = source("src/components/InteractiveMap.tsx")

    assert "function isApproximate" in component
    assert "uncertainty_radius_x" in component
    assert "uncertainty_radius_y" in component
    assert "ctx.ellipse" in component
    assert "setLineDash" in component


def test_route_distance_is_displayed_only_from_explicit_distance_km():
    component = source("src/components/InteractiveMap.tsx")
    contract = source("docs/MAP_DATA_CONTRACT_MVP.md")

    assert 'numberField(selected.data, "distance_km")' in component
    assert "Distance de route" in component
    assert "ne représentent jamais automatiquement une distance" in contract
    assert "distance_km" in contract
    assert "refuse une route sans distance explicite" in contract


def test_successful_update_reloads_campaign_entities_used_by_atlas():
    app = source("src/App.tsx")

    assert "const result = await backend.importUpdate(jsonText);" in app
    assert "await refreshCampaigns();" in app
    assert "refreshCampaignData(campaign.id)" in app
    assert "[campaign?.id, campaign?.current_revision]" in app
    assert "setEntities(player);" in app
    assert "const currentLocation = entities.find((e) => e.entity_type === \"current_location\")?.data;" in app
    assert "const mapEntities = entities.filter" in app
    assert "<InteractiveMap imageUrl={worldMapUrl" in app
    assert "entities={mapEntities}" in app


def test_map_wheel_is_consumed_by_map_and_does_not_scroll_page():
    component = source("src/components/InteractiveMap.tsx")
    css = source("src/interactive-map-mvp.css")

    assert 'viewport.addEventListener("wheel", onWheel, { passive: false })' in component
    assert "event.preventDefault();" in component
    assert "event.stopPropagation();" in component
    assert "overscroll-behavior:contain" in css


def test_overlapping_locations_spiderfy_into_individually_clickable_markers():
    component = source("src/components/InteractiveMap.tsx")
    css = source("src/interactive-map-mvp.css")

    assert "spiderClusterId" in component
    assert "openCluster(cluster)" in component
    assert "SPIDER_RADIUS_PX" in component
    assert "spiderItems.map" in component
    assert "interactive-map-spider-marker" in component
    assert "Lieux à cet endroit" in component
    assert ".map-spider-lines" in css
    assert ".interactive-map-spider-marker" in css


def test_map_uses_dpr_canvas_and_caps_zoom_at_native_source_resolution():
    component = source("src/components/InteractiveMap.tsx")
    css = source("src/interactive-map-mvp.css")

    assert "devicePixelRatio" in component
    assert "canvas.width = Math.round(g.viewportWidth * dpr)" in component
    assert "ctx.drawImage(image" in component
    assert "maxScale: 1" in component
    assert "100% natif" in component
    assert "100% = pixels natifs" in component
    assert "interactive-map-raster-canvas" in component
    assert "DPR-aware canvas" in css
    assert "no automatic enlargement beyond native resolution" in css


def test_cluster_distance_is_screen_pixel_based_so_exact_and_near_overlaps_share_one_target():
    component = source("src/components/InteractiveMap.tsx")

    assert "CLUSTER_RADIUS_PX" in component
    assert "Math.hypot(cluster.sx - marker.sx, cluster.sy - marker.sy) <= CLUSTER_RADIUS_PX" in component
    assert "clusterMarkers(screenMarkers)" in component
