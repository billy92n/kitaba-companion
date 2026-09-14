from reference.story_export import render_story_html
from reference.story_system import EditorialScene


def sample_scene(**overrides):
    base = dict(
        scene_id="s1",
        title="Le seuil",
        kind="revelation",
        canon_revision_start=8,
        canon_revision_end=9,
        prose="Elle ouvre la porte.\nLe silence change.",
        source_event_ids=("e1",),
        participant_entity_ids=("pc",),
        location_entity_id="home",
        illustration_asset_ids=("img-1",),
    )
    base.update(overrides)
    return EditorialScene(**base)


def test_html_export_is_readable_and_traceable_to_scene_revisions():
    html = render_story_html("Chroniques de Kitaba", [sample_scene()])
    assert "<!doctype html>" in html
    assert "Chroniques de Kitaba" in html
    assert 'data-scene-id="s1"' in html
    assert "révisions 8–9" in html
    assert "Elle ouvre la porte." in html
    assert "Kitaba — l’art de façonner votre propre histoire." in html


def test_html_export_escapes_editorial_content_instead_of_executing_it():
    html = render_story_html("<Kitaba>", [sample_scene(title="<script>", prose="<b>pas du HTML</b>")])
    assert "&lt;Kitaba&gt;" in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;pas du HTML&lt;/b&gt;" in html
    assert "<script>" not in html


def test_html_export_can_attach_known_scene_illustrations():
    html = render_story_html(
        "Kitaba",
        [sample_scene()],
        illustration_src_by_asset_id={"img-1": "assets/scene-1.webp"},
    )
    assert 'src="assets/scene-1.webp"' in html
    assert '<img class="scene-image"' in html


def test_missing_illustration_mapping_does_not_break_export():
    html = render_story_html("Kitaba", [sample_scene()], illustration_src_by_asset_id={})
    assert '<img class="scene-image"' not in html


def test_empty_title_is_rejected():
    try:
        render_story_html("", [sample_scene()])
    except ValueError as exc:
        assert "title is required" in str(exc)
    else:
        raise AssertionError("empty title should be rejected")
