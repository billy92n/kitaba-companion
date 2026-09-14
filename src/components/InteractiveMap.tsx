import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { EntityDocument } from "../lib/types";
import { entityTypeLabelFr, valueFr } from "../lib/frenchUi";
import "../interactive-map-mvp.css";

type Props = {
  imageUrl: string;
  entities: EntityDocument[];
};

type Pan = { x: number; y: number };
type Geometry = {
  viewportWidth: number;
  viewportHeight: number;
  naturalWidth: number;
  naturalHeight: number;
  fitScale: number;
  maxScale: number;
};
type LayerKey = "settlements" | "political" | "routes" | "dungeons" | "other";
type PositionedMarker = { entity: EntityDocument; x: number; y: number; current: boolean; priority: number; layer: LayerKey };
type ScreenMarker = PositionedMarker & { sx: number; sy: number };
type MarkerCluster = { id: string; sx: number; sy: number; markers: ScreenMarker[] };
type NormalizedPoint = { x: number; y: number };
type VectorFeature = { entity: EntityDocument; layer: "political" | "routes"; points: NormalizedPoint[]; closed: boolean };

const LAYERS: Array<{ key: LayerKey; label: string }> = [
  { key: "settlements", label: "Lieux" },
  { key: "political", label: "Régions" },
  { key: "routes", label: "Routes" },
  { key: "dungeons", label: "Donjons" },
  { key: "other", label: "Autres" },
];
const CLUSTER_RADIUS_PX = 38;
const SPIDER_RADIUS_PX = 58;

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
  if (entity.entity_type === "route") {
    const points = parseNormalizedPoints(entity.data.path ?? entity.data.points ?? entity.data.map_path);
    return points.length >= 2 ? { entity, layer: "routes", points, closed: false } : null;
  }
  if (["region", "state"].includes(entity.entity_type)) {
    const points = parseNormalizedPoints(entity.data.polygon ?? entity.data.boundary ?? entity.data.map_polygon);
    return points.length >= 3 ? { entity, layer: "political", points, closed: true } : null;
  }
  return null;
}

function clampPan(next: Pan, scale: number, geometry: Geometry | null): Pan {
  if (!geometry) return next;
  const renderedWidth = geometry.naturalWidth * scale;
  const renderedHeight = geometry.naturalHeight * scale;
  const x = renderedWidth <= geometry.viewportWidth
    ? (geometry.viewportWidth - renderedWidth) / 2
    : Math.max(geometry.viewportWidth - renderedWidth, Math.min(0, next.x));
  const y = renderedHeight <= geometry.viewportHeight
    ? (geometry.viewportHeight - renderedHeight) / 2
    : Math.max(geometry.viewportHeight - renderedHeight, Math.min(0, next.y));
  return { x, y };
}

function fitPan(scale: number, geometry: Geometry) {
  return {
    x: (geometry.viewportWidth - geometry.naturalWidth * scale) / 2,
    y: (geometry.viewportHeight - geometry.naturalHeight * scale) / 2,
  };
}

function visibleAtScale(marker: PositionedMarker, scale: number, geometry: Geometry | null) {
  if (!geometry) return true;
  const zoomFactor = scale / geometry.fitScale;
  if (marker.current || marker.priority >= 80) return true;
  if (marker.priority >= 65) return zoomFactor >= 1.05;
  if (marker.priority >= 50) return zoomFactor >= 1.25;
  if (marker.priority >= 40) return zoomFactor >= 1.55;
  return zoomFactor >= 1.9;
}

function clusterMarkers(markers: ScreenMarker[]): MarkerCluster[] {
  const clusters: MarkerCluster[] = [];
  const sorted = [...markers].sort((a, b) => b.priority - a.priority);
  for (const marker of sorted) {
    const target = clusters.find((cluster) => Math.hypot(cluster.sx - marker.sx, cluster.sy - marker.sy) <= CLUSTER_RADIUS_PX);
    if (!target) {
      clusters.push({ id: marker.entity.id, sx: marker.sx, sy: marker.sy, markers: [marker] });
      continue;
    }
    target.markers.push(marker);
    target.sx = target.markers.reduce((sum, row) => sum + row.sx, 0) / target.markers.length;
    target.sy = target.markers.reduce((sum, row) => sum + row.sy, 0) / target.markers.length;
    target.id = target.markers.map((row) => row.entity.id).sort().join(":");
  }
  return clusters;
}

function markerScreen(marker: PositionedMarker, pan: Pan, scale: number, geometry: Geometry) {
  return {
    ...marker,
    sx: pan.x + marker.x * geometry.naturalWidth * scale,
    sy: pan.y + marker.y * geometry.naturalHeight * scale,
  };
}

export function InteractiveMap({ imageUrl, entities }: Props) {
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const geometryRef = useRef<Geometry | null>(null);
  const scaleRef = useRef(1);
  const panRef = useRef<Pan>({ x: 0, y: 0 });
  const dragRef = useRef<{ pointerId: number; startX: number; startY: number; origin: Pan } | null>(null);
  const [geometry, setGeometry] = useState<Geometry | null>(null);
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState<Pan>({ x: 0, y: 0 });
  const [imageReady, setImageReady] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [spiderClusterId, setSpiderClusterId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({ settlements: true, political: true, routes: true, dungeons: true, other: true });

  useEffect(() => { geometryRef.current = geometry; }, [geometry]);
  useEffect(() => { scaleRef.current = scale; }, [scale]);
  useEffect(() => { panRef.current = pan; }, [pan]);

  const rawMarkers = useMemo(() => entities.filter((entity) => {
    const x = numberField(entity.data, "x", "map_x");
    const y = numberField(entity.data, "y", "map_y");
    return x !== null && y !== null && x >= 0 && x <= 1 && y >= 0 && y <= 1;
  }), [entities]);
  const vectors = useMemo(() => entities.map(vectorFeature).filter((feature): feature is VectorFeature => feature !== null), [entities]);
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
  const visibleMarkers = useMemo(() => markers.filter((marker) => layers[marker.layer] && visibleAtScale(marker, scale, geometry)), [markers, layers, scale, geometry]);
  const screenMarkers = useMemo(() => geometry ? visibleMarkers.map((marker) => markerScreen(marker, pan, scale, geometry)) : [], [visibleMarkers, geometry, pan, scale]);
  const clusters = useMemo(() => clusterMarkers(screenMarkers), [screenMarkers]);
  const spiderCluster = spiderClusterId ? clusters.find((cluster) => cluster.id === spiderClusterId) ?? null : null;
  const selected = markers.find((marker) => marker.entity.id === selectedId)?.entity ?? null;

  const layerCounts = useMemo(() => {
    const counts: Record<LayerKey, number> = { settlements: 0, political: 0, routes: 0, dungeons: 0, other: 0 };
    for (const marker of markers) counts[marker.layer] += 1;
    for (const feature of vectors) counts[feature.layer] += 1;
    return counts;
  }, [markers, vectors]);

  const searchResults = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("fr");
    if (!normalized) return [];
    return markers.filter((marker) => `${markerLabel(marker.entity)} ${entityTypeLabelFr(marker.entity.entity_type)} ${stringField(marker.entity.data, "region", "realm", "kingdom", "summary", "description") ?? ""}`.toLocaleLowerCase("fr").includes(normalized)).slice(0, 8);
  }, [markers, query]);

  const applyView = useCallback((nextScale: number, nextPan: Pan, nextGeometry = geometryRef.current) => {
    if (!nextGeometry) return;
    const clampedScale = Math.max(nextGeometry.fitScale, Math.min(nextGeometry.maxScale, nextScale));
    const clampedPan = clampPan(nextPan, clampedScale, nextGeometry);
    scaleRef.current = clampedScale;
    panRef.current = clampedPan;
    setScale(clampedScale);
    setPan(clampedPan);
    setSpiderClusterId(null);
  }, []);

  const fitMap = useCallback((nextGeometry = geometryRef.current) => {
    if (!nextGeometry) return;
    applyView(nextGeometry.fitScale, fitPan(nextGeometry.fitScale, nextGeometry), nextGeometry);
  }, [applyView]);

  const nativeMap = useCallback(() => {
    const g = geometryRef.current;
    if (!g) return;
    const target = Math.min(1, g.maxScale);
    applyView(target, fitPan(target, g), g);
  }, [applyView]);

  const setScaleAt = useCallback((nextScale: number, clientX?: number, clientY?: number) => {
    const g = geometryRef.current;
    const viewport = viewportRef.current;
    if (!g || !viewport) return;
    const currentScale = scaleRef.current;
    const rect = viewport.getBoundingClientRect();
    const anchorX = clientX === undefined ? g.viewportWidth / 2 : clientX - rect.left;
    const anchorY = clientY === undefined ? g.viewportHeight / 2 : clientY - rect.top;
    const sourceX = (anchorX - panRef.current.x) / currentScale;
    const sourceY = (anchorY - panRef.current.y) / currentScale;
    const bounded = Math.max(g.fitScale, Math.min(g.maxScale, nextScale));
    applyView(bounded, { x: anchorX - sourceX * bounded, y: anchorY - sourceY * bounded }, g);
  }, [applyView]);

  useEffect(() => {
    setImageReady(false);
    const image = new Image();
    image.decoding = "async";
    image.onload = () => {
      imageRef.current = image;
      setImageReady(true);
      const viewport = viewportRef.current;
      if (!viewport) return;
      const rect = viewport.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const fitScale = Math.min(1, rect.width / image.naturalWidth, rect.height / image.naturalHeight);
      const next: Geometry = {
        viewportWidth: rect.width,
        viewportHeight: rect.height,
        naturalWidth: image.naturalWidth,
        naturalHeight: image.naturalHeight,
        fitScale,
        maxScale: 1,
      };
      geometryRef.current = next;
      setGeometry(next);
      scaleRef.current = fitScale;
      const initialPan = fitPan(fitScale, next);
      panRef.current = initialPan;
      setScale(fitScale);
      setPan(initialPan);
    };
    image.src = imageUrl;
    return () => { image.onload = null; };
  }, [imageUrl]);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const observer = new ResizeObserver(() => {
      const image = imageRef.current;
      if (!image) return;
      const rect = viewport.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const fitScale = Math.min(1, rect.width / image.naturalWidth, rect.height / image.naturalHeight);
      const next: Geometry = { viewportWidth: rect.width, viewportHeight: rect.height, naturalWidth: image.naturalWidth, naturalHeight: image.naturalHeight, fitScale, maxScale: 1 };
      geometryRef.current = next;
      setGeometry(next);
      const nextScale = Math.max(fitScale, Math.min(1, scaleRef.current));
      applyView(nextScale, panRef.current, next);
    });
    observer.observe(viewport);
    return () => observer.disconnect();
  }, [applyView]);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      event.stopPropagation();
      const factor = Math.exp(-event.deltaY * 0.0015);
      setScaleAt(scaleRef.current * factor, event.clientX, event.clientY);
    };
    viewport.addEventListener("wheel", onWheel, { passive: false });
    return () => viewport.removeEventListener("wheel", onWheel);
  }, [setScaleAt]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    const g = geometry;
    if (!canvas || !image || !g || !imageReady) return;
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    canvas.width = Math.round(g.viewportWidth * dpr);
    canvas.height = Math.round(g.viewportHeight * dpr);
    canvas.style.width = `${g.viewportWidth}px`;
    canvas.style.height = `${g.viewportHeight}px`;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, g.viewportWidth, g.viewportHeight);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(image, pan.x, pan.y, g.naturalWidth * scale, g.naturalHeight * scale);

    for (const feature of vectors) {
      if (!layers[feature.layer]) continue;
      ctx.beginPath();
      feature.points.forEach((point, index) => {
        const x = pan.x + point.x * g.naturalWidth * scale;
        const y = pan.y + point.y * g.naturalHeight * scale;
        if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      if (feature.closed) ctx.closePath();
      if (feature.layer === "routes") {
        ctx.strokeStyle = "rgba(225,205,155,.82)";
        ctx.lineWidth = 2.2;
        ctx.stroke();
      } else {
        ctx.fillStyle = "rgba(157,132,81,.12)";
        ctx.strokeStyle = "rgba(211,188,133,.72)";
        ctx.lineWidth = 1.5;
        ctx.fill();
        ctx.stroke();
      }
    }

    for (const marker of visibleMarkers.filter((row) => isApproximate(row.entity))) {
      const x = pan.x + marker.x * g.naturalWidth * scale;
      const y = pan.y + marker.y * g.naturalHeight * scale;
      const rx = uncertaintyRadius(marker.entity, "x") * g.naturalWidth * scale;
      const ry = uncertaintyRadius(marker.entity, "y") * g.naturalHeight * scale;
      ctx.beginPath();
      ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(225,203,141,.12)";
      ctx.strokeStyle = "rgba(240,219,159,.8)";
      ctx.lineWidth = 1.5;
      ctx.setLineDash([5, 4]);
      ctx.fill();
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }, [geometry, imageReady, scale, pan, vectors, visibleMarkers, layers]);

  function focusMarker(marker: PositionedMarker) {
    const g = geometryRef.current;
    if (!g) return;
    const targetScale = Math.min(1, Math.max(scaleRef.current, g.fitScale * 2.1));
    const targetPan = {
      x: g.viewportWidth / 2 - marker.x * g.naturalWidth * targetScale,
      y: g.viewportHeight / 2 - marker.y * g.naturalHeight * targetScale,
    };
    applyView(targetScale, targetPan, g);
    setSelectedId(marker.entity.id);
    setQuery("");
  }

  function openCluster(cluster: MarkerCluster) {
    setSelectedId(null);
    setSpiderClusterId((current) => current === cluster.id ? null : cluster.id);
  }

  const spiderItems = spiderCluster ? spiderCluster.markers.map((marker, index) => {
    const angle = -Math.PI / 2 + index * (Math.PI * 2 / spiderCluster.markers.length);
    const radius = SPIDER_RADIUS_PX + Math.min(30, spiderCluster.markers.length * 3);
    return { marker, x: spiderCluster.sx + Math.cos(angle) * radius, y: spiderCluster.sy + Math.sin(angle) * radius };
  }) : [];

  const zoomPercent = Math.round(scale * 100);
  const routeDistance = selected ? numberField(selected.data, "distance_km") : null;

  return <div className="interactive-map-shell">
    <div className="map-discovery-controls">
      <div className="map-layer-filters">{LAYERS.map((layer) => <button key={layer.key} className={`map-layer-chip ${layers[layer.key] ? "active" : ""}`} disabled={layerCounts[layer.key] === 0} onClick={() => setLayers((current) => ({ ...current, [layer.key]: !current[layer.key] }))}>{layer.label}<span>{layerCounts[layer.key]}</span></button>)}</div>
      <div className="map-search-wrap"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Rechercher un lieu…" aria-label="Rechercher un lieu" />{searchResults.length > 0 && <div className="map-search-results">{searchResults.map((marker) => <button key={marker.entity.id} onClick={() => focusMarker(marker)}><strong>{markerLabel(marker.entity)}</strong><span>{entityTypeLabelFr(marker.entity.entity_type)}</span></button>)}</div>}</div>
    </div>

    <div className="map-hd-toolbar">
      <div><strong>{zoomPercent}%</strong><span>{geometry ? `${geometry.naturalWidth} × ${geometry.naturalHeight} px` : "Chargement…"}</span></div>
      <div className="map-controls"><button className="ghost small" onClick={() => setScaleAt(scaleRef.current / 1.25)}>−</button><button className="ghost small" onClick={() => setScaleAt(scaleRef.current * 1.25)}>+</button><button className="ghost small" onClick={() => fitMap()}>Ajuster</button><button className="ghost small" onClick={nativeMap} disabled={!geometry || geometry.fitScale >= 1}>100% natif</button><button className="ghost small" onClick={() => viewportRef.current?.requestFullscreen?.()}>Plein écran</button>{currentMarker && <button className="secondary small" onClick={() => focusMarker(currentMarker)}>Ma position</button>}</div>
    </div>

    <div
      ref={viewportRef}
      className="interactive-map-viewport hd-map"
      onPointerDown={(event) => {
        if ((event.target as HTMLElement).closest("button")) return;
        dragRef.current = { pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, origin: panRef.current };
        event.currentTarget.setPointerCapture(event.pointerId);
      }}
      onPointerMove={(event) => {
        const drag = dragRef.current;
        if (!drag || drag.pointerId !== event.pointerId) return;
        applyView(scaleRef.current, { x: drag.origin.x + event.clientX - drag.startX, y: drag.origin.y + event.clientY - drag.startY });
      }}
      onPointerUp={(event) => {
        if (dragRef.current?.pointerId === event.pointerId) dragRef.current = null;
      }}
      onPointerCancel={() => { dragRef.current = null; }}
      onClick={(event) => {
        if (event.target === event.currentTarget || event.target === canvasRef.current) setSpiderClusterId(null);
      }}
    >
      <canvas ref={canvasRef} className="interactive-map-raster-canvas" aria-label="Carte du monde" />
      <div className="interactive-map-marker-layer">
        {clusters.map((cluster) => {
          if (spiderClusterId === cluster.id) return null;
          if (cluster.markers.length > 1) return <button key={cluster.id} className="interactive-map-cluster" style={{ left: `${cluster.sx}px`, top: `${cluster.sy}px` }} onClick={(event) => { event.stopPropagation(); openCluster(cluster); }} title={`${cluster.markers.length} lieux proches — ouvrir`} aria-label={`${cluster.markers.length} lieux proches, ouvrir`}><span>{cluster.markers.length}</span></button>;
          const marker = cluster.markers[0];
          const label = markerLabel(marker.entity);
          const showLabel = marker.current || marker.priority >= 65 || selectedId === marker.entity.id;
          return <button key={marker.entity.id} className={`interactive-map-marker layer-${marker.layer} ${marker.current ? "current" : ""} ${isApproximate(marker.entity) ? "approximate" : ""} ${selectedId === marker.entity.id ? "selected" : ""}`} style={{ left: `${marker.sx}px`, top: `${marker.sy}px` }} onClick={(event) => { event.stopPropagation(); setSelectedId(marker.entity.id); setSpiderClusterId(null); }} title={label}><span className="marker-dot" />{showLabel && <b>{label}</b>}</button>;
        })}

        {spiderCluster && <>
          <svg className="map-spider-lines" width="100%" height="100%" aria-hidden="true">{spiderItems.map(({ marker, x, y }) => <line key={marker.entity.id} x1={spiderCluster.sx} y1={spiderCluster.sy} x2={x} y2={y} />)}</svg>
          <button className="interactive-map-cluster spider-center" style={{ left: `${spiderCluster.sx}px`, top: `${spiderCluster.sy}px` }} onClick={(event) => { event.stopPropagation(); setSpiderClusterId(null); }} aria-label="Refermer les repères"><span>{spiderCluster.markers.length}</span></button>
          {spiderItems.map(({ marker, x, y }) => <button key={marker.entity.id} className="interactive-map-spider-marker" style={{ left: `${x}px`, top: `${y}px` }} onClick={(event) => { event.stopPropagation(); focusMarker(marker); setSpiderClusterId(null); }} title={markerLabel(marker.entity)}><span className="marker-dot" /><b>{markerLabel(marker.entity)}</b></button>)}
        </>}
      </div>
    </div>

    {spiderCluster && <article className="interactive-map-cluster-details"><div className="map-details-head"><div><span className="eyebrow">Plusieurs repères</span><h3>Lieux à cet endroit</h3></div><button className="ghost small" onClick={() => setSpiderClusterId(null)}>Fermer</button></div><div className="map-cluster-choice-list">{spiderCluster.markers.map((marker) => <button key={marker.entity.id} onClick={() => focusMarker(marker)}><span><strong>{markerLabel(marker.entity)}</strong><small>{entityTypeLabelFr(marker.entity.entity_type)}</small></span><em>{stringField(marker.entity.data, "summary", "known_description", "description") ?? "Ouvrir la fiche"}</em></button>)}</div></article>}

    {selected && <article className="interactive-map-details"><div><span className="eyebrow">{entityTypeLabelFr(selected.entity_type)}</span><h3>{markerLabel(selected)}</h3></div><p>{stringField(selected.data, "known_summary", "summary", "known_description", "description") ?? "Aucune description supplémentaire connue."}</p>{routeDistance !== null && <p><b>Distance de route :</b> {valueFr(routeDistance)} km</p>}</article>}

    {geometry && <p className="map-resolution-note">Le zoom affiché correspond à la densité réelle de l'image : <b>100% = pixels natifs</b>. La carte n'est plus agrandie au-delà de sa résolution source.</p>}
  </div>;
}
