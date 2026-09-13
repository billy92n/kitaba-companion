import { useEffect, useMemo, useRef, useState } from "react";
import type { EntityDocument } from "../lib/types";
import { entityTypeLabelFr, valueFr } from "../lib/frenchUi";
import "../interactive-map-mvp.css";

type Props = {
  imageUrl: string;
  entities: EntityDocument[];
};

type Pan = { x: number; y: number };
type WorldGeometry = {
  viewportWidth: number;
  viewportHeight: number;
  fittedWidth: number;
  fittedHeight: number;
  offsetX: number;
  offsetY: number;
  minimumZoom: number;
};
type LayerKey = "settlements" | "political" | "routes" | "dungeons" | "other";
type PositionedMarker = { entity: EntityDocument; x: number; y: number; current: boolean; priority: number; layer: LayerKey };
type MarkerCluster = { id: string; x: number; y: number; markers: PositionedMarker[] };
type NormalizedPoint = { x: number; y: number };
type VectorFeature = { entity: EntityDocument; layer: "political" | "routes"; points: NormalizedPoint[]; closed: boolean };

const MAX_ZOOM = 12;
const LAYERS: Array<{ key: LayerKey; label: string }> = [
  { key: "settlements", label: "Lieux" },
  { key: "political", label: "Régions" },
  { key: "routes", label: "Routes" },
  { key: "dungeons", label: "Donjons" },
  { key: "other", label: "Autres" },
];

function numberField(data: Record<string, unknown>, ...keys: string[]) {
  for (const key of keys) {
    const value = Number(data[key]);
    if (Number.isFinite(value)) return value;
  }
  return null;
}

function stringField(data: Record<string, unknown>, ...keys: string[]) {
  for (const key of keys) {
    const value = data[key];
    if (typeof value === "string" && value.trim()) return value.trim();
    if (typeof value === "number") return String(value);
  }
  return null;
}

function markerLabel(entity: EntityDocument) {
  return stringField(entity.data, "name", "label", "known_name", "title") ?? (entity.entity_type === "current_location" ? "Position actuelle" : "Lieu connu");
}

function markerLayer(entity: EntityDocument): LayerKey {
  if (["state", "region"].includes(entity.entity_type)) return "political";
  if (entity.entity_type === "route") return "routes";
  if (entity.entity_type === "dungeon") return "dungeons";
  if (["settlement", "place", "current_location", "map_marker"].includes(entity.entity_type)) return "settlements";
  return "other";
}

function markerPriority(entity: EntityDocument, current: boolean) {
  if (current) return 100;
  const explicit = numberField(entity.data, "map_importance", "importance", "priority");
  if (explicit !== null) return Math.max(0, Math.min(100, explicit));
  if (entity.entity_type === "state") return 90;
  if (entity.entity_type === "region") return 80;
  if (entity.entity_type === "settlement") return 68;
  if (entity.entity_type === "dungeon") return 55;
  if (["place", "map_marker"].includes(entity.entity_type)) return 48;
  if (entity.entity_type === "route") return 35;
  return 40;
}

function visibleAtZoom(marker: PositionedMarker, zoom: number) {
  if (marker.current || marker.priority >= 80) return true;
  if (marker.priority >= 65) return zoom >= 1.15;
  if (marker.priority >= 50) return zoom >= 1.55;
  if (marker.priority >= 40) return zoom >= 1.85;
  return zoom >= 2.2;
}

function isApproximate(entity: EntityDocument) {
  const precision = (stringField(entity.data, "location_precision", "map_precision") ?? "exact").toLocaleLowerCase("fr");
  return precision.includes("approx");
}

function uncertaintyRadius(entity: EntityDocument, axis: "x" | "y") {
  const specific = axis === "x"
    ? numberField(entity.data, "uncertainty_radius_x", "map_uncertainty_x")
    : numberField(entity.data, "uncertainty_radius_y", "map_uncertainty_y");
  const shared = numberField(entity.data, "uncertainty_radius", "map_uncertainty_radius");
  const fallback = axis === "x" ? 0.035 : 0.025;
  return Math.max(0.005, Math.min(0.25, specific ?? shared ?? fallback));
}

function parseNormalizedPoints(value: unknown): NormalizedPoint[] {
  if (!Array.isArray(value)) return [];
  const points: NormalizedPoint[] = [];
  for (const row of value) {
    let x: number | null = null;
    let y: number | null = null;
    if (Array.isArray(row) && row.length >= 2) {
      const maybeX = Number(row[0]);
      const maybeY = Number(row[1]);
      if (Number.isFinite(maybeX) && Number.isFinite(maybeY)) { x = maybeX; y = maybeY; }
    } else if (row && typeof row === "object") {
      const record = row as Record<string, unknown>;
      const maybeX = Number(record.x ?? record.map_x);
      const maybeY = Number(record.y ?? record.map_y);
      if (Number.isFinite(maybeX) && Number.isFinite(maybeY)) { x = maybeX; y = maybeY; }
    }
    if (x !== null && y !== null && x >= 0 && x <= 1 && y >= 0 && y <= 1) points.push({ x, y });
  }
  return points;
}

function vectorFeature(entity: EntityDocument): VectorFeature | null {
  const data = entity.data;
  if (entity.entity_type === "route") {
    const points = parseNormalizedPoints(data.path ?? data.points ?? data.map_path);
    return points.length >= 2 ? { entity, layer: "routes", points, closed: false } : null;
  }
  if (["region", "state"].includes(entity.entity_type)) {
    const points = parseNormalizedPoints(data.polygon ?? data.boundary ?? data.map_polygon);
    return points.length >= 3 ? { entity, layer: "political", points, closed: true } : null;
  }
  return null;
}

function measureWorld(viewport: HTMLDivElement | null, image: HTMLImageElement | null): WorldGeometry | null {
  if (!viewport) return null;
  const { width, height } = viewport.getBoundingClientRect();
  if (width <= 0 || height <= 0) return null;

  const naturalAspect = image?.naturalWidth && image?.naturalHeight ? image.naturalWidth / image.naturalHeight : 2;
  const viewportAspect = width / height;
  const fittedWidth = viewportAspect > naturalAspect ? height * naturalAspect : width;
  const fittedHeight = viewportAspect > naturalAspect ? height : width / naturalAspect;
  const offsetX = (width - fittedWidth) / 2;
  const offsetY = (height - fittedHeight) / 2;
  const minimumZoom = Math.max(1, width / fittedWidth, height / fittedHeight);

  return { viewportWidth: width, viewportHeight: height, fittedWidth, fittedHeight, offsetX, offsetY, minimumZoom };
}

function clampPanToWorld(next: Pan, zoom: number, geometry: WorldGeometry | null): Pan {
  if (!geometry) return next;
  const effectiveZoom = Math.max(zoom, geometry.minimumZoom);
  const maxX = Math.max(0, (geometry.fittedWidth * effectiveZoom - geometry.viewportWidth) / 2);
  const maxY = Math.max(0, (geometry.fittedHeight * effectiveZoom - geometry.viewportHeight) / 2);
  return {
    x: Math.max(-maxX, Math.min(maxX, next.x)),
    y: Math.max(-maxY, Math.min(maxY, next.y)),
  };
}

function clusterMarkers(markers: PositionedMarker[], zoom: number): MarkerCluster[] {
  const radius = 0.07 / Math.max(1, zoom);
  const clusters: MarkerCluster[] = [];
  const sorted = [...markers].sort((a, b) => b.priority - a.priority);

  for (const marker of sorted) {
    const target = clusters.find((cluster) => {
      const dx = (cluster.x - marker.x) * 2;
      const dy = cluster.y - marker.y;
      return Math.hypot(dx, dy) <= radius;
    });
    if (!target) {
      clusters.push({ id: marker.entity.id, x: marker.x, y: marker.y, markers: [marker] });
      continue;
    }
    target.markers.push(marker);
    target.x = target.markers.reduce((sum, row) => sum + row.x, 0) / target.markers.length;
    target.y = target.markers.reduce((sum, row) => sum + row.y, 0) / target.markers.length;
    target.id = target.markers.map((row) => row.entity.id).sort().join(":");
  }
  return clusters;
}

function worldRect(geometry: WorldGeometry | null, zoom: number, pan: Pan) {
  if (!geometry) return null;
  const width = geometry.fittedWidth * zoom;
  const height = geometry.fittedHeight * zoom;
  return {
    width,
    height,
    left: (geometry.viewportWidth - width) / 2 + pan.x,
    top: (geometry.viewportHeight - height) / 2 + pan.y,
  };
}

export function InteractiveMap({ imageUrl, entities }: Props) {
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const dragRef = useRef<{ pointerId: number; startX: number; startY: number; origin: Pan } | null>(null);
  const zoomRef = useRef(1);
  const panRef = useRef<Pan>({ x: 0, y: 0 });
  const geometryRef = useRef<WorldGeometry | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<Pan>({ x: 0, y: 0 });
  const [geometry, setGeometry] = useState<WorldGeometry | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({ settlements: true, political: true, routes: true, dungeons: true, other: true });

  useEffect(() => { zoomRef.current = zoom; }, [zoom]);
  useEffect(() => { panRef.current = pan; }, [pan]);
  useEffect(() => { geometryRef.current = geometry; }, [geometry]);

  const rawMarkers = useMemo(() => entities.filter((entity) => {
    const x = numberField(entity.data, "x", "map_x");
    const y = numberField(entity.data, "y", "map_y");
    return x !== null && y !== null && x >= 0 && x <= 1 && y >= 0 && y <= 1;
  }), [entities]);

  const vectors = useMemo(() => entities.map(vectorFeature).filter((feature): feature is VectorFeature => feature !== null), [entities]);
  const unpositionedCount = useMemo(() => entities.filter((entity) => {
    const canBeMapped = ["settlement", "place", "map_marker", "current_location", "state", "region", "route", "dungeon"].includes(entity.entity_type);
    if (!canBeMapped) return false;
    if (rawMarkers.some((marker) => marker.id === entity.id)) return false;
    if (vectors.some((feature) => feature.entity.id === entity.id)) return false;
    return true;
  }).length, [entities, rawMarkers, vectors]);

  const currentLocation = useMemo(() => entities.find((entity) => entity.entity_type === "current_location") ?? null, [entities]);
  const currentLinkedIds = useMemo(() => new Set([
    stringField(currentLocation?.data ?? {}, "place_id"),
    stringField(currentLocation?.data ?? {}, "settlement_id"),
    stringField(currentLocation?.data ?? {}, "map_marker_id"),
  ].filter((value): value is string => Boolean(value))), [currentLocation]);

  const markers = useMemo<PositionedMarker[]>(() => rawMarkers.map((entity) => {
    const current = entity.entity_type === "current_location" || entity.data.current === true || currentLinkedIds.has(entity.id);
    return {
      entity,
      x: numberField(entity.data, "x", "map_x") ?? 0,
      y: numberField(entity.data, "y", "map_y") ?? 0,
      current,
      priority: markerPriority(entity, current),
      layer: markerLayer(entity),
    };
  }), [rawMarkers, currentLinkedIds]);

  const currentMarker = useMemo(() => markers.find((marker) => marker.current) ?? null, [markers]);
  const selected = markers.find((marker) => marker.entity.id === selectedId)?.entity ?? null;
  const filteredMarkers = useMemo(() => markers.filter((marker) => layers[marker.layer] && visibleAtZoom(marker, zoom)), [markers, layers, zoom]);
  const clusters = useMemo(() => clusterMarkers(filteredMarkers, zoom), [filteredMarkers, zoom]);
  const selectedCluster = selectedClusterId ? clusters.find((cluster) => cluster.id === selectedClusterId) ?? null : null;
  const uncertaintyMarkers = useMemo(() => markers.filter((marker) => layers[marker.layer] && visibleAtZoom(marker, zoom) && isApproximate(marker.entity)), [markers, layers, zoom]);

  const searchResults = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("fr");
    if (!normalized) return [];
    return markers.filter((marker) => {
      const haystack = `${markerLabel(marker.entity)} ${entityTypeLabelFr(marker.entity.entity_type)} ${stringField(marker.entity.data, "region", "realm", "kingdom", "summary", "description") ?? ""}`.toLocaleLowerCase("fr");
      return haystack.includes(normalized);
    }).slice(0, 8);
  }, [markers, query]);

  const layerCounts = useMemo(() => {
    const ids: Record<LayerKey, Set<string>> = {
      settlements: new Set(), political: new Set(), routes: new Set(), dungeons: new Set(), other: new Set(),
    };
    for (const marker of markers) ids[marker.layer].add(marker.entity.id);
    for (const feature of vectors) ids[feature.layer].add(feature.entity.id);
    return {
      settlements: ids.settlements.size,
      political: ids.political.size,
      routes: ids.routes.size,
      dungeons: ids.dungeons.size,
      other: ids.other.size,
    };
  }, [markers, vectors]);

  const rendered = worldRect(geometry, zoom, pan);

  function applyView(nextZoom: number, nextPan: Pan, nextGeometry: WorldGeometry | null) {
    const clampedZoom = nextGeometry ? Math.max(nextGeometry.minimumZoom, Math.min(MAX_ZOOM, nextZoom)) : Math.max(1, Math.min(MAX_ZOOM, nextZoom));
    const clampedPan = clampPanToWorld(nextPan, clampedZoom, nextGeometry);
    zoomRef.current = clampedZoom;
    panRef.current = clampedPan;
    setZoom(clampedZoom);
    setPan(clampedPan);
  }

  function synchronizeGeometry() {
    const nextGeometry = measureWorld(viewportRef.current, imageRef.current);
    if (!nextGeometry) return;
    geometryRef.current = nextGeometry;
    setGeometry(nextGeometry);
    applyView(zoomRef.current, panRef.current, nextGeometry);
  }

  function setZoomAt(next: number, anchorClientX?: number, anchorClientY?: number) {
    const viewport = viewportRef.current;
    const latestGeometry = measureWorld(viewport, imageRef.current) ?? geometryRef.current;
    if (!latestGeometry || !viewport) return;
    const currentZoom = Math.max(latestGeometry.minimumZoom, zoomRef.current);
    const nextZoom = Math.max(latestGeometry.minimumZoom, Math.min(MAX_ZOOM, Number(next.toFixed(3))));
    if (Math.abs(nextZoom - currentZoom) < 0.0001) return;

    const rect = viewport.getBoundingClientRect();
    const anchorX = anchorClientX == null ? latestGeometry.viewportWidth / 2 : anchorClientX - rect.left;
    const anchorY = anchorClientY == null ? latestGeometry.viewportHeight / 2 : anchorClientY - rect.top;
    const before = worldRect(latestGeometry, currentZoom, panRef.current);
    if (!before) return;
    const normalizedX = Math.max(0, Math.min(1, (anchorX - before.left) / before.width));
    const normalizedY = Math.max(0, Math.min(1, (anchorY - before.top) / before.height));
    const nextWidth = latestGeometry.fittedWidth * nextZoom;
    const nextHeight = latestGeometry.fittedHeight * nextZoom;
    const centeredLeft = (latestGeometry.viewportWidth - nextWidth) / 2;
    const centeredTop = (latestGeometry.viewportHeight - nextHeight) / 2;
    const nextPan = {
      x: anchorX - normalizedX * nextWidth - centeredLeft,
      y: anchorY - normalizedY * nextHeight - centeredTop,
    };
    applyView(nextZoom, nextPan, latestGeometry);
  }

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const observer = new ResizeObserver(synchronizeGeometry);
    observer.observe(viewport);
    document.addEventListener("fullscreenchange", synchronizeGeometry);
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      event.stopPropagation();
      const delta = Math.max(-120, Math.min(120, event.deltaY));
      const factor = Math.exp(-delta * 0.0022);
      setZoomAt(zoomRef.current * factor, event.clientX, event.clientY);
    };
    viewport.addEventListener("wheel", onWheel, { passive: false });
    synchronizeGeometry();
    return () => {
      observer.disconnect();
      document.removeEventListener("fullscreenchange", synchronizeGeometry);
      viewport.removeEventListener("wheel", onWheel);
    };
  }, []);

  function setZoomSafe(next: number) {
    setZoomAt(next);
  }

  function focusNormalized(x: number, y: number, requestedZoom = Math.max(2, zoomRef.current)) {
    const latestGeometry = measureWorld(viewportRef.current, imageRef.current) ?? geometryRef.current;
    if (!latestGeometry) return;
    const nextZoom = Math.max(latestGeometry.minimumZoom, Math.min(MAX_ZOOM, requestedZoom));
    const desired = {
      x: (0.5 - x) * latestGeometry.fittedWidth * nextZoom,
      y: (0.5 - y) * latestGeometry.fittedHeight * nextZoom,
    };
    applyView(nextZoom, desired, latestGeometry);
  }

  function focusMarker(marker: PositionedMarker) {
    setLayers((current) => ({ ...current, [marker.layer]: true }));
    setSelectedClusterId(null);
    setSelectedId(marker.entity.id);
    setQuery("");
    focusNormalized(marker.x, marker.y, Math.max(2.25, zoomRef.current));
  }

  function openCluster(cluster: MarkerCluster) {
    setSelectedId(null);
    setSelectedClusterId(cluster.id);
    focusNormalized(cluster.x, cluster.y, Math.min(MAX_ZOOM, Math.max(2.4, zoomRef.current + 0.65)));
  }

  function reset() {
    const latestGeometry = measureWorld(viewportRef.current, imageRef.current) ?? geometryRef.current;
    const minimumZoom = latestGeometry?.minimumZoom ?? 1;
    applyView(minimumZoom, { x: 0, y: 0 }, latestGeometry);
    setSelectedId(null);
    setSelectedClusterId(null);
  }

  async function fullscreen() {
    await viewportRef.current?.requestFullscreen();
  }

  const minimumZoom = geometry?.minimumZoom ?? 1;
  const selectedRouteDistance = selected?.entity_type === "route" ? numberField(selected.data, "distance_km") : null;

  return <div className="interactive-map-shell">
    <div className="interactive-map-toolbar">
      <div><strong>Carte interactive</strong><span>{markers.length} repère(s) · {vectors.length} tracé(s) · {filteredMarkers.length} repère(s) visible(s){unpositionedCount ? ` · ${unpositionedCount} connu(s) non localisé(s)` : ""}</span></div>
      <div className="map-controls">
        {currentMarker && <button className="secondary small" onClick={() => focusMarker(currentMarker)}>Ma position</button>}
        <button className="ghost small" onClick={() => setZoomSafe(zoom / 1.25)} disabled={zoom <= minimumZoom + .001}>−</button>
        <button className="ghost small" onClick={reset}>{Math.round(zoom * 100)} %</button>
        <button className="ghost small" onClick={() => setZoomSafe(zoom * 1.25)} disabled={zoom >= MAX_ZOOM - .001}>+</button>
        <button className="secondary small" onClick={() => fullscreen().catch(() => undefined)}>Plein écran</button>
      </div>
    </div>

    <div className="map-discovery-controls">
      <div className="map-layer-filters" aria-label="Couches de la carte">
        {LAYERS.map((layer) => <button
          key={layer.key}
          className={`map-layer-chip ${layers[layer.key] ? "active" : ""}`}
          aria-pressed={layers[layer.key]}
          onClick={() => setLayers((current) => ({ ...current, [layer.key]: !current[layer.key] }))}
          disabled={layerCounts[layer.key] === 0}
        >{layer.label}<span>{layerCounts[layer.key]}</span></button>)}
      </div>
      <div className="map-search-wrap">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Trouver un lieu connu…" aria-label="Trouver un lieu connu sur la carte" />
        {searchResults.length > 0 && <div className="map-search-results">
          {searchResults.map((marker) => <button key={marker.entity.id} onClick={() => focusMarker(marker)}>
            <strong>{markerLabel(marker.entity)}</strong><span>{entityTypeLabelFr(marker.entity.entity_type)}</span>
          </button>)}
        </div>}
      </div>
    </div>

    <div
      ref={viewportRef}
      className={`interactive-map-viewport ${dragRef.current ? "dragging" : ""}`}
      onPointerDown={(event) => {
        if ((event.target as HTMLElement).closest(".interactive-map-marker, .interactive-map-cluster")) return;
        dragRef.current = { pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, origin: panRef.current };
        event.currentTarget.setPointerCapture(event.pointerId);
      }}
      onPointerMove={(event) => {
        const drag = dragRef.current;
        if (!drag || drag.pointerId !== event.pointerId) return;
        const next = { x: drag.origin.x + event.clientX - drag.startX, y: drag.origin.y + event.clientY - drag.startY };
        const clamped = clampPanToWorld(next, zoomRef.current, geometryRef.current);
        panRef.current = clamped;
        setPan(clamped);
      }}
      onPointerUp={(event) => {
        if (dragRef.current?.pointerId === event.pointerId) dragRef.current = null;
        try { event.currentTarget.releasePointerCapture(event.pointerId); } catch { /* aucun effet */ }
      }}
      onPointerCancel={() => { dragRef.current = null; }}
    >
      <div className="interactive-map-stage">
        {rendered && <img
          ref={imageRef}
          src={imageUrl}
          alt="Carte physique interactive de Kitaba"
          draggable={false}
          decoding="async"
          onLoad={synchronizeGeometry}
          style={{ left: `${rendered.left}px`, top: `${rendered.top}px`, width: `${rendered.width}px`, height: `${rendered.height}px` }}
        />}
        {!rendered && <img ref={imageRef} src={imageUrl} alt="Carte physique interactive de Kitaba" draggable={false} decoding="async" onLoad={synchronizeGeometry} />}
        {rendered && <svg
          className="interactive-map-vector-layer"
          style={{ left: `${rendered.left}px`, top: `${rendered.top}px`, width: `${rendered.width}px`, height: `${rendered.height}px` }}
          viewBox="0 0 1000 500"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          {vectors.filter((feature) => layers[feature.layer]).map((feature) => {
            const points = feature.points.map((point) => `${point.x * 1000},${point.y * 500}`).join(" ");
            if (feature.closed) return <polygon key={feature.entity.id} className="map-vector-region" points={points} />;
            return <polyline key={feature.entity.id} className="map-vector-route" points={points} />;
          })}
          {uncertaintyMarkers.map((marker) => <ellipse
            key={`incertitude:${marker.entity.id}`}
            className={`map-uncertainty-area ${marker.entity.id === selectedId ? "selected" : ""}`}
            cx={marker.x * 1000}
            cy={marker.y * 500}
            rx={uncertaintyRadius(marker.entity, "x") * 1000}
            ry={uncertaintyRadius(marker.entity, "y") * 500}
          />)}
        </svg>}
        {clusters.map((cluster) => {
          const left = rendered ? rendered.left + cluster.x * rendered.width : cluster.x * 100;
          const top = rendered ? rendered.top + cluster.y * rendered.height : cluster.y * 100;
          const markerStyle = rendered ? { left: `${left}px`, top: `${top}px` } : { left: `${left}%`, top: `${top}%` };
          if (cluster.markers.length > 1) {
            return <button key={cluster.id} className={`interactive-map-cluster ${selectedClusterId === cluster.id ? "selected" : ""}`} style={markerStyle} onClick={(event) => {
              event.stopPropagation();
              openCluster(cluster);
            }} title={`${cluster.markers.length} lieux proches — ouvrir la liste`} aria-label={`${cluster.markers.length} lieux proches, ouvrir la liste`}>
              <span>{cluster.markers.length}</span>
            </button>;
          }

          const marker = cluster.markers[0];
          const label = markerLabel(marker.entity);
          const showLabel = marker.current || marker.entity.id === selectedId || marker.priority >= 80 || zoom >= 2.2;
          const knowledge = (stringField(marker.entity.data, "knowledge_state", "status", "known_status") ?? "known").toLocaleLowerCase("fr");
          const precision = (stringField(marker.entity.data, "location_precision", "map_precision") ?? "exact").toLocaleLowerCase("fr");
          return <button
            key={marker.entity.id}
            className={`interactive-map-marker layer-${marker.layer} ${marker.current ? "current" : ""} ${selectedId === marker.entity.id ? "selected" : ""} ${knowledge.includes("rumeur") || knowledge.includes("rumor") ? "rumor" : ""} ${precision.includes("approx") ? "approximate" : ""}`}
            style={markerStyle}
            onClick={(event) => { event.stopPropagation(); setSelectedClusterId(null); setSelectedId(marker.entity.id); }}
            title={label}
            aria-label={`Ouvrir ${label}`}
          ><span className="marker-dot" />{showLabel && <b>{label}</b>}</button>;
        })}
      </div>
    </div>

    {selectedCluster && <article className="interactive-map-cluster-details">
      <div className="map-details-head"><div><span className="eyebrow">Plusieurs repères</span><h3>Lieux à cet endroit</h3></div><button className="ghost small" onClick={() => setSelectedClusterId(null)}>Fermer</button></div>
      <div className="map-cluster-choice-list">{selectedCluster.markers.map((marker) => <button key={marker.entity.id} onClick={() => focusMarker(marker)}>
        <span><strong>{markerLabel(marker.entity)}</strong><small>{entityTypeLabelFr(marker.entity.entity_type)}</small></span>
        <em>{stringField(marker.entity.data, "summary", "known_description", "description") ?? "Ouvrir la fiche"}</em>
      </button>)}</div>
    </article>}

    {selected ? <article className="interactive-map-details">
      <div>
        <span className="eyebrow">{valueFr(stringField(selected.data, "category", "type", "kind") ?? entityTypeLabelFr(selected.entity_type))}</span>
        <h3>{markerLabel(selected)}</h3>
        <p>{stringField(selected.data, "summary", "description", "known_description", "player_description") ?? "Aucune description supplémentaire enregistrée."}</p>
      </div>
      <dl>
        {stringField(selected.data, "realm", "kingdom", "state_name") && <div><dt>Royaume / État</dt><dd>{valueFr(stringField(selected.data, "realm", "kingdom", "state_name"))}</dd></div>}
        {stringField(selected.data, "region", "region_name", "continent") && <div><dt>Région</dt><dd>{valueFr(stringField(selected.data, "region", "region_name", "continent"))}</dd></div>}
        {stringField(selected.data, "location_precision", "map_precision") && <div><dt>Précision</dt><dd>{valueFr(stringField(selected.data, "location_precision", "map_precision"))}</dd></div>}
        {selectedRouteDistance !== null && <div><dt>Distance de route</dt><dd>{selectedRouteDistance} km</dd></div>}
        {stringField(selected.data, "discovered_at", "first_known_at") && <div><dt>Découvert</dt><dd>{valueFr(stringField(selected.data, "discovered_at", "first_known_at"))}</dd></div>}
        {stringField(selected.data, "status", "known_status", "knowledge_state") && <div><dt>Statut connu</dt><dd>{valueFr(stringField(selected.data, "status", "known_status", "knowledge_state"))}</dd></div>}
      </dl>
      <button className="ghost small" onClick={() => setSelectedId(null)}>Fermer</button>
    </article> : !selectedCluster && <p className="interactive-map-hint">Molette sur la carte : zoom sous le curseur · cliquer-glisser : déplacer · cliquer sur un groupe numéroté : choisir le lieu. Le zoom n'entraîne jamais le défilement de la page.</p>}
  </div>;
}
