import json
import sqlite3
import tempfile
import uuid
import zipfile
from pathlib import Path

import pytest

from reference.engine import (
    DuplicateUpdate,
    EntityConflict,
    KitabaError,
    KitabaEngine,
    RevisionConflict,
    TimelineConflict,
    ValidationError,
)


def u():
    return str(uuid.uuid4())


@pytest.fixture
def eng(tmp_path):
    e = KitabaEngine(tmp_path / "kitaba.sqlite")
    yield e
    e.close()


def base_update(campaign_id, timeline_id, revision=0, *, update_id=None, operations=None, gm_operations=None, checkpoint=None):
    return {
        "format": "KITABA_UPDATE",
        "protocol_version": 1,
        "campaign_id": campaign_id,
        "timeline_id": timeline_id,
        "update_id": update_id or u(),
        "base_revision": revision,
        "target_revision": revision + 1,
        "game_time": {"set": f"Day 1 {8+revision:02d}:00", "elapsed_minutes": 60 if revision else 0},
        "operations": operations or [],
        "gm_operations": gm_operations or [],
        "journal_entries": [],
        "notifications": [],
        "checkpoint": checkpoint,
        "death": None,
    }


def test_create_campaign(eng):
    cid, tid = eng.create_campaign("Sully")
    row = eng.campaign(cid)
    assert row["current_revision"] == 0
    assert row["current_timeline_id"] == tid


def test_valid_update_advances_revision(eng):
    cid, tid = eng.create_campaign("Sully")
    eid = u()
    up = base_update(cid, tid, operations=[{
        "op": "create", "entity_type": "player_character", "entity_id": eid,
        "data": {"first_name": "Sully", "age": 8}
    }])
    result = eng.apply_update(up)
    assert result.revision == 1
    assert eng.campaign(cid)["current_revision"] == 1
    assert eng.export_context(cid, "PLAYER")["entities"][0]["data"]["first_name"] == "Sully"


def test_duplicate_update_rejected(eng):
    cid, tid = eng.create_campaign("Sully")
    up = base_update(cid, tid)
    eng.apply_update(up)
    with pytest.raises(DuplicateUpdate):
        eng.apply_update(up)


def test_stale_revision_rejected(eng):
    cid, tid = eng.create_campaign("Sully")
    eng.apply_update(base_update(cid, tid))
    stale = base_update(cid, tid, revision=0)
    with pytest.raises(RevisionConflict):
        eng.apply_update(stale)


def test_wrong_timeline_rejected(eng):
    cid, tid = eng.create_campaign("Sully")
    up = base_update(cid, u())
    with pytest.raises(TimelineConflict):
        eng.apply_update(up)


def test_atomic_transaction_rolls_back_first_operation_when_second_fails(eng):
    cid, tid = eng.create_campaign("Sully")
    eid = u()
    missing = u()
    up = base_update(cid, tid, operations=[
        {"op": "create", "entity_type": "item", "entity_id": eid, "data": {"name": "Test"}},
        {"op": "patch", "entity_type": "item", "entity_id": missing, "data": {"name": "Nope"}},
    ])
    with pytest.raises(EntityConflict):
        eng.apply_update(up)
    assert eng.conn.execute("SELECT COUNT(*) FROM entity_documents WHERE campaign_id=?", (cid,)).fetchone()[0] == 0
    assert eng.campaign(cid)["current_revision"] == 0


def test_gm_secret_never_in_player_context(eng):
    cid, tid = eng.create_campaign("Sully")
    player_id, secret_id = u(), u()
    eng.apply_update(base_update(
        cid, tid,
        operations=[{"op":"create","entity_type":"npc","entity_id":player_id,"data":{"known_name":"Person"}}],
        gm_operations=[{"op":"create","entity_type":"npc_truth","entity_id":secret_id,"data":{"real_identity":"SECRET_SENTINEL"}}]
    ))
    player = eng.export_context(cid, "PLAYER")
    full = eng.export_context(cid, "GM_FULL")
    assert "SECRET_SENTINEL" not in json.dumps(player)
    assert "SECRET_SENTINEL" in json.dumps(full)
    assert all(e["visibility"] == "PLAYER" for e in player["entities"])


def test_reveal_creates_separate_player_record_and_keeps_gm_secret(eng):
    cid, tid = eng.create_campaign("Sully")
    secret_id = u()
    eng.apply_update(base_update(
        cid, tid,
        gm_operations=[{"op":"create","entity_type":"aptitude_truth","entity_id":secret_id,"data":{"full":"SECRET_CORE","known_fragment":"spark"}}]
    ))
    reveal_id = u()
    eng.apply_update(base_update(
        cid, tid, revision=1,
        operations=[{
            "op":"reveal","entity_type":"known_aptitude","entity_id":reveal_id,
            "source_gm_entity_id":secret_id,"data":{"observation":"A strange spark"}
        }]
    ))
    player = eng.export_context(cid, "PLAYER")
    full = eng.export_context(cid, "GM_FULL")
    assert "A strange spark" in json.dumps(player)
    assert "SECRET_CORE" not in json.dumps(player)
    assert "SECRET_CORE" in json.dumps(full)


def test_entity_version_conflict_rejected(eng):
    cid, tid = eng.create_campaign("Sully")
    eid = u()
    eng.apply_update(base_update(cid, tid, operations=[{"op":"create","entity_type":"item","entity_id":eid,"data":{"q":1}}]))
    bad = base_update(cid, tid, revision=1, operations=[{
        "op":"patch","entity_type":"item","entity_id":eid,"expected_entity_version":99,"data":{"q":2}
    }])
    with pytest.raises(EntityConflict):
        eng.apply_update(bad)
    assert eng.campaign(cid)["current_revision"] == 1


def test_checkpoint_and_death_rollback_restores_state_but_preserves_dead_resolution(eng):
    cid, tid = eng.create_campaign("Sully")
    char_id = u()
    checkpoint_id = u()
    up1 = base_update(cid, tid, operations=[{
        "op":"create","entity_type":"player_character","entity_id":char_id,"data":{"hp":20,"knowledge":[]}
    }], checkpoint={"id":checkpoint_id,"location":"Home","description":"Safe long rest"})
    eng.apply_update(up1)

    up2 = base_update(cid, tid, revision=1, operations=[{
        "op":"patch","entity_type":"player_character","entity_id":char_id,"expected_entity_version":1,
        "data":{"hp":0,"knowledge":["dead timeline secret"]}
    }])
    up2["death"] = {"occurred": True, "summary": "Test death"}
    eng.apply_update(up2)
    eng.add_dead_resolution(cid, checkpoint_id, "state-A", "action-A", {"same": True}, {"death": True}, {"hp": 0})

    new_rev, new_tid = eng.rollback_death(cid, checkpoint_id, "Test death")
    assert new_rev == 3
    assert new_tid != tid
    assert eng.campaign(cid)["game_time"] == "Day 1 08:00"
    player = eng.export_context(cid, "PLAYER")
    char = next(e for e in player["entities"] if e["id"] == char_id)
    assert char["data"]["hp"] == 20
    assert "dead timeline secret" not in json.dumps(player)
    full = eng.export_context(cid, "GM_FULL")
    assert len(full["dead_timeline_resolutions"]) == 1
    assert full["continuity_metadata"]["parent_timeline_id"] == tid
    assert full["continuity_metadata"]["restored_from_rest_point_id"] == checkpoint_id


def test_old_timeline_update_rejected_after_rollback(eng):
    cid, tid = eng.create_campaign("Sully")
    cp = eng.create_rest_point(cid, location="Home", description="Safe")
    death_update = base_update(cid, tid)
    death_update["death"] = {"occurred": True, "summary": "death"}
    eng.apply_update(death_update)
    _, new_tid = eng.rollback_death(cid, cp, "death")
    assert new_tid != tid
    old_branch_update = base_update(cid, tid, revision=2)
    with pytest.raises(TimelineConflict):
        eng.apply_update(old_branch_update)


def test_technical_backup_is_valid_zip_with_checksum(eng, tmp_path):
    cid, _ = eng.create_campaign("Sully")
    path = eng.create_technical_backup(cid, tmp_path / "backup.kitaba", "manual")
    assert path.exists()
    manifest = KitabaEngine.verify_backup(path)
    assert manifest["format"] == "KITABA_BACKUP"
    with zipfile.ZipFile(path) as zf:
        assert {"campaign.sqlite", "manifest.json"}.issubset(zf.namelist())


def test_context_files_validate_and_player_export_has_no_gm(eng, tmp_path):
    cid, tid = eng.create_campaign("Sully")
    eng.apply_update(base_update(
        cid, tid,
        operations=[{"op":"create","entity_type":"knowledge","entity_id":u(),"data":{"text":"known"}}],
        gm_operations=[{"op":"create","entity_type":"canon_fact","entity_id":u(),"data":{"text":"hidden"}}]
    ))
    p = eng.export_context_file(cid, tmp_path / "player.kitaba-context", "PLAYER")
    g = eng.export_context_file(cid, tmp_path / "full.kitaba-context", "GM_FULL")
    player_context = json.loads(p.read_text())
    gm_context = json.loads(g.read_text())
    assert not any(e.get("data", {}).get("text") == "hidden" for e in player_context["entities"])
    assert any(e.get("data", {}).get("text") == "hidden" for e in gm_context["entities"])


def test_schema_rejects_non_incrementing_target_revision(eng):
    cid, tid = eng.create_campaign("Sully")
    up = base_update(cid, tid)
    up["target_revision"] = 5
    with pytest.raises(ValidationError):
        eng.apply_update(up)


def test_persistence_after_close_and_reopen(tmp_path):
    db = tmp_path / "persist.sqlite"
    e = KitabaEngine(db)
    cid, tid = e.create_campaign("Sully")
    eid = u()
    e.apply_update(base_update(cid, tid, operations=[{"op":"create","entity_type":"item","entity_id":eid,"data":{"name":"Persistent"}}]))
    e.close()
    e2 = KitabaEngine(db)
    try:
        assert e2.campaign(cid)["current_revision"] == 1
        assert "Persistent" in json.dumps(e2.export_context(cid, "PLAYER"))
    finally:
        e2.close()


def test_backup_restore_to_new_database(eng, tmp_path):
    cid, tid = eng.create_campaign("Sully")
    eng.apply_update(base_update(cid, tid, operations=[{"op":"create","entity_type":"knowledge","entity_id":u(),"data":{"text":"survives backup"}}]))
    backup = eng.create_technical_backup(cid, tmp_path / "full.kitaba", "manual")
    restored_db = tmp_path / "restored.sqlite"
    KitabaEngine.restore_backup_to(backup, restored_db)
    restored = KitabaEngine(restored_db)
    try:
        assert restored.campaign(cid)["current_revision"] == 1
        assert "survives backup" in json.dumps(restored.export_context(cid, "PLAYER"))
    finally:
        restored.close()


def test_dead_resolution_can_arrive_via_update_and_is_gm_only(eng):
    cid, tid = eng.create_campaign("Sully")
    checkpoint_id = eng.create_rest_point(cid, location="Home", description="safe")
    resolution_id = u()
    up = base_update(cid, tid)
    up["dead_timeline_resolutions"] = [{
        "id": resolution_id,
        "checkpoint_id": checkpoint_id,
        "state_fingerprint": "state-x",
        "action_fingerprint": "action-x",
        "context": {"secret_condition": "SECRET_RESOLUTION"},
        "result": {"outcome": "death"},
        "consequences": {"hp": 0},
        "notes": None,
    }]
    eng.apply_update(up)
    player = eng.export_context(cid, "PLAYER")
    gm = eng.export_context(cid, "GM_FULL")
    assert "SECRET_RESOLUTION" not in json.dumps(player)
    assert "SECRET_RESOLUTION" in json.dumps(gm)
    assert len(gm["dead_timeline_resolutions"]) == 1


def test_rollback_forbidden_without_confirmed_death(eng):
    cid, _ = eng.create_campaign("Sully")
    cp = eng.create_rest_point(cid, location="Home", description="safe")
    with pytest.raises(Exception, match="no confirmed player death"):
        eng.rollback_death(cid, cp, "cheat attempt")


def test_updates_blocked_after_death_until_rollback(eng):
    cid, tid = eng.create_campaign("Sully")
    cp = eng.create_rest_point(cid, location="Home", description="safe")
    death = base_update(cid, tid)
    death["death"] = {"occurred": True, "summary": "fatal"}
    eng.apply_update(death)
    with pytest.raises(ValidationError, match="awaiting authorized death rollback"):
        eng.apply_update(base_update(cid, tid, revision=1))
    eng.rollback_death(cid, cp, "fatal")
    row = eng.campaign(cid)
    assert row["death_pending"] == 0


def test_immutable_entity_rejects_accidental_change_and_allows_explicit_override(eng):
    cid, tid = eng.create_campaign("Sully")
    eid = u()
    create = base_update(cid, tid, gm_operations=[{
        "op":"create","entity_type":"canon_fact","entity_id":eid,"data":{"truth":"fixed"},"protection":"IMMUTABLE"
    }])
    eng.apply_update(create)
    bad = base_update(cid, tid, revision=1, gm_operations=[{
        "op":"patch","entity_type":"canon_fact","entity_id":eid,"expected_entity_version":1,"data":{"truth":"changed"}
    }])
    with pytest.raises(EntityConflict, match="immutable"):
        eng.apply_update(bad)
    good = base_update(cid, tid, revision=1, gm_operations=[{
        "op":"patch","entity_type":"canon_fact","entity_id":eid,"expected_entity_version":1,"data":{"truth":"changed"},
        "override_immutable":True,"override_reason":"Explicit canon correction"
    }])
    eng.apply_update(good)
    assert "changed" in json.dumps(eng.export_context(cid,"GM_FULL"))


def test_protected_entity_requires_expected_version(eng):
    cid, tid = eng.create_campaign("Sully")
    eid = u()
    eng.apply_update(base_update(cid, tid, operations=[{
        "op":"create","entity_type":"player_character","entity_id":eid,"data":{"name":"Sully"},"protection":"PROTECTED"
    }]))
    bad = base_update(cid, tid, revision=1, operations=[{
        "op":"patch","entity_type":"player_character","entity_id":eid,"data":{"age":9}
    }])
    with pytest.raises(EntityConflict, match="protected"):
        eng.apply_update(bad)


def test_player_links_round_trip_and_gm_links_do_not_leak(eng):
    cid, tid = eng.create_campaign("Sully")
    a, b, secret = u(), u(), u()
    eng.apply_update(base_update(cid, tid,
        operations=[
            {"op":"create","entity_type":"npc","entity_id":a,"data":{"name":"A"}},
            {"op":"create","entity_type":"place","entity_id":b,"data":{"name":"B"}},
        ],
        gm_operations=[{"op":"create","entity_type":"canon_fact","entity_id":secret,"data":{"x":1}}]
    ))
    up = base_update(cid, tid, revision=1)
    up["link_operations"] = [{"op":"link","link_id":u(),"from_entity_id":a,"to_entity_id":b,"link_type":"located_at","data":{}}]
    up["gm_link_operations"] = [{"op":"link","link_id":u(),"from_entity_id":secret,"to_entity_id":a,"link_type":"secret_about","data":{"hidden":"S"}}]
    eng.apply_update(up)
    player = eng.export_context(cid,"PLAYER")
    gm = eng.export_context(cid,"GM_FULL")
    assert len(player["links"]) == 1
    assert len(gm["links"]) == 2
    assert "secret_about" not in json.dumps(player)

def test_full_kitaba_round_trip_scenario(eng, tmp_path):
    cid, tid = eng.create_campaign("Sully — Kitaba Solo")
    pc, npc, rel_visible, rel_hidden, item, rumor, truth, checkpoint = [u() for _ in range(8)]

    up1 = base_update(cid, tid,
        operations=[
            {"op":"create","entity_type":"player_character","entity_id":pc,"protection":"PROTECTED","data":{
                "first_name":"Sully","species":"Humain","age":8,"hp_current":20,"hp_max":20,"mana_current":5,"mana_max":5
            }},
            {"op":"create","entity_type":"npc","entity_id":npc,"data":{"known_name":"Mère"}},
            {"op":"create","entity_type":"relationship","entity_id":rel_visible,"data":{"npc_id":npc,"perception":"semble inquiète"}},
            {"op":"create","entity_type":"inventory_item","entity_id":item,"data":{"name":"Petit couteau","quantity":1}},
            {"op":"create","entity_type":"knowledge","entity_id":rumor,"data":{"subject":"Rumeur","content":"Quelque chose","perceived_type":"rumeur"}},
        ],
        gm_operations=[
            {"op":"create","entity_type":"relationship_truth","entity_id":rel_hidden,"data":{"npc_id":npc,"trust":97,"fear":62}},
            {"op":"create","entity_type":"canon_fact","entity_id":truth,"protection":"IMMUTABLE","data":{"rumor_id":rumor,"truth":False,"reason":"SECRET_REASON"}},
        ],
        checkpoint={"id":checkpoint,"location":"Maison","description":"Repos sûr"}
    )
    up1["game_time"] = {"set":"Jour 1 — 07:30","elapsed_minutes":0}
    eng.apply_update(up1)

    player_context = eng.export_context(cid,"PLAYER")
    full_context = eng.export_context(cid,"GM_FULL")
    assert "SECRET_REASON" not in json.dumps(player_context)
    assert "SECRET_REASON" in json.dumps(full_context)
    assert player_context["last_rest_point"]["id"] == checkpoint

    death_resolution = u()
    up2 = base_update(cid, tid, revision=1, operations=[{
        "op":"patch","entity_type":"player_character","entity_id":pc,"expected_entity_version":1,"data":{"hp_current":0}
    }])
    up2["death"] = {"occurred":True,"summary":"Test fatal"}
    up2["dead_timeline_resolutions"] = [{
        "id":death_resolution,"checkpoint_id":checkpoint,"state_fingerprint":"state-1","action_fingerprint":"action-1",
        "context":{"attempt":"same"},"result":{"death":True},"consequences":{"hp":0},"notes":"anti save-scum"
    }]
    eng.apply_update(up2)
    assert eng.campaign(cid)["death_pending"] == 1

    rev, new_tid = eng.rollback_death(cid, checkpoint, "Test fatal")
    assert rev == 3 and new_tid != tid
    rolled = eng.export_context(cid,"PLAYER")
    pc_state = next(e for e in rolled["entities"] if e["id"] == pc)
    assert pc_state["data"]["hp_current"] == 20
    assert eng.campaign(cid)["death_pending"] == 0
    gm_after = eng.export_context(cid,"GM_FULL")
    assert any(r["id"] == death_resolution for r in gm_after["dead_timeline_resolutions"])

    backup = eng.create_technical_backup(cid, tmp_path / "campaign.kitaba", "e2e")
    restored_db = tmp_path / "restored.sqlite"
    KitabaEngine.restore_backup_to(backup, restored_db)
    restored = KitabaEngine(restored_db)
    try:
        ctx = restored.export_context(cid,"GM_FULL")
        assert ctx["campaign_revision"] == 3
        assert ctx["timeline_id"] == new_tid
        assert "SECRET_REASON" in json.dumps(ctx)
    finally:
        restored.close()


def test_schema_rejects_elapsed_time_without_explicit_set(eng):
    cid, tid = eng.create_campaign("Time validation")
    update = base_update(cid, tid)
    update["game_time"] = {"elapsed_minutes": 15}
    with pytest.raises(ValidationError, match="set"):
        eng.apply_update(update)


def test_death_rollback_only_allows_latest_rest_point(eng):
    cid, tid = eng.create_campaign("Latest checkpoint only")
    first = eng.create_rest_point(cid, location="A", description="Premier")
    # Ensure deterministic ordering when timestamps are close by inserting a second checkpoint after state change.
    update = base_update(cid, tid)
    update["operations"] = [{
        "op": "create", "entity_type": "item", "entity_id": str(uuid.uuid4()), "data": {"name": "token"}
    }]
    eng.apply_update(update)
    second = eng.create_rest_point(cid, location="B", description="Dernier")
    death = base_update(cid, tid, revision=1)
    death["death"] = {"occurred": True, "summary": "test"}
    eng.apply_update(death)
    with pytest.raises(KitabaError, match="latest valid Rest Point"):
        eng.rollback_death(cid, first)
    eng.rollback_death(cid, second)


def test_context_is_self_describing_for_next_chatgpt_update(eng):
    cid, tid = eng.create_campaign("Sully")
    context = eng.export_context(cid, "GM_FULL")
    contract = context["companion_contract"]
    assert context["campaign_name"] == "Sully"
    assert contract["update_format"] == "KITABA_UPDATE"
    assert contract["required_timeline_id"] == tid
    assert contract["next_base_revision"] == 0
    assert contract["next_target_revision"] == 1
    assert "gm_operations" in " ".join(contract["rules"])
    assert "player_character" in contract["ui_entity_types"]["character"]


def test_dead_timeline_history_is_gm_only_and_survives_context_export(eng):
    cid, tid = eng.create_campaign("Dead branch export")
    rp = eng.create_rest_point(cid, location="Maison", description="Repos")
    death = base_update(cid, tid)
    death["operations"] = [{
        "op": "create", "entity_type": "knowledge", "entity_id": u(), "data": {"text": "seen only in dead branch"}
    }]
    death["death"] = {"occurred": True, "summary": "fatal"}
    eng.apply_update(death)
    eng.rollback_death(cid, rp)
    player = eng.export_context(cid, "PLAYER")
    full = eng.export_context(cid, "GM_FULL")
    assert player["dead_timelines"] == []
    assert len(full["dead_timelines"]) == 1
    assert any(
        e.get("data", {}).get("text") == "seen only in dead branch"
        for e in full["dead_timelines"][0]["state_snapshot"]["entities"]
    )


def test_backup_rejects_tampered_database_payload(eng, tmp_path):
    cid, _ = eng.create_campaign("Tamper test")
    backup = eng.create_technical_backup(cid, tmp_path / "good.kitaba", "manual")
    tampered = tmp_path / "tampered.kitaba"
    with zipfile.ZipFile(backup, "r") as src, zipfile.ZipFile(tampered, "w", zipfile.ZIP_DEFLATED) as dst:
        dst.writestr("manifest.json", src.read("manifest.json"))
        dst.writestr("campaign.sqlite", src.read("campaign.sqlite") + b"tamper")
    with pytest.raises(KitabaError, match="checksum"):
        KitabaEngine.verify_backup(tampered)


def test_backup_rejects_future_schema(eng, tmp_path):
    cid, _ = eng.create_campaign("Future schema")
    backup = eng.create_technical_backup(cid, tmp_path / "good.kitaba", "manual")
    future = tmp_path / "future.kitaba"
    with zipfile.ZipFile(backup, "r") as src:
        manifest = json.loads(src.read("manifest.json"))
        db_bytes = src.read("campaign.sqlite")
    manifest["schema_version"] = 999
    with zipfile.ZipFile(future, "w", zipfile.ZIP_DEFLATED) as dst:
        dst.writestr("manifest.json", json.dumps(manifest))
        dst.writestr("campaign.sqlite", db_bytes)
    with pytest.raises(KitabaError, match="newer"):
        KitabaEngine.verify_backup(future)


def test_backup_rejects_non_kitaba_archive(tmp_path):
    bad = tmp_path / "bad.kitaba"
    with zipfile.ZipFile(bad, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("hello.txt", "not a campaign")
    with pytest.raises(KitabaError, match="required files"):
        KitabaEngine.verify_backup(bad)


def test_context_export_revision_tracking_marks_sync_state(eng):
    cid, tid = eng.create_campaign("Sync tracking")
    row = eng.campaign(cid)
    assert row["last_gm_export_revision"] is None
    eng.record_context_export(cid, "GM_FULL")
    row = eng.campaign(cid)
    assert row["last_gm_export_revision"] == 0
    eng.apply_update(base_update(cid, tid))
    row = eng.campaign(cid)
    assert row["current_revision"] == 1
    assert row["last_gm_export_revision"] == 0
    eng.record_context_export(cid, "GM_FULL")
    assert eng.campaign(cid)["last_gm_export_revision"] == 1


def test_player_and_gm_export_tracking_are_independent(eng):
    cid, _ = eng.create_campaign("Separate exports")
    eng.record_context_export(cid, "PLAYER")
    row = eng.campaign(cid)
    assert row["last_player_export_revision"] == 0
    assert row["last_gm_export_revision"] is None


def test_exported_player_and_gm_contexts_validate_against_public_schema(eng):
    cid, tid = eng.create_campaign("Schema round trip")
    visible, hidden = u(), u()
    eng.apply_update(base_update(
        cid,
        tid,
        operations=[{"op":"create","entity_type":"player_character","entity_id":visible,"data":{"name":"Sully"}}],
        gm_operations=[{"op":"create","entity_type":"canon_fact","entity_id":hidden,"data":{"secret":True}}],
    ))
    for mode in ("PLAYER", "GM_FULL"):
        context = eng.export_context(cid, mode)
        errors = list(eng.context_validator.iter_errors(context))
        assert errors == [], [error.message for error in errors]


def test_update_protocol_requires_explicit_player_and_gm_operation_arrays(eng):
    cid, tid = eng.create_campaign("Strict arrays")
    payload = base_update(cid, tid)
    del payload["operations"]
    with pytest.raises(ValidationError):
        eng.apply_update(payload)
    payload = base_update(cid, tid)
    del payload["gm_operations"]
    with pytest.raises(ValidationError):
        eng.apply_update(payload)


def test_latest_rest_point_uses_canonical_revision_not_wall_clock_order(eng):
    cid, tid = eng.create_campaign("Rest point revision order")
    first = eng.create_rest_point(cid, location="A", description="Premier")
    up = base_update(cid, tid)
    up["operations"] = [{"op":"create","entity_type":"item","entity_id":u(),"data":{"name":"token"}}]
    eng.apply_update(up)
    second = eng.create_rest_point(cid, location="B", description="Second")
    # Deliberately make the older canonical checkpoint look newer by wall-clock metadata.
    eng.conn.execute("UPDATE rest_points SET created_at='9999-12-31T23:59:59+00:00' WHERE id=?", (first,))
    eng.conn.execute("UPDATE rest_points SET created_at='2000-01-01T00:00:00+00:00' WHERE id=?", (second,))
    eng.conn.commit()
    ctx = eng.export_context(cid, "PLAYER")
    assert ctx["last_rest_point"]["id"] == second

    death = base_update(cid, tid, revision=1)
    death["death"] = {"occurred": True, "summary": "test"}
    eng.apply_update(death)
    with pytest.raises(KitabaError, match="latest valid Rest Point"):
        eng.rollback_death(cid, first)
    eng.rollback_death(cid, second)


def test_campaign_scoped_backup_does_not_contain_other_campaigns(eng, tmp_path):
    first, _ = eng.create_campaign("First")
    second, _ = eng.create_campaign("Second")
    backup = eng.create_technical_backup(first, tmp_path / "first.kitaba", "manual")
    with tempfile.TemporaryDirectory() as td:
        extracted = Path(td) / "db.sqlite"
        with zipfile.ZipFile(backup, "r") as zf:
            extracted.write_bytes(zf.read("campaign.sqlite"))
        conn = sqlite3.connect(extracted)
        try:
            ids = [row[0] for row in conn.execute("SELECT id FROM campaigns")]
        finally:
            conn.close()
    assert ids == [first]
    assert second not in ids


def test_campaign_restore_merge_preserves_unrelated_campaigns(eng, tmp_path):
    first, first_tid = eng.create_campaign("First")
    second, _ = eng.create_campaign("Second")
    item = u()
    eng.apply_update(base_update(first, first_tid, operations=[{
        "op":"create","entity_type":"item","entity_id":item,"data":{"name":"Before backup"}
    }]))
    backup = eng.create_technical_backup(first, tmp_path / "first.kitaba", "manual")

    # Mutate the current copy after backup; restore must revert only the backed-up campaign.
    up = base_update(first, first_tid, revision=1, operations=[{
        "op":"patch","entity_type":"item","entity_id":item,"expected_entity_version":1,"data":{"name":"After backup"}
    }])
    eng.apply_update(up)
    eng.restore_backup_into_current(backup)

    assert eng.campaign(second)["name"] == "Second"
    ctx = eng.export_context(first, "PLAYER")
    restored_item = next(e for e in ctx["entities"] if e["id"] == item)
    assert restored_item["data"]["name"] == "Before backup"
    assert ctx["campaign_revision"] == 1


def test_import_asset_rejects_non_image_and_accepts_png(eng, tmp_path):
    cid, _ = eng.create_campaign("Sully")
    bad = tmp_path / "bad.txt"
    bad.write_text("not an image", encoding="utf-8")
    with pytest.raises(ValidationError, match="PNG, JPEG and WebP"):
        eng.import_asset(cid, "world_map", bad)

    png = tmp_path / "map.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"kitaba-map-test")
    asset = eng.import_asset(cid, "world_map", png)
    assert asset["kind"] == "world_map"
    assert eng.read_asset(cid, asset["id"]).startswith(b"\x89PNG")
    assert len(eng.list_assets(cid)) == 1


def test_singleton_visual_asset_replaces_previous_file(eng, tmp_path):
    cid, _ = eng.create_campaign("Sully")
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"\x89PNG\r\n\x1a\nFIRST")
    second.write_bytes(b"\x89PNG\r\n\x1a\nSECOND")
    a1 = eng.import_asset(cid, "player_portrait", first)
    old_path = eng.asset_root / a1["relative_path"]
    assert old_path.exists()
    a2 = eng.import_asset(cid, "player_portrait", second)
    assert a1["id"] != a2["id"]
    assert not old_path.exists()
    assets = eng.list_assets(cid)
    assert len(assets) == 1 and assets[0]["id"] == a2["id"]


def test_backup_includes_and_restores_campaign_assets(eng, tmp_path):
    cid, _ = eng.create_campaign("Sully")
    image = tmp_path / "portrait.webp"
    image.write_bytes(b"RIFF" + (12).to_bytes(4, "little") + b"WEBP" + b"ASSETDATA")
    asset = eng.import_asset(cid, "player_portrait", image)
    backup = eng.create_technical_backup(cid, tmp_path / "with-assets.kitaba", "asset-test")

    with zipfile.ZipFile(backup, "r") as zf:
        name = f"assets/{asset['relative_path']}"
        assert name in zf.namelist()
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["files"][name]["sha256"]

    restored_db = tmp_path / "restored" / "kitaba.sqlite"
    KitabaEngine.restore_backup_to(backup, restored_db)
    restored = KitabaEngine(restored_db)
    try:
        restored_asset = restored.list_assets(cid)[0]
        assert restored.read_asset(cid, restored_asset["id"]) == image.read_bytes()
    finally:
        restored.close()


def test_campaign_restore_replaces_only_target_campaign_assets(tmp_path):
    db = tmp_path / "main.sqlite"
    eng = KitabaEngine(db)
    try:
        c1, _ = eng.create_campaign("Sully")
        c2, _ = eng.create_campaign("Other")
        p1 = tmp_path / "sully.png"
        p2 = tmp_path / "other.png"
        p1.write_bytes(b"\x89PNG\r\n\x1a\nSULLY")
        p2.write_bytes(b"\x89PNG\r\n\x1a\nOTHER")
        a1 = eng.import_asset(c1, "player_portrait", p1)
        a2 = eng.import_asset(c2, "player_portrait", p2)
        backup = eng.create_technical_backup(c1, tmp_path / "sully.kitaba", "isolation")

        replacement = tmp_path / "replacement.png"
        replacement.write_bytes(b"\x89PNG\r\n\x1a\nREPLACED")
        eng.import_asset(c1, "player_portrait", replacement)
        other_before = eng.read_asset(c2, a2["id"])

        eng.restore_backup_into_current(backup)
        assert eng.read_asset(c1, a1["id"]) == p1.read_bytes()
        assert eng.read_asset(c2, a2["id"]) == other_before
    finally:
        eng.close()


def test_dead_resolution_export_preserves_source_timeline_and_provenance(eng):
    cid, tid = eng.create_campaign("Sully")
    checkpoint = eng.create_rest_point(cid, location="Home", description="safe")
    rid = eng.add_dead_resolution(
        cid, checkpoint, "state-source", "action-source",
        {"x": 1}, {"outcome": "death"}, {"hp": 0}, "provenance"
    )
    full = eng.export_context(cid, "GM_FULL")
    row = next(r for r in full["dead_timeline_resolutions"] if r["id"] == rid)
    assert row["source_timeline_id"] == tid
    assert "created_at" in row
    assert "source_update_id" in row


def test_manual_player_correction_is_audited_and_advances_revision(eng):
    cid, tid = eng.create_campaign("Manual correction")
    eid = u()
    eng.apply_update(base_update(cid, tid, operations=[{
        "op":"create","entity_type":"player_character","entity_id":eid,"data":{"name":"Sully","age":8}
    }]))
    result = eng.manual_patch_entity(
        cid, eid, {"age": 9}, expected_entity_version=1, reason="Correction de saisie", visibility="PLAYER"
    )
    assert result["campaign_revision"] == 2
    assert result["entity_version"] == 2
    ctx = eng.export_context(cid, "PLAYER")
    entity = next(e for e in ctx["entities"] if e["id"] == eid)
    assert entity["data"]["age"] == 9
    assert ctx["campaign_revision"] == 2
    audit = eng.conn.execute(
        "SELECT event_type,summary,metadata_json FROM audit_log WHERE campaign_id=? ORDER BY created_at DESC LIMIT 1",
        (cid,),
    ).fetchone()
    assert audit["event_type"] == "manual_entity_correction"
    assert "player_character" in audit["summary"]
    assert "Correction de saisie" in audit["metadata_json"]


def test_manual_gm_correction_does_not_leak_secret_in_player_context_or_audit_summary(eng):
    cid, tid = eng.create_campaign("GM correction")
    secret = "THE_HIDDEN_APTITUDE_NAME"
    eid = u()
    eng.apply_update(base_update(cid, tid, gm_operations=[{
        "op":"create","entity_type":"aptitude_truth","entity_id":eid,"data":{"name":secret,"stage":1}
    }]))
    eng.manual_patch_entity(
        cid, eid, {"stage": 2}, expected_entity_version=1, reason=f"Fix {secret}", visibility="GM"
    )
    player = eng.export_context(cid, "PLAYER")
    assert secret not in json.dumps(player)
    audit = eng.conn.execute(
        "SELECT summary,metadata_json FROM audit_log WHERE campaign_id=? AND event_type='manual_entity_correction' ORDER BY created_at DESC LIMIT 1",
        (cid,),
    ).fetchone()
    assert secret not in audit["summary"]
    assert secret not in audit["metadata_json"]
    assert eid not in audit["metadata_json"]


def test_manual_correction_rejects_stale_version_and_death_pending(eng):
    cid, tid = eng.create_campaign("Manual guards")
    eid = u()
    eng.apply_update(base_update(cid, tid, operations=[{
        "op":"create","entity_type":"item","entity_id":eid,"data":{"name":"A"}
    }]))
    with pytest.raises(EntityConflict, match="version conflict"):
        eng.manual_patch_entity(cid, eid, {"name":"B"}, expected_entity_version=99, reason="test")

    death = base_update(cid, tid, revision=1)
    death["death"] = {"occurred": True, "summary": "test"}
    eng.apply_update(death)
    with pytest.raises(ValidationError, match="death rollback"):
        eng.manual_patch_entity(cid, eid, {"name":"C"}, expected_entity_version=1, reason="test")


def test_manual_correction_requires_explicit_immutable_override(eng):
    cid, tid = eng.create_campaign("Immutable correction")
    eid = u()
    eng.apply_update(base_update(cid, tid, operations=[{
        "op":"create","entity_type":"canon_display","entity_id":eid,"data":{"value":1},"protection":"IMMUTABLE"
    }]))
    with pytest.raises(EntityConflict, match="immutable"):
        eng.manual_patch_entity(cid, eid, {"value":2}, expected_entity_version=1, reason="typo")
    result = eng.manual_patch_entity(
        cid, eid, {"value":2}, expected_entity_version=1, reason="typo", override_immutable=True
    )
    assert result["entity_version"] == 2


def test_campaign_archive_and_restore(eng):
    campaign_id, _ = eng.create_campaign("Archive me")
    eng.archive_campaign(campaign_id)
    row = eng.campaign(campaign_id)
    assert row["archived_at"] is not None
    archived = eng.list_archived_campaigns()
    assert any(c["id"] == campaign_id for c in archived)

    eng.restore_archived_campaign(campaign_id)
    assert eng.campaign(campaign_id)["archived_at"] is None
    assert all(c["id"] != campaign_id for c in eng.list_archived_campaigns())


def test_permanent_delete_requires_exact_name_and_removes_assets(eng, tmp_path):
    campaign_id, _ = eng.create_campaign("Delete exactly")
    png = tmp_path / "portrait.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"fake-png-payload")
    asset = eng.import_asset(campaign_id, "player_portrait", png)
    managed = eng.asset_root / asset["relative_path"]
    assert managed.exists()

    with pytest.raises(Exception):
        eng.delete_campaign_permanently(campaign_id, "wrong name")
    assert eng.campaign(campaign_id)

    eng.delete_campaign_permanently(campaign_id, "Delete exactly")
    assert eng.conn.execute("SELECT 1 FROM campaigns WHERE id=?", (campaign_id,)).fetchone() is None
    assert not (eng.asset_root / campaign_id).exists()


def test_integrity_report_is_healthy_for_valid_campaign(eng):
    campaign_id, timeline_id = eng.create_campaign("Healthy")
    report = eng.integrity_report(campaign_id)
    assert report["ok"] is True
    assert report["campaign_id"] == campaign_id
    assert all(check["ok"] for check in report["checks"])


def test_integrity_report_detects_tampered_rest_point(eng):
    campaign_id, timeline_id = eng.create_campaign("Tamper")
    update = base_update(campaign_id, timeline_id, 0)
    update["checkpoint"] = {
        "id": str(uuid.uuid4()),
        "location": "Maison",
        "description": "Repos",
    }
    eng.apply_update(update)
    eng.conn.execute(
        "UPDATE rest_points SET snapshot_json='{}' WHERE campaign_id=?",
        (campaign_id,),
    )
    eng.conn.commit()
    report = eng.integrity_report(campaign_id)
    by_code = {c["code"]: c for c in report["checks"]}
    assert report["ok"] is False
    assert by_code["rest_point_hashes"]["ok"] is False


def test_integrity_report_detects_missing_asset(eng, tmp_path):
    campaign_id, _ = eng.create_campaign("Missing asset")
    png = tmp_path / "map.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"map")
    asset = eng.import_asset(campaign_id, "world_map", png)
    (eng.asset_root / asset["relative_path"]).unlink()
    report = eng.integrity_report(campaign_id)
    by_code = {c["code"]: c for c in report["checks"]}
    assert report["ok"] is False
    assert by_code["assets"]["ok"] is False


def test_registered_asset_path_cannot_escape_campaign_directory(eng, tmp_path):
    campaign_id, _ = eng.create_campaign("Path guard")
    asset_id = u()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"\x89PNG\r\n\x1a\n" + b"secret")
    eng.conn.execute(
        "INSERT INTO assets(id,campaign_id,kind,relative_path,mime_type,sha256,created_at) VALUES (?,?,?,?,?,?,?)",
        (asset_id, campaign_id, "other_image", "../outside.png", "image/png", None, "2026-01-01T00:00:00+00:00"),
    )
    eng.conn.commit()
    with pytest.raises(ValidationError):
        eng.read_asset(campaign_id, asset_id)
    report = eng.integrity_report(campaign_id)
    assert report["ok"] is False
    assert next(c for c in report["checks"] if c["code"] == "assets")["ok"] is False


def test_world_state_contract_and_hidden_persistence(eng):
    cid, tid = eng.create_campaign("World state")
    secret_id = u()
    eng.apply_update(base_update(
        cid, tid,
        gm_operations=[{
            "op": "create",
            "entity_type": "faction",
            "entity_id": secret_id,
            "data": {"name": "Hidden faction", "status": "SECRET_WORLD_SENTINEL"},
        }],
    ))
    player = eng.export_context(cid, "PLAYER")
    full = eng.export_context(cid, "GM_FULL")
    expected = {"faction", "organization", "settlement", "state", "market", "economy_state", "conflict", "world_event", "environment_state", "resource_state", "infrastructure", "law", "political_state"}
    assert expected <= set(full["companion_contract"]["ui_entity_types"]["world"])
    assert "SECRET_WORLD_SENTINEL" not in json.dumps(player)
    assert "SECRET_WORLD_SENTINEL" in json.dumps(full)
