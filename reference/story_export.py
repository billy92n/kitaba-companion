"""Reference HTML renderer for Kitaba editorial scenes.

PROPOSAL only. This renderer consumes the non-canonical EditorialScene layer and
never reads or mutates campaign canon itself.
"""

from __future__ import annotations

from html import escape
from typing import Iterable, Mapping

from reference.story_system import EditorialScene, validate_editorial_scene


DEFAULT_CSS = """
body{font-family:Georgia,serif;max-width:760px;margin:0 auto;padding:3rem 1.5rem;line-height:1.7;color:#241f1a;background:#f4efe4}
header{border-bottom:1px solid #b8aa91;margin-bottom:2.5rem}h1{font-size:2.4rem;margin-bottom:.25rem}article{margin:0 0 3.2rem}article h2{margin-bottom:.25rem}.meta{font:12px system-ui;color:#6e6457}.scene-image{max-width:100%;height:auto;border-radius:8px;margin:1rem 0}.prose{white-space:pre-wrap}
""".strip()


def render_story_html(
    title: str,
    scenes: Iterable[EditorialScene],
    *,
    illustration_src_by_asset_id: Mapping[str, str] | None = None,
) -> str:
    if not title.strip():
        raise ValueError("title is required")
    scene_list = list(scenes)
    for scene in scene_list:
        validate_editorial_scene(scene)

    illustration_src_by_asset_id = illustration_src_by_asset_id or {}
    chunks = [
        "<!doctype html>",
        '<html lang="fr"><head><meta charset="utf-8">',
        f"<title>{escape(title)}</title>",
        f"<style>{DEFAULT_CSS}</style></head><body>",
        f"<header><h1>{escape(title)}</h1><p>Kitaba — l’art de façonner votre propre histoire.</p></header>",
    ]

    for scene in scene_list:
        chunks.append(f'<article data-scene-id="{escape(scene.scene_id, quote=True)}">')
        chunks.append(f"<h2>{escape(scene.title)}</h2>")
        chunks.append(
            f'<div class="meta">{escape(scene.kind)} · révisions {scene.canon_revision_start}–{scene.canon_revision_end}</div>'
        )
        for asset_id in scene.illustration_asset_ids:
            src = illustration_src_by_asset_id.get(asset_id)
            if src:
                chunks.append(
                    f'<img class="scene-image" src="{escape(src, quote=True)}" alt="Illustration de {escape(scene.title, quote=True)}">'
                )
        chunks.append(f'<div class="prose">{escape(scene.prose)}</div>')
        chunks.append("</article>")

    chunks.append("</body></html>")
    return "".join(chunks)
