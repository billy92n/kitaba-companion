import { useEffect, useMemo, useRef, useState } from "react";
import type { EntityDocument } from "../lib/types";

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

const MAX_ZOOM = 6;

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

function measureWorld(viewport: HTMLDivElement | null, image: HTMLImageElement | null): WorldGeometry | null {
  if (!viewport) return null;

  const { width, height } = viewport.getBoundingClientRect();
  if (width <= 0 || height <= 0) return null;

  const naturalAspect = image?.naturalWidth && image?.naturalHeight
    ? image.naturalWidth / image.naturalHeight
    : 2;
  const viewportAspect = width / height;

  const fittedWidth = viewportAspect > naturalAspect ? height * naturalAspect : width;
  const fittedHeight = viewportAspect > naturalAspect ? height : width / naturalAspect;
  const offsetX = (width - fittedWidth) / 2;
  const offsetY = (height - fittedHeight) / 2;
  const minimumZoom = Math.max(1, width / fittedWidth, height / fittedHeight);

  return {
    viewportWidth: width,
    viewportHeight: height,
    fittedWidth,
    fittedHeight,
    offsetX,
    offsetY,
    minimumZoom,
  };
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

export function InteractiveMap({ imageUrl, entities }: Props) {
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const dragRef = useRef<{ pointerId: number; startX: number; startY: number; origin: Pan } | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<Pan>({ x: 0, y: 0 });
  const [geometry, setGeometry] = useState<WorldGeometry | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const markers = useMemo(() => entities.filter((entity) => {
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

  const selected = markers.find((marker) => marker.id === selectedId) ?? null;

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
      <div><strong>Carte interactive</strong><span>{markers.length} lieu(x) positionné(s)</span></div>
      <div className="map-controls">
        <button className="ghost small" onClick={() => setZoomSafe(zoom - .25)} disabled={zoom <= minimumZoom + .001}>−</button>
        <button className="ghost small" onClick={reset}>{Math.round(zoom * 100)} %</button>
        <button className="ghost small" onClick={() => setZoomSafe(zoom + .25)} disabled={zoom >= MAX_ZOOM}>+</button>
        <button className="secondary small" onClick={() => fullscreen().catch(() => undefined)}>Plein écran</button>
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
        if ((event.target as HTMLElement).closest(".interactive-map-marker")) return;
        dragRef.current = { pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, origin: pan };
        event.currentTarget.setPointerCapture(event.pointerId);
      }}
      onPointerMove={(event) => {
        const drag = dragRef.current;
        if (!drag || drag.pointerId !== event.pointerId || zoom <= minimumZoom) return;
        const next = {
          x: drag.origin.x + event.clientX - drag.startX,
          y: drag.origin.y + event.clientY - drag.startY,
        };
        setPan(clampPanToWorld(next, zoom, geometry));
      }}
      onPointerUp={(event) => {
        if (dragRef.current?.pointerId === event.pointerId) dragRef.current = null;
        try { event.currentTarget.releasePointerCapture(event.pointerId); } catch { /* no-op */ }
      }}
      onPointerCancel={() => { dragRef.current = null; }}
    >
      <div className="interactive-map-stage" style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}>
        <img
          ref={imageRef}
          src={imageUrl}
          alt="Carte physique interactive de Kitaba"
          draggable={false}
          onLoad={synchronizeGeometry}
        />
        {markers.map((marker) => {
          const normalizedX = numberField(marker.data, "x", "map_x") ?? 0;
          const normalizedY = numberField(marker.data, "y", "map_y") ?? 0;
          const current = marker.entity_type === "current_location" || marker.data.current === true || currentLinkedIds.has(marker.id);
          const label = markerLabel(marker);
          const markerStyle = geometry
            ? { left: `${geometry.offsetX + normalizedX * geometry.fittedWidth}px`, top: `${geometry.offsetY + normalizedY * geometry.fittedHeight}px` }
            : { left: `${normalizedX * 100}%`, top: `${normalizedY * 100}%` };
          return <button
            key={marker.id}
            className={`interactive-map-marker ${current ? "current" : ""} ${selectedId === marker.id ? "selected" : ""}`}
            style={markerStyle}
            onClick={(event) => { event.stopPropagation(); setSelectedId(marker.id); }}
            title={label}
            aria-label={`Ouvrir ${label}`}
          ><span className="marker-dot" /><b>{label}</b></button>;
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
        {stringField(selected.data, "status", "known_status") && <div><dt>Statut connu</dt><dd>{stringField(selected.data, "status", "known_status")}</dd></div>}
      </dl>
      <button className="ghost small" onClick={() => setSelectedId(null)}>Fermer</button>
    </article> : <p className="interactive-map-hint">Molette : zoom · cliquer-glisser : déplacer · cliquer sur un lieu : ouvrir sa fiche. La carte reste verrouillée sur les limites du monde et révèle uniquement les lieux présents dans le canon joueur.</p>}
  </div>;
}
