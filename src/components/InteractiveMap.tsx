import { useEffect, useMemo, useRef, useState } from "react";
import type { EntityDocument } from "../lib/types";
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

const MAX_ZOOM = 6;
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
  const radius = 0.075 / Math.max(1, zoom);
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

export function InteractiveMap({ imageUrl, entities }: Props) {
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const dragRef = useRef<{ pointerId: number; startX: number; startY: number; origin: Pan } | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<Pan>({ x: 0, y: 0 });
  const [geometry, setGeometry] = useState<WorldGeometry | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({ settlements: true, political: true, routes: true, dungeons: true, other: true });

  const rawMarkers = useMemo(() => entities.filter((entity) => {
    const x = numberField(entity.data, "x", "map_x");
    const y = numberField(entity.data, "y", "map_y");
    return x !== null && y !== null && x >= 0 && x <= 1 && y >= 0 && y <= 1;
  }), [entities]);

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

  const searchResults = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("fr");
    if (!normalized) return [];
    return markers.filter((marker) => {
      const haystack = `${markerLabel(marker.entity)} ${marker.entity.entity_type} ${stringField(marker.entity.data, "region", "realm", "kingdom", "summary", "description") ?? ""}`.toLocaleLowerCase("fr");
      return haystack.includes(normalized);
    }).slice(0, 6);
  }, [markers, query]);

  const layerCounts = useMemo(() => {
    const counts: Record<LayerKey, number> = { settlements: 0, political: 0, routes: 0, dungeons: 0, other: 0 };
    for (const marker of markers) counts[marker.layer] += 1;
    return counts;
  }, [markers]);

  function synchronizeGeometry() {
    const nextGeometry = measureWorld(viewportRef.current, imageRef.current);
    if (!nextGeometry) return;
    setGeometry(nextGeometry);
    setZoom((currentZoom) => {
      const nextZoom = Math.max(nextGeometry.minimumZoom, Math.min(MAX_ZOOM, currentZoom));
      setPan((currentPan) => clampPanToWorld(currentPan, nextZoom, nextGeometry));
      return nextZoom;
    });
  }

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const observer = new ResizeObserver(synchronizeGeometry);
    observer.observe(viewport);
    document.addEventListener("fullscreenchange", synchronizeGeometry);
    synchronizeGeometry();
    return () => {
      observer.disconnect();
      document.removeEventListener("fullscreenchange", synchronizeGeometry);
    };
  }, []);

  function setZoomSafe(next: number) {
    const latestGeometry = measureWorld(viewportRef.current, imageRef.current) ?? geometry;
    const minimumZoom = latestGeometry?.minimumZoom ?? 1;
    const value = Math.max(minimumZoom, Math.min(MAX_ZOOM, Number(next.toFixed(2))));
    setZoom(value);
    setPan((current) => clampPanToWorld(current, value, latestGeometry));
  }

  function focusNormalized(x: number, y: number, requestedZoom = Math.max(2, zoom)) {
    const latestGeometry = measureWorld(viewportRef.current, imageRef.current) ?? geometry;
    if (!latestGeometry) return;
    const nextZoom = Math.max(latestGeometry.minimumZoom, Math.min(MAX_ZOOM, requestedZoom));
    const baseX = latestGeometry.offsetX + x * latestGeometry.fittedWidth;
    const baseY = latestGeometry.offsetY + y * latestGeometry.fittedHeight;
    const desired = {
      x: -(baseX - latestGeometry.viewportWidth / 2) * nextZoom,
      y: -(baseY - latestGeometry.viewportHeight / 2) * nextZoom,
    };
    setZoom(nextZoom);
    setPan(clampPanToWorld(desired, nextZoom, latestGeometry));
  }

  function focusMarker(marker: PositionedMarker) {
    setLayers((current) => ({ ...current, [marker.layer]: true }));
    setSelectedId(marker.entity.id);
    setQuery("");
    focusNormalized(marker.x, marker.y, Math.max(2.25, zoom));
  }

  function reset() {
    const latestGeometry = measureWorld(viewportRef.current, imageRef.current) ?? geometry;
    const minimumZoom = latestGeometry?.minimumZoom ?? 1;
    setZoom(minimumZoom);
    setPan({ x: 0, y: 0 });
    setSelectedId(null);
  }

  async function fullscreen() {
    await viewportRef.current?.requestFullscreen();
  }

  const minimumZoom = geometry?.minimumZoom ?? 1;

  return <div className="interactive-map-shell">
    <div className="interactive-map-toolbar">
      <div><strong>Carte interactive</strong><span>{markers.length} lieu(x) positionné(s) · {filteredMarkers.length} visible(s) à ce niveau</span></div>
      <div className="map-controls">
        {currentMarker && <button className="secondary small" onClick={() => focusMarker(currentMarker)}>Ma position</button>}
        <button className="ghost small" onClick={() => setZoomSafe(zoom - .25)} disabled={zoom <= minimumZoom + .001}>−</button>
        <button className="ghost small" onClick={reset}>{Math.round(zoom * 100)} %</button>
        <button className="ghost small" onClick={() => setZoomSafe(zoom + .25)} disabled={zoom >= MAX_ZOOM}>+</button>
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
            <strong>{markerLabel(marker.entity)}</strong><span>{marker.entity.entity_type}</span>
          </button>)}
        </div>}
      </div>
    </div>

    <div
      ref={viewportRef}
      className={`interactive-map-viewport ${dragRef.current ? "dragging" : ""}`}
      onWheel={(event) => {
        event.preventDefault();
        setZoomSafe(zoom + (event.deltaY < 0 ? .2 : -.2));
      }}
      onPointerDown={(event) => {
        if ((event.target as HTMLElement).closest(".interactive-map-marker, .interactive-map-cluster")) return;
        dragRef.current = { pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, origin: pan };
        event.currentTarget.setPointerCapture(event.pointerId);
      }}
      onPointerMove={(event) => {
        const drag = dragRef.current;
        if (!drag || drag.pointerId !== event.pointerId || zoom <= minimumZoom) return;
        const next = { x: drag.origin.x + event.clientX - drag.startX, y: drag.origin.y + event.clientY - drag.startY };
        setPan(clampPanToWorld(next, zoom, geometry));
      }}
      onPointerUp={(event) => {
        if (dragRef.current?.pointerId === event.pointerId) dragRef.current = null;
        try { event.currentTarget.releasePointerCapture(event.pointerId); } catch { /* no-op */ }
      }}
      onPointerCancel={() => { dragRef.current = null; }}
    >
      <div className="interactive-map-stage" style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, ["--map-marker-scale" as string]: zoom }}>
        <img ref={imageRef} src={imageUrl} alt="Carte physique interactive de Kitaba" draggable={false} onLoad={synchronizeGeometry} />
        {clusters.map((cluster) => {
          const left = geometry ? geometry.offsetX + cluster.x * geometry.fittedWidth : cluster.x * 100;
          const top = geometry ? geometry.offsetY + cluster.y * geometry.fittedHeight : cluster.y * 100;
          const markerStyle = geometry ? { left: `${left}px`, top: `${top}px` } : { left: `${left}%`, top: `${top}%` };
          if (cluster.markers.length > 1) {
            return <button key={cluster.id} className="interactive-map-cluster" style={markerStyle} onClick={(event) => {
              event.stopPropagation();
              focusNormalized(cluster.x, cluster.y, Math.min(MAX_ZOOM, zoom + 1));
            }} title={`${cluster.markers.length} lieux proches — cliquer pour zoomer`} aria-label={`${cluster.markers.length} lieux proches, zoomer`}>
              <span>{cluster.markers.length}</span>
            </button>;
          }

          const marker = cluster.markers[0];
          const label = markerLabel(marker.entity);
          const showLabel = marker.current || marker.entity.id === selectedId || marker.priority >= 80 || zoom >= 2.2;
          const knowledge = (stringField(marker.entity.data, "knowledge_state", "status", "known_status") ?? "known").toLocaleLowerCase("fr");
          return <button
            key={marker.entity.id}
            className={`interactive-map-marker layer-${marker.layer} ${marker.current ? "current" : ""} ${selectedId === marker.entity.id ? "selected" : ""} ${knowledge.includes("rumeur") || knowledge.includes("rumor") ? "rumor" : ""}`}
            style={markerStyle}
            onClick={(event) => { event.stopPropagation(); setSelectedId(marker.entity.id); }}
            title={label}
            aria-label={`Ouvrir ${label}`}
          ><span className="marker-dot" />{showLabel && <b>{label}</b>}</button>;
        })}
      </div>
    </div>

    {selected ? <article className="interactive-map-details">
      <div>
        <span className="eyebrow">{stringField(selected.data, "category", "type", "kind") ?? "Lieu découvert"}</span>
        <h3>{markerLabel(selected)}</h3>
        <p>{stringField(selected.data, "summary", "description", "known_description", "player_description") ?? "Aucune description supplémentaire enregistrée."}</p>
      </div>
      <dl>
        {stringField(selected.data, "realm", "kingdom", "state_name") && <div><dt>Royaume / État</dt><dd>{stringField(selected.data, "realm", "kingdom", "state_name")}</dd></div>}
        {stringField(selected.data, "region", "region_name", "continent") && <div><dt>Région</dt><dd>{stringField(selected.data, "region", "region_name", "continent")}</dd></div>}
        {stringField(selected.data, "discovered_at", "first_known_at") && <div><dt>Découvert</dt><dd>{stringField(selected.data, "discovered_at", "first_known_at")}</dd></div>}
        {stringField(selected.data, "status", "known_status", "knowledge_state") && <div><dt>Statut connu</dt><dd>{stringField(selected.data, "status", "known_status", "knowledge_state")}</dd></div>}
      </dl>
      <button className="ghost small" onClick={() => setSelectedId(null)}>Fermer</button>
    </article> : <p className="interactive-map-hint">Molette : zoom · cliquer-glisser : déplacer · un groupe numéroté se sépare en zoomant. Les détails apparaissent progressivement et la carte reste verrouillée sur les limites du monde.</p>}
  </div>;
}
