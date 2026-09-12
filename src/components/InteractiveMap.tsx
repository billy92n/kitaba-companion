import { useMemo, useRef, useState } from "react";
import type { EntityDocument } from "../lib/types";

type Props = {
  imageUrl: string;
  entities: EntityDocument[];
};

type Pan = { x: number; y: number };

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

export function InteractiveMap({ imageUrl, entities }: Props) {
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const dragRef = useRef<{ pointerId: number; startX: number; startY: number; origin: Pan } | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<Pan>({ x: 0, y: 0 });
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const markers = useMemo(() => entities.filter((entity) => {
    const x = numberField(entity.data, "x", "map_x");
    const y = numberField(entity.data, "y", "map_y");
    return x !== null && y !== null && x >= 0 && x <= 1 && y >= 0 && y <= 1;
  }), [entities]);

  const selected = markers.find((marker) => marker.id === selectedId) ?? null;

  function setZoomSafe(next: number) {
    const value = Math.max(1, Math.min(6, Number(next.toFixed(2))));
    setZoom(value);
    if (value === 1) setPan({ x: 0, y: 0 });
  }

  function reset() {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSelectedId(null);
  }

  async function fullscreen() {
    await viewportRef.current?.requestFullscreen();
  }

  return <div className="interactive-map-shell">
    <div className="interactive-map-toolbar">
      <div><strong>Carte interactive</strong><span>{markers.length} lieu(x) positionné(s)</span></div>
      <div className="map-controls">
        <button className="ghost small" onClick={() => setZoomSafe(zoom - .25)} disabled={zoom <= 1}>−</button>
        <button className="ghost small" onClick={reset}>{Math.round(zoom * 100)} %</button>
        <button className="ghost small" onClick={() => setZoomSafe(zoom + .25)} disabled={zoom >= 6}>+</button>
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
        if (!drag || drag.pointerId !== event.pointerId || zoom <= 1) return;
        setPan({ x: drag.origin.x + event.clientX - drag.startX, y: drag.origin.y + event.clientY - drag.startY });
      }}
      onPointerUp={(event) => {
        if (dragRef.current?.pointerId === event.pointerId) dragRef.current = null;
        try { event.currentTarget.releasePointerCapture(event.pointerId); } catch { /* no-op */ }
      }}
      onPointerCancel={() => { dragRef.current = null; }}
    >
      <div className="interactive-map-stage" style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}>
        <img src={imageUrl} alt="Carte physique interactive de Kitaba" draggable={false} />
        {markers.map((marker) => {
          const x = (numberField(marker.data, "x", "map_x") ?? 0) * 100;
          const y = (numberField(marker.data, "y", "map_y") ?? 0) * 100;
          const current = marker.entity_type === "current_location" || marker.data.current === true;
          const label = markerLabel(marker);
          return <button
            key={marker.id}
            className={`interactive-map-marker ${current ? "current" : ""} ${selectedId === marker.id ? "selected" : ""}`}
            style={{ left: `${x}%`, top: `${y}%` }}
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
    </article> : <p className="interactive-map-hint">Molette : zoom · cliquer-glisser : déplacer · cliquer sur un lieu : ouvrir sa fiche. La carte révèle uniquement les lieux présents dans le canon joueur.</p>}
  </div>;
}
