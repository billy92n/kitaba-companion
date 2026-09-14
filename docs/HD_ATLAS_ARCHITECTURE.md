# Kitaba Companion — HD Atlas Architecture

## Immediate 0.1.6 rendering contract

The interactive atlas must never pretend that a fitted raster is already at 100% native resolution.

- `100%` means one source-image pixel per CSS pixel.
- Initial fit may therefore be 35%, 50%, etc.
- The renderer uses a `devicePixelRatio`-aware canvas.
- Automatic zoom is capped at the source's native raster resolution; the UI does not silently upscale the map beyond 100%.
- Exact and near-overlapping markers are clustered in screen-pixel space and can be spiderfied so every child marker remains individually clickable.
- Search, player-knowledge gating, layers and current-position focus stay independent of the raster renderer.

This removes the previous misleading behavior where a single DOM `<img>` could be enlarged many times beyond its native pixel dimensions.

## Why a single source image still has limits

A 1774×887 map contains exactly that many source pixels. No CSS or canvas renderer can reveal genuine extra detail beyond those pixels. The native-resolution renderer prevents avoidable blur, but it cannot manufacture 8K detail from a 1774px source.

For sharper deep zoom, the source asset itself must be larger or use a multiresolution pyramid.

## Post-MVP robust path: local tile pyramid

For large 8K/16K+ world maps, the preferred architecture is:

1. import the original high-resolution source once;
2. generate a local multiresolution pyramid (DZI/XYZ-style tiles) in the Tauri backend;
3. persist pyramid metadata with the campaign asset;
4. load only visible tiles at the appropriate zoom level;
5. keep markers/routes/regions as independent vector/UI overlays;
6. cache recently used tiles locally.

This follows the same general architecture used by deep-zoom image viewers and modern tiled map renderers: multiple raster levels rather than indefinitely stretching one bitmap.

## Candidate libraries / references

- OpenSeadragon: strong fit for arbitrary fantasy images and Deep Zoom/DZI pyramids.
- MapLibre GL JS: strong if Kitaba later moves toward conventional raster/vector tile sources and richer geographic layers.
- Marker-cluster/spiderfy behavior: retain in Kitaba even if the raster engine changes; overlapping POIs must always expose an explicit selection path.

## MVP acceptance criteria

- fit view is sharp for the available source;
- 100% is native source density;
- wheel zoom does not scroll the page;
- no hidden automatic raster upscale beyond native resolution;
- exact overlaps can be spiderfied and individually selected;
- fullscreen preserves bounds and marker alignment;
- imported higher-resolution maps immediately gain more usable native zoom without a frontend rewrite.
