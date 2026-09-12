from __future__ import annotations

import copy
import hashlib
import json
import os
import sqlite3
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = Path(__file__).with_name("schema.sql")
UPDATE_SCHEMA = ROOT / "protocols" / "kitaba_update.schema.json"
CONTEXT_SCHEMA = ROOT / "protocols" / "kitaba_context.schema.json"
SCHEMA_VERSION = 4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """JSON Merge Patch-like merge: null removes a key, nested objects merge."""
    out = copy.deepcopy(base)
    for key, value in patch.items():
        if value is None:
            out.pop(key, None)
        elif isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


@dataclass(frozen=True)
class ApplyResult:
    revision: int
    timeline_id: str
    update_id: str


class KitabaError(RuntimeError):
    pass


class ValidationError(KitabaError):
    pass


class RevisionConflict(KitabaError):
    pass


class DuplicateUpdate(KitabaError):
    pass


class TimelineConflict(KitabaError):
    pass


class EntityConflict(KitabaError):
    pass


class KitabaEngine:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.asset_root = self.db_path.parent / "assets"
        self.asset_root.mkdir(parents=True, exist_ok=True)
        self._load_validators()
        self._migrate()

    def close(self) -> None:
        self.conn.close()

    def _load_validators(self) -> None:
        with UPDATE_SCHEMA.open("r", encoding="utf-8") as f:
            self.update_validator = Draft202012Validator(json.load(f), format_checker=FormatChecker())
        with CONTEXT_SCHEMA.open("r", encoding="utf-8") as f:
            self.context_validator = Draft202012Validator(json.load(f), format_checker=FormatChecker())

    def _migrate(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        migrations = [
            (1, SCHEMA_SQL),
            (2, Path(__file__).with_name("migration_v2.sql")),
            (3, Path(__file__).with_name("migration_v3.sql")),
            (4, Path(__file__).with_name("migration_v4.sql")),
        ]
        for version, path in migrations:
            applied = self.conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version=?", (version,)
            ).fetchone()
            if not applied:
                self.conn.executescript(path.read_text(encoding="utf-8"))
                self.conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (version, utc_now()),
                )
        self.conn.commit()

    def create_campaign(self, name: str, campaign_id: str | None = None, timeline_id: str | None = None) -> tuple[str, str]:
        campaign_id = campaign_id or str(uuid.uuid4())
        timeline_id = timeline_id or str(uuid.uuid4())
        now = utc_now()
        with self.conn:
            self.conn.execute(
                "INSERT INTO campaigns(id,name,current_revision,current_timeline_id,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                (campaign_id, name, 0, timeline_id, now, now),
            )
            self.conn.execute(
                "INSERT INTO timelines(id,campaign_id,status,started_revision,created_at) VALUES (?,?,?,?,?)",
                (timeline_id, campaign_id, "ACTIVE", 0, now),
            )
            self._audit(campaign_id, timeline_id, "campaign_created", "Campaign created", {})
        return campaign_id, timeline_id

    def campaign(self, campaign_id: str) -> sqlite3.Row:
        row = self.conn.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
        if not row:
            raise KitabaError(f"Unknown campaign {campaign_id}")
        return row

    def _managed_asset_path(self, campaign_id: str, relative_path: str) -> Path:
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != campaign_id:
            raise ValidationError("Unsafe registered asset path")
        return self.asset_root / relative

    def import_asset(self, campaign_id: str, kind: str, source_path: str | Path) -> dict[str, Any]:
        """Copy a campaign asset into Kitaba-managed storage and index it in SQLite.

        The reference implementation deliberately supports image assets only because
        these are the only runtime assets required by V1 (world map / portraits).
        """
        self.campaign(campaign_id)
        if kind not in {"world_map", "player_portrait", "npc_portrait", "other_image"}:
            raise ValidationError(f"Unsupported asset kind: {kind}")
        source = Path(source_path)
        if not source.is_file():
            raise ValidationError("Asset file not found")
        data = source.read_bytes()
        if len(data) > 25 * 1024 * 1024:
            raise ValidationError("Asset file is too large")

        mime: str
        ext: str
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            mime, ext = "image/png", ".png"
        elif data.startswith(b"\xff\xd8\xff"):
            mime, ext = "image/jpeg", ".jpg"
        elif len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            mime, ext = "image/webp", ".webp"
        else:
            raise ValidationError("Only PNG, JPEG and WebP image assets are accepted")

        asset_id = str(uuid.uuid4())
        relative = f"{campaign_id}/{asset_id}{ext}"
        destination = self.asset_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        try:
            with self.conn:
                # Singleton visual roles replace the previous active asset for the
                # same campaign while retaining only the new managed file.
                if kind in {"world_map", "player_portrait"}:
                    old = self.conn.execute(
                        "SELECT id,relative_path FROM assets WHERE campaign_id=? AND kind=?",
                        (campaign_id, kind),
                    ).fetchall()
                    self.conn.execute("DELETE FROM assets WHERE campaign_id=? AND kind=?", (campaign_id, kind))
                    for row in old:
                        old_path = self.asset_root / row["relative_path"]
                        if old_path.exists():
                            old_path.unlink()
                self.conn.execute(
                    "INSERT INTO assets(id,campaign_id,kind,relative_path,mime_type,sha256,created_at) VALUES (?,?,?,?,?,?,?)",
                    (asset_id, campaign_id, kind, relative, mime, digest, utc_now()),
                )
                campaign = self.campaign(campaign_id)
                self._audit(campaign_id, campaign["current_timeline_id"], "asset_imported", f"Imported {kind} asset", {"asset_id": asset_id, "kind": kind})
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return {"id": asset_id, "campaign_id": campaign_id, "kind": kind, "relative_path": relative, "mime_type": mime, "sha256": digest}

    def list_assets(self, campaign_id: str) -> list[dict[str, Any]]:
        self.campaign(campaign_id)
        return [dict(r) for r in self.conn.execute(
            "SELECT id,campaign_id,kind,relative_path,mime_type,sha256,created_at FROM assets WHERE campaign_id=? ORDER BY created_at DESC",
            (campaign_id,),
        ).fetchall()]

    def read_asset(self, campaign_id: str, asset_id: str) -> bytes:
        row = self.conn.execute(
            "SELECT relative_path,sha256 FROM assets WHERE campaign_id=? AND id=?",
            (campaign_id, asset_id),
        ).fetchone()
        if not row:
            raise KitabaError("Unknown asset")
        path = self._managed_asset_path(campaign_id, row["relative_path"])
        data = path.read_bytes()
        if row["sha256"] and hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise KitabaError("Asset checksum mismatch")
        return data

    def validate_update(self, payload: dict[str, Any]) -> None:
        errors = sorted(self.update_validator.iter_errors(payload), key=lambda e: list(e.path))
        if errors:
            details = "; ".join(f"{'.'.join(map(str,e.path)) or '<root>'}: {e.message}" for e in errors[:10])
            raise ValidationError(details)
        if payload["target_revision"] != payload["base_revision"] + 1:
            raise ValidationError("target_revision must equal base_revision + 1")

    def apply_update(self, payload: dict[str, Any]) -> ApplyResult:
        self.validate_update(payload)
        campaign_id = payload["campaign_id"]
        update_id = payload["update_id"]
        timeline_id = payload["timeline_id"]
        raw = stable_json(payload)

        try:
            self.conn.execute("BEGIN IMMEDIATE")
            campaign = self.conn.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
            if not campaign:
                raise KitabaError(f"Unknown campaign {campaign_id}")
            if campaign["death_pending"]:
                raise ValidationError("Campaign is awaiting authorized death rollback")
            if self.conn.execute("SELECT 1 FROM applied_updates WHERE update_id=?", (update_id,)).fetchone():
                raise DuplicateUpdate(update_id)
            if campaign["current_revision"] != payload["base_revision"]:
                raise RevisionConflict(
                    f"Expected base_revision {campaign['current_revision']}, got {payload['base_revision']}"
                )
            if campaign["current_timeline_id"] != timeline_id:
                raise TimelineConflict(
                    f"Expected timeline {campaign['current_timeline_id']}, got {timeline_id}"
                )

            for op in payload["operations"]:
                self._apply_operation(campaign_id, update_id, "PLAYER", op)
            for op in payload["gm_operations"]:
                self._apply_operation(campaign_id, update_id, "GM", op)
            for op in payload.get("link_operations", []):
                self._apply_link_operation(campaign_id, update_id, "PLAYER", op)
            for op in payload.get("gm_link_operations", []):
                self._apply_link_operation(campaign_id, update_id, "GM", op)
            for doc in payload.get("journal_entries", []):
                op = {
                    "op": "create",
                    "entity_type": doc["entity_type"],
                    "entity_id": doc["entity_id"],
                    "data": doc["data"],
                }
                self._apply_operation(campaign_id, update_id, "PLAYER", op)
            for resolution in payload.get("dead_timeline_resolutions", []):
                self.conn.execute(
                    "INSERT INTO dead_timeline_resolutions(id,campaign_id,source_timeline_id,checkpoint_id,state_fingerprint,action_fingerprint,context_json,result_json,consequences_json,source_update_id,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        resolution["id"], campaign_id, timeline_id, resolution.get("checkpoint_id"),
                        resolution["state_fingerprint"], resolution["action_fingerprint"],
                        stable_json(resolution["context"]), stable_json(resolution["result"]),
                        stable_json(resolution["consequences"]), update_id, resolution.get("notes"), utc_now(),
                    ),
                )

            new_game_time = campaign["game_time"]
            game_time = payload.get("game_time")
            if game_time and game_time.get("set") is not None:
                new_game_time = game_time["set"]

            now = utc_now()
            self.conn.execute(
                "INSERT INTO applied_updates(update_id,campaign_id,timeline_id,base_revision,target_revision,payload_sha256,applied_at) VALUES (?,?,?,?,?,?,?)",
                (
                    update_id,
                    campaign_id,
                    timeline_id,
                    payload["base_revision"],
                    payload["target_revision"],
                    sha256_text(raw),
                    now,
                ),
            )
            death = payload.get("death")
            death_pending = 1 if death and death.get("occurred") is True else 0
            death_summary = death.get("summary") if death_pending else None
            self.conn.execute(
                "UPDATE campaigns SET current_revision=?, game_time=?, last_update_id=?, updated_at=?, death_pending=?, death_summary=? WHERE id=?",
                (payload["target_revision"], new_game_time, update_id, now, death_pending, death_summary, campaign_id),
            )

            if payload.get("checkpoint"):
                cp = payload["checkpoint"]
                self._create_rest_point_in_tx(
                    campaign_id,
                    cp["id"],
                    cp.get("location"),
                    cp.get("description", ""),
                    update_id,
                )

            self._audit(
                campaign_id,
                timeline_id,
                "kitaba_update_applied",
                f"Applied update at revision {payload['target_revision']}",
                {"update_id": update_id, "gm_operation_count": len(payload["gm_operations"])},
            )
            self.conn.commit()
            return ApplyResult(payload["target_revision"], timeline_id, update_id)
        except Exception:
            self.conn.rollback()
            raise

    def _apply_operation(self, campaign_id: str, update_id: str, visibility: str, op: dict[str, Any]) -> None:
        op_name = op["op"]
        entity_id = op["entity_id"]
        entity_type = op["entity_type"]
        row = self.conn.execute(
            "SELECT * FROM entity_documents WHERE campaign_id=? AND id=?",
            (campaign_id, entity_id),
        ).fetchone()
        now = utc_now()

        if op_name == "create":
            if row:
                raise EntityConflict(f"Entity already exists: {entity_id}")
            protection = op.get("protection") or "NORMAL"
            self.conn.execute(
                "INSERT INTO entity_documents(id,campaign_id,entity_type,visibility,entity_version,data_json,protection,created_by_update_id,updated_by_update_id,created_at,updated_at) VALUES (?,?,?,?,1,?,?,?,?,?,?)",
                (entity_id, campaign_id, entity_type, visibility, stable_json(op["data"]), protection, update_id, update_id, now, now),
            )
            return

        if op_name == "reveal":
            if visibility != "PLAYER":
                raise EntityConflict("reveal may only create player-facing data")
            source_id = op.get("source_gm_entity_id")
            source = self.conn.execute(
                "SELECT 1 FROM entity_documents WHERE campaign_id=? AND id=? AND visibility='GM' AND archived=0",
                (campaign_id, source_id),
            ).fetchone()
            if not source:
                raise EntityConflict("Reveal source GM entity does not exist")
            if row:
                protection = row["protection"]
                if protection == "IMMUTABLE":
                    if op.get("override_immutable") is not True or not str(op.get("override_reason") or "").strip():
                        raise EntityConflict("immutable entity requires explicit override with reason")
                if protection == "PROTECTED" and op.get("expected_entity_version") is None:
                    raise EntityConflict("protected entity requires expected_entity_version")
                self._check_expected_version(row, op)
                data = deep_merge(json.loads(row["data_json"]), op["data"])
                next_protection = op.get("protection") or protection
                self.conn.execute(
                    "UPDATE entity_documents SET data_json=?,protection=?,entity_version=entity_version+1,updated_by_update_id=?,updated_at=? WHERE campaign_id=? AND id=?",
                    (stable_json(data), next_protection, update_id, now, campaign_id, entity_id),
                )
            else:
                self.conn.execute(
                    "INSERT INTO entity_documents(id,campaign_id,entity_type,visibility,entity_version,data_json,created_by_update_id,updated_by_update_id,created_at,updated_at) VALUES (?,?,?,?,1,?,?,?,?,?)",
                    (entity_id, campaign_id, entity_type, "PLAYER", stable_json(op["data"]), update_id, update_id, now, now),
                )
            return

        if not row:
            raise EntityConflict(f"Entity does not exist: {entity_id}")
        protection = row["protection"]
        if protection == "IMMUTABLE":
            if op.get("override_immutable") is not True or not str(op.get("override_reason") or "").strip():
                raise EntityConflict("immutable entity requires explicit override with reason")
        if protection == "PROTECTED" and op.get("expected_entity_version") is None:
            raise EntityConflict("protected entity requires expected_entity_version")
        if row["visibility"] != visibility:
            raise EntityConflict("Operation scope does not match existing entity visibility")
        if row["entity_type"] != entity_type:
            raise EntityConflict("entity_type cannot change")
        self._check_expected_version(row, op)

        if op_name == "replace":
            data = op["data"]
            next_protection = op.get("protection") or protection
            self.conn.execute(
                "UPDATE entity_documents SET data_json=?,protection=?,entity_version=entity_version+1,archived=0,updated_by_update_id=?,updated_at=? WHERE campaign_id=? AND id=?",
                (stable_json(data), next_protection, update_id, now, campaign_id, entity_id),
            )
        elif op_name == "patch":
            data = deep_merge(json.loads(row["data_json"]), op["data"])
            next_protection = op.get("protection") or protection
            self.conn.execute(
                "UPDATE entity_documents SET data_json=?,protection=?,entity_version=entity_version+1,updated_by_update_id=?,updated_at=? WHERE campaign_id=? AND id=?",
                (stable_json(data), next_protection, update_id, now, campaign_id, entity_id),
            )
        elif op_name == "archive":
            self.conn.execute(
                "UPDATE entity_documents SET archived=1,entity_version=entity_version+1,updated_by_update_id=?,updated_at=? WHERE campaign_id=? AND id=?",
                (update_id, now, campaign_id, entity_id),
            )
        else:
            raise EntityConflict(f"Unsupported operation {op_name}")

    def _apply_link_operation(self, campaign_id: str, update_id: str, visibility: str, op: dict[str, Any]) -> None:
        now = utc_now()
        link_id = op["link_id"]
        row = self.conn.execute("SELECT * FROM entity_links WHERE campaign_id=? AND id=?", (campaign_id, link_id)).fetchone()
        if op["op"] == "unlink":
            if not row or row["visibility"] != visibility:
                raise EntityConflict("link not found or visibility mismatch")
            self.conn.execute(
                "UPDATE entity_links SET archived=1,updated_by_update_id=?,updated_at=? WHERE campaign_id=? AND id=?",
                (update_id, now, campaign_id, link_id),
            )
            return
        if row:
            raise EntityConflict("link already exists")
        from_id, to_id = op["from_entity_id"], op["to_entity_id"]
        refs = self.conn.execute(
            "SELECT id,visibility FROM entity_documents WHERE campaign_id=? AND id IN (?,?) AND archived=0",
            (campaign_id, from_id, to_id),
        ).fetchall()
        expected_count = 1 if from_id == to_id else 2
        if len(refs) != expected_count:
            raise EntityConflict("link references unknown entity")
        if visibility == "PLAYER" and any(r["visibility"] != "PLAYER" for r in refs):
            raise EntityConflict("player link cannot reference GM-only entity")
        self.conn.execute(
            "INSERT INTO entity_links(id,campaign_id,from_entity_id,to_entity_id,link_type,visibility,data_json,archived,created_by_update_id,updated_by_update_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,0,?,?,?,?)",
            (link_id, campaign_id, from_id, to_id, op["link_type"], visibility, stable_json(op.get("data") or {}), update_id, update_id, now, now),
        )

    @staticmethod
    def _check_expected_version(row: sqlite3.Row, op: dict[str, Any]) -> None:
        expected = op.get("expected_entity_version")
        if expected is not None and row["entity_version"] != expected:
            raise EntityConflict(
                f"Entity version conflict: expected {expected}, actual {row['entity_version']}"
            )

    def _entity_export(self, campaign_id: str, include_gm: bool) -> list[dict[str, Any]]:
        if include_gm:
            rows = self.conn.execute(
                "SELECT * FROM entity_documents WHERE campaign_id=? AND archived=0 ORDER BY entity_type,id",
                (campaign_id,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM entity_documents WHERE campaign_id=? AND archived=0 AND visibility='PLAYER' ORDER BY entity_type,id",
                (campaign_id,),
            ).fetchall()
        return [
            {
                "id": r["id"],
                "entity_type": r["entity_type"],
                "visibility": r["visibility"],
                "entity_version": r["entity_version"],
                "protection": r["protection"],
                "data": json.loads(r["data_json"]),
            }
            for r in rows
        ]

    def export_context(self, campaign_id: str, mode: str = "GM_FULL") -> dict[str, Any]:
        if mode not in {"PLAYER", "GM_FULL"}:
            raise ValueError("mode must be PLAYER or GM_FULL")
        campaign = self.campaign(campaign_id)
        timeline = self.conn.execute(
            "SELECT * FROM timelines WHERE id=?", (campaign["current_timeline_id"],)
        ).fetchone()
        rest = self.conn.execute(
            "SELECT id,snapshot_revision,game_time,location,description,created_at FROM rest_points WHERE campaign_id=? AND invalidated_at IS NULL ORDER BY snapshot_revision DESC, created_at DESC, rowid DESC LIMIT 1",
            (campaign_id,),
        ).fetchone()

        exported_entities = self._entity_export(campaign_id, include_gm=(mode == "GM_FULL"))
        exported_links = [dict(r) for r in self.conn.execute(
            "SELECT * FROM entity_links WHERE campaign_id=? AND archived=0" + ("" if mode == "GM_FULL" else " AND visibility='PLAYER'") + " ORDER BY id",
            (campaign_id,),
        ).fetchall()]
        export_state_sha256 = sha256_text(stable_json({
            "revision": campaign["current_revision"],
            "timeline_id": campaign["current_timeline_id"],
            "game_time": campaign["game_time"],
            "entities": exported_entities,
            "links": exported_links,
        }))

        context = {
            "format": "KITABA_CONTEXT",
            "protocol_version": 1,
            "mode": mode,
            "campaign_id": campaign_id,
            "campaign_name": campaign["name"],
            "campaign_revision": campaign["current_revision"],
            "timeline_id": campaign["current_timeline_id"],
            "exported_at": utc_now(),
            "game_time": campaign["game_time"],
            "death_pending": bool(campaign["death_pending"]),
            "death_summary": campaign["death_summary"],
            "entities": exported_entities,
            "links": exported_links,
            "last_rest_point": dict(rest) if rest else None,
            "dead_timelines": [],
            "dead_timeline_resolutions": [],
            "canon_facts": [],
            "companion_contract": {
                "update_format": "KITABA_UPDATE",
                "update_protocol_version": 1,
                "next_base_revision": campaign["current_revision"],
                "next_target_revision": campaign["current_revision"] + 1,
                "required_timeline_id": campaign["current_timeline_id"],
                "supported_operations": ["create", "replace", "patch", "archive", "reveal"],
                "ui_entity_types": {
                    "character": ["player_character", "characteristic", "specialized_stat", "injury", "status_effect", "awakening"],
                    "skills": ["skill", "mastery"],
                    "magic": ["magic", "spell", "affinity", "invocation", "contract", "enchantment", "known_aptitude"],
                    "inventory": ["item", "inventory_item", "equipment", "wallet", "currency", "debt"],
                    "relations": ["npc", "relationship", "reputation"],
                    "journal": ["journal_entry"],
                    "missions": ["mission", "quest"],
                    "knowledge": ["knowledge", "rumor", "belief"],
                    "map": ["place", "map_marker", "map", "current_location"],
                    "timeline": ["timeline_event", "historical_event"],
                    "adventurer_card": ["adventurer_card", "evaluation", "certification"],
                    "gm": ["canon_fact"]
                },
                "rules": [
                    "Use campaign_id, required_timeline_id and next_base_revision exactly as exported.",
                    "target_revision must equal base_revision + 1.",
                    "Use operations for player-visible knowledge and gm_operations for hidden canonical truth.",
                    "Never expose hidden truth by copying it into a player operation; reveal only the partial information the character actually learns.",
                    "The Companion never advances time itself. When time advances, provide an explicit game_time.set; elapsed_minutes is informational and requires set.",
                    "Create checkpoint only after a sufficiently safe completed long rest validated by the GM.",
                    "Set death.occurred=true only for confirmed player death. After death, no further update is accepted until Companion rollback.",
                    "Store repeated dead-timeline material resolutions in dead_timeline_resolutions with stable fingerprints."
                ]
            },
            "continuity_metadata": {
                "schema_version": SCHEMA_VERSION,
                "last_update_id": campaign["last_update_id"],
                "parent_timeline_id": timeline["parent_timeline_id"] if timeline else None,
                "restored_from_rest_point_id": timeline["restored_from_rest_point_id"] if timeline else None,
                "export_state_sha256": export_state_sha256,
            },
        }
        if mode == "GM_FULL":
            context["dead_timelines"] = [
                {
                    "timeline_id": r["timeline_id"],
                    "died_at_revision": r["died_at_revision"],
                    "death_summary": r["death_summary"],
                    "state_snapshot": json.loads(r["state_snapshot_json"]),
                    "rolled_back_to_rest_point_id": r["rolled_back_to_rest_point_id"],
                    "created_at": r["created_at"],
                }
                for r in self.conn.execute(
                    "SELECT * FROM dead_timelines WHERE campaign_id=? ORDER BY created_at",
                    (campaign_id,),
                ).fetchall()
            ]
            context["dead_timeline_resolutions"] = [
                {
                    "id": r["id"],
                    "source_timeline_id": r["source_timeline_id"],
                    "checkpoint_id": r["checkpoint_id"],
                    "state_fingerprint": r["state_fingerprint"],
                    "action_fingerprint": r["action_fingerprint"],
                    "context": json.loads(r["context_json"]),
                    "result": json.loads(r["result_json"]),
                    "consequences": json.loads(r["consequences_json"]),
                    "source_update_id": r["source_update_id"],
                    "notes": r["notes"],
                    "created_at": r["created_at"],
                }
                for r in self.conn.execute(
                    "SELECT * FROM dead_timeline_resolutions WHERE campaign_id=? ORDER BY created_at",
                    (campaign_id,),
                ).fetchall()
            ]
            context["canon_facts"] = [e for e in context["entities"] if e["entity_type"] == "canon_fact" and e["visibility"] == "GM"]

        errors = list(self.context_validator.iter_errors(context))
        if errors:
            raise ValidationError("Generated KITABA_CONTEXT failed schema: " + "; ".join(e.message for e in errors[:5]))
        return context

    def export_context_file(self, campaign_id: str, output_path: str | Path, mode: str = "GM_FULL") -> Path:
        output_path = Path(output_path)
        output_path.write_text(json.dumps(self.export_context(campaign_id, mode), ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


    def record_context_export(self, campaign_id: str, mode: str) -> None:
        if mode not in {"PLAYER", "GM_FULL"}:
            raise ValueError("mode must be PLAYER or GM_FULL")
        campaign = self.campaign(campaign_id)
        now = utc_now()
        if mode == "GM_FULL":
            sql = "UPDATE campaigns SET last_gm_export_revision=?,last_gm_export_at=? WHERE id=?"
        else:
            sql = "UPDATE campaigns SET last_player_export_revision=?,last_player_export_at=? WHERE id=?"
        with self.conn:
            self.conn.execute(sql, (campaign["current_revision"], now, campaign_id))

    def manual_patch_entity(
        self,
        campaign_id: str,
        entity_id: str,
        patch: dict[str, Any],
        *,
        expected_entity_version: int,
        reason: str,
        visibility: str = "PLAYER",
        override_immutable: bool = False,
    ) -> dict[str, Any]:
        """Apply an explicit, audited local correction outside KITABA_UPDATE.

        Manual corrections are intentionally exceptional. They advance the canonical
        campaign revision so the next ChatGPT export/update cannot silently ignore
        the local change. GM corrections never place secret content in the normal
        audit summary/metadata.
        """
        if visibility not in {"PLAYER", "GM"}:
            raise ValidationError("visibility must be PLAYER or GM")
        if not isinstance(patch, dict) or not patch:
            raise ValidationError("manual patch must be a non-empty object")
        if not isinstance(expected_entity_version, int) or expected_entity_version < 1:
            raise ValidationError("expected_entity_version must be a positive integer")
        if not isinstance(reason, str) or not reason.strip():
            raise ValidationError("manual correction requires a reason")

        correction_id = str(uuid.uuid4())
        now = utc_now()
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            campaign = self.conn.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
            if not campaign:
                raise KitabaError(f"Unknown campaign {campaign_id}")
            if campaign["death_pending"]:
                raise ValidationError("Manual correction is blocked while death rollback is pending")

            row = self.conn.execute(
                "SELECT * FROM entity_documents WHERE campaign_id=? AND id=? AND archived=0",
                (campaign_id, entity_id),
            ).fetchone()
            if not row:
                raise EntityConflict(f"Entity does not exist: {entity_id}")
            if row["visibility"] != visibility:
                raise EntityConflict("Manual correction scope does not match entity visibility")
            if row["entity_version"] != expected_entity_version:
                raise EntityConflict(
                    f"Entity version conflict: expected {expected_entity_version}, actual {row['entity_version']}"
                )
            if row["protection"] == "IMMUTABLE" and not override_immutable:
                raise EntityConflict("immutable entity requires explicit override")

            merged = deep_merge(json.loads(row["data_json"]), patch)
            new_revision = campaign["current_revision"] + 1
            self.conn.execute(
                "UPDATE entity_documents SET data_json=?,entity_version=entity_version+1,updated_by_update_id=?,updated_at=? WHERE campaign_id=? AND id=?",
                (stable_json(merged), f"manual:{correction_id}", now, campaign_id, entity_id),
            )
            self.conn.execute(
                "UPDATE campaigns SET current_revision=?,updated_at=? WHERE id=?",
                (new_revision, now, campaign_id),
            )
            if visibility == "GM":
                summary = "Correction manuelle MJ enregistrée"
                metadata = {"correction_id": correction_id, "visibility": "GM", "reason_recorded": True}
            else:
                summary = f"Correction manuelle joueur : {row['entity_type']}"
                metadata = {
                    "correction_id": correction_id,
                    "visibility": "PLAYER",
                    "entity_id": entity_id,
                    "entity_type": row["entity_type"],
                    "reason": reason.strip(),
                }
            self._audit(
                campaign_id, campaign["current_timeline_id"], "manual_entity_correction", summary, metadata
            )
            self.conn.commit()
            return {
                "correction_id": correction_id,
                "campaign_revision": new_revision,
                "entity_id": entity_id,
                "entity_version": row["entity_version"] + 1,
            }
        except Exception:
            self.conn.rollback()
            raise

    def _snapshot_state(self, campaign_id: str) -> dict[str, Any]:
        campaign = self.campaign(campaign_id)
        return {
            "game_time": campaign["game_time"],
            "death_pending": bool(campaign["death_pending"]),
            "death_summary": campaign["death_summary"],
            "entities": self._entity_export(campaign_id, include_gm=True),
            "links": [
                dict(r)
                for r in self.conn.execute(
                    "SELECT * FROM entity_links WHERE campaign_id=? AND archived=0 ORDER BY id", (campaign_id,)
                ).fetchall()
            ],
        }

    def _create_rest_point_in_tx(self, campaign_id: str, checkpoint_id: str, location: str | None, description: str, source_update_id: str | None) -> None:
        campaign = self.campaign(campaign_id)
        snapshot = self._snapshot_state(campaign_id)
        raw = stable_json(snapshot)
        self.conn.execute(
            "INSERT INTO rest_points(id,campaign_id,timeline_id,source_update_id,snapshot_revision,game_time,location,description,snapshot_json,snapshot_sha256,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                checkpoint_id,
                campaign_id,
                campaign["current_timeline_id"],
                source_update_id,
                campaign["current_revision"],
                campaign["game_time"],
                location,
                description,
                raw,
                sha256_text(raw),
                utc_now(),
            ),
        )

    def create_rest_point(self, campaign_id: str, checkpoint_id: str | None = None, location: str | None = None, description: str = "") -> str:
        checkpoint_id = checkpoint_id or str(uuid.uuid4())
        with self.conn:
            self._create_rest_point_in_tx(campaign_id, checkpoint_id, location, description, None)
        return checkpoint_id

    def add_dead_resolution(
        self,
        campaign_id: str,
        checkpoint_id: str,
        state_fingerprint: str,
        action_fingerprint: str,
        context: dict[str, Any],
        result: dict[str, Any],
        consequences: dict[str, Any],
        notes: str | None = None,
    ) -> str:
        campaign = self.campaign(campaign_id)
        rid = str(uuid.uuid4())
        with self.conn:
            self.conn.execute(
                "INSERT INTO dead_timeline_resolutions(id,campaign_id,source_timeline_id,checkpoint_id,state_fingerprint,action_fingerprint,context_json,result_json,consequences_json,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    rid,
                    campaign_id,
                    campaign["current_timeline_id"],
                    checkpoint_id,
                    state_fingerprint,
                    action_fingerprint,
                    stable_json(context),
                    stable_json(result),
                    stable_json(consequences),
                    notes,
                    utc_now(),
                ),
            )
        return rid

    def rollback_death(self, campaign_id: str, rest_point_id: str, death_summary: str | None = None) -> tuple[int, str]:
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            campaign = self.campaign(campaign_id)
            latest = self.conn.execute(
                "SELECT id FROM rest_points WHERE campaign_id=? AND invalidated_at IS NULL ORDER BY snapshot_revision DESC, created_at DESC, rowid DESC LIMIT 1",
                (campaign_id,),
            ).fetchone()
            if not latest or latest["id"] != rest_point_id:
                raise KitabaError("Death rollback is only authorized to the latest valid Rest Point")
            rest = self.conn.execute(
                "SELECT * FROM rest_points WHERE id=? AND campaign_id=? AND invalidated_at IS NULL",
                (rest_point_id, campaign_id),
            ).fetchone()
            if not rest:
                raise KitabaError("Unknown or invalid Rest Point")
            if not campaign["death_pending"]:
                raise KitabaError("Death rollback is not authorized: no confirmed player death")
            old_timeline_id = campaign["current_timeline_id"]
            dead_snapshot = self._snapshot_state(campaign_id)
            dead_raw = stable_json(dead_snapshot)
            dead_id = str(uuid.uuid4())
            new_timeline_id = str(uuid.uuid4())
            new_revision = campaign["current_revision"] + 1
            now = utc_now()

            self.conn.execute(
                "INSERT INTO dead_timelines(id,campaign_id,timeline_id,died_at_revision,death_summary,state_snapshot_json,state_snapshot_sha256,rolled_back_to_rest_point_id,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (dead_id, campaign_id, old_timeline_id, campaign["current_revision"], death_summary, dead_raw, sha256_text(dead_raw), rest_point_id, now),
            )
            self.conn.execute(
                "UPDATE timelines SET status='DEAD',ended_revision=? WHERE id=?",
                (campaign["current_revision"], old_timeline_id),
            )

            snapshot = json.loads(rest["snapshot_json"])
            self.conn.execute("DELETE FROM entity_documents WHERE campaign_id=?", (campaign_id,))
            self.conn.execute("DELETE FROM entity_links WHERE campaign_id=?", (campaign_id,))
            for entity in snapshot["entities"]:
                self.conn.execute(
                    "INSERT INTO entity_documents(id,campaign_id,entity_type,visibility,entity_version,data_json,protection,archived,created_at,updated_at) VALUES (?,?,?,?,?,?,?,0,?,?)",
                    (
                        entity["id"], campaign_id, entity["entity_type"], entity["visibility"],
                        entity["entity_version"], stable_json(entity["data"]), entity.get("protection", "NORMAL"), now, now
                    ),
                )
            for link in snapshot.get("links", []):
                self.conn.execute(
                    "INSERT INTO entity_links(id,campaign_id,from_entity_id,to_entity_id,link_type,visibility,data_json,archived,created_by_update_id,updated_by_update_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        link["id"], campaign_id, link["from_entity_id"], link["to_entity_id"], link["link_type"],
                        link["visibility"], link["data_json"], link["archived"], link["created_by_update_id"],
                        link["updated_by_update_id"], link["created_at"], link["updated_at"]
                    ),
                )

            self.conn.execute(
                "INSERT INTO timelines(id,campaign_id,parent_timeline_id,restored_from_rest_point_id,status,started_revision,created_at) VALUES (?,?,?,?,?,?,?)",
                (new_timeline_id, campaign_id, old_timeline_id, rest_point_id, "ACTIVE", new_revision, now),
            )
            self.conn.execute(
                "UPDATE campaigns SET current_revision=?,current_timeline_id=?,game_time=?,last_update_id=NULL,updated_at=?,death_pending=0,death_summary=NULL WHERE id=?",
                (new_revision, new_timeline_id, snapshot["game_time"], now, campaign_id),
            )
            self._audit(
                campaign_id, new_timeline_id, "death_rollback", "Death rollback to authorized Rest Point",
                {"rest_point_id": rest_point_id, "previous_timeline_id": old_timeline_id},
            )
            self.conn.commit()
            return new_revision, new_timeline_id
        except Exception:
            self.conn.rollback()
            raise

    def create_technical_backup(self, campaign_id: str | None, output_path: str | Path, reason: str) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if campaign_id is not None and not self.conn.execute("SELECT 1 FROM campaigns WHERE id=?", (campaign_id,)).fetchone():
            raise KitabaError(f"Unknown campaign {campaign_id}")
        with tempfile.TemporaryDirectory() as td:
            db_copy = Path(td) / "campaign.sqlite"
            backup_conn = sqlite3.connect(db_copy)
            backup_conn.execute("PRAGMA foreign_keys=ON")
            self.conn.backup(backup_conn)
            if campaign_id is not None:
                # A manual .kitaba campaign backup must never silently contain other campaigns.
                backup_conn.execute("DELETE FROM campaigns WHERE id<>?", (campaign_id,))
                backup_conn.execute("DELETE FROM technical_backups WHERE campaign_id IS NULL OR campaign_id<>?", (campaign_id,))
                backup_conn.execute("DELETE FROM audit_log WHERE campaign_id IS NULL OR campaign_id<>?", (campaign_id,))
                backup_conn.commit()
            backup_conn.close()
            db_hash = hashlib.sha256(db_copy.read_bytes()).hexdigest()
            files: dict[str, dict[str, str]] = {"campaign.sqlite": {"sha256": db_hash}}
            asset_rows = self.conn.execute(
                "SELECT campaign_id,relative_path,sha256 FROM assets" + (" WHERE campaign_id=?" if campaign_id is not None else ""),
                ((campaign_id,) if campaign_id is not None else ()),
            ).fetchall()
            staged_assets: list[tuple[Path, str]] = []
            for row in asset_rows:
                src = self._managed_asset_path(row["campaign_id"], row["relative_path"])
                if campaign_id is not None and row["campaign_id"] != campaign_id:
                    raise KitabaError("Campaign backup contains asset registration from another campaign")
                if not src.is_file():
                    raise KitabaError(f"Registered asset is missing: {row['relative_path']}")
                data = src.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                if row["sha256"] and digest != row["sha256"]:
                    raise KitabaError(f"Registered asset checksum mismatch: {row['relative_path']}")
                archive_name = f"assets/{row['relative_path']}"
                files[archive_name] = {"sha256": digest}
                staged_assets.append((src, archive_name))
            manifest = {
                "format": "KITABA_BACKUP",
                "backup_version": 1,
                "schema_version": SCHEMA_VERSION,
                "campaign_id": campaign_id,
                "reason": reason,
                "created_at": utc_now(),
                "files": files,
            }
            manifest_raw = json.dumps(manifest, ensure_ascii=False, indent=2)
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(db_copy, arcname="campaign.sqlite")
                for src, archive_name in staged_assets:
                    zf.write(src, arcname=archive_name)
                zf.writestr("manifest.json", manifest_raw)
        file_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        with self.conn:
            self.conn.execute(
                "INSERT INTO technical_backups(id,campaign_id,reason,file_name,sha256,created_at) VALUES (?,?,?,?,?,?)",
                (str(uuid.uuid4()), campaign_id, reason, output_path.name, file_hash, utc_now()),
            )
        return output_path

    @staticmethod
    def verify_backup(path: str | Path) -> dict[str, Any]:
        path = Path(path)
        try:
            with zipfile.ZipFile(path, "r") as zf:
                if "manifest.json" not in zf.namelist() or "campaign.sqlite" not in zf.namelist():
                    raise KitabaError("Not a Kitaba backup: required files are missing")
                manifest = json.loads(zf.read("manifest.json"))
                if manifest.get("format") != "KITABA_BACKUP":
                    raise KitabaError("Not a Kitaba backup: invalid manifest format")
                if manifest.get("backup_version") != 1:
                    raise KitabaError("Unsupported Kitaba backup version")
                schema_version = manifest.get("schema_version")
                if not isinstance(schema_version, int):
                    raise KitabaError("Backup manifest has no valid schema_version")
                if schema_version > SCHEMA_VERSION:
                    raise KitabaError(
                        f"Backup schema {schema_version} is newer than this Companion supports ({SCHEMA_VERSION})"
                    )
                files = manifest.get("files")
                if not isinstance(files, dict) or "campaign.sqlite" not in files:
                    raise KitabaError("Backup manifest has no database checksum")
                for archive_name, metadata in files.items():
                    if archive_name == "manifest.json" or archive_name.startswith("/") or ".." in Path(archive_name).parts:
                        raise KitabaError("Backup manifest contains an unsafe file path")
                    if archive_name not in zf.namelist():
                        raise KitabaError(f"Backup file is missing: {archive_name}")
                    expected = metadata.get("sha256") if isinstance(metadata, dict) else None
                    if not isinstance(expected, str):
                        raise KitabaError(f"Backup manifest has no checksum for {archive_name}")
                    actual = hashlib.sha256(zf.read(archive_name)).hexdigest()
                    if actual != expected:
                        raise KitabaError(f"Backup checksum mismatch: {archive_name}")
                return manifest
        except zipfile.BadZipFile as exc:
            raise KitabaError("Invalid .kitaba archive") from exc

    @staticmethod
    def restore_backup_to(path: str | Path, destination_db: str | Path) -> dict[str, Any]:
        path = Path(path)
        destination_db = Path(destination_db)
        manifest = KitabaEngine.verify_backup(path)
        destination_assets = destination_db.parent / "assets"
        with zipfile.ZipFile(path, "r") as zf:
            db_bytes = zf.read("campaign.sqlite")
            asset_entries = [name for name in manifest.get("files", {}) if name.startswith("assets/")]
            extracted_assets: list[tuple[Path, bytes]] = []
            for name in asset_entries:
                relative = Path(name).relative_to("assets")
                if relative.is_absolute() or ".." in relative.parts:
                    raise KitabaError("Unsafe asset path in backup")
                extracted_assets.append((destination_assets / relative, zf.read(name)))
        destination_db.parent.mkdir(parents=True, exist_ok=True)
        tmp = destination_db.with_suffix(destination_db.suffix + ".restore-tmp")
        tmp.write_bytes(db_bytes)
        check = sqlite3.connect(tmp)
        try:
            result = check.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise KitabaError(f"Restored SQLite integrity check failed: {result}")
            tables = {row[0] for row in check.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "campaigns" not in tables or "schema_migrations" not in tables:
                raise KitabaError("Not a Kitaba backup: required database tables are missing")
            fk_problem = check.execute("PRAGMA foreign_key_check").fetchone()
            if fk_problem is not None:
                raise KitabaError("Restored SQLite foreign-key integrity check failed")
        finally:
            check.close()
        os.replace(tmp, destination_db)
        for asset_path, data in extracted_assets:
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_path.write_bytes(data)
        return manifest

    def restore_backup_into_current(self, path: str | Path) -> dict[str, Any]:
        """Restore a .kitaba backup into this database without destroying unrelated campaigns.

        Campaign-scoped backups replace/import only their campaign. Full-app backups
        (manifest campaign_id = null) replace the complete database state and are
        intended for disaster recovery.
        """
        path = Path(path)
        manifest = self.verify_backup(path)
        with tempfile.TemporaryDirectory() as td:
            incoming_db = Path(td) / "incoming.sqlite"
            with zipfile.ZipFile(path, "r") as zf:
                incoming_db.write_bytes(zf.read("campaign.sqlite"))
                archived_assets = {
                    name: zf.read(name)
                    for name in manifest.get("files", {})
                    if name.startswith("assets/")
                }
            incoming_engine = KitabaEngine(incoming_db)
            incoming_engine.close()

            campaign_id = manifest.get("campaign_id")
            if campaign_id is None:
                self.conn.close()
                os.replace(incoming_db, self.db_path)
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
                self.conn.execute("PRAGMA foreign_keys=ON")
                self._load_validators()
                self._migrate()
                # Full disaster recovery replaces the managed asset tree as well.
                if self.asset_root.exists():
                    import shutil
                    shutil.rmtree(self.asset_root)
                self.asset_root.mkdir(parents=True, exist_ok=True)
                for name, data in archived_assets.items():
                    relative = Path(name).relative_to("assets")
                    if relative.is_absolute() or ".." in relative.parts:
                        raise KitabaError("Unsafe asset path in backup")
                    target = self.asset_root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                return manifest

            probe = sqlite3.connect(incoming_db)
            try:
                count = probe.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
                row = probe.execute("SELECT id FROM campaigns LIMIT 1").fetchone()
                if count != 1 or row is None or row[0] != campaign_id:
                    raise KitabaError("Campaign backup manifest/database mismatch")
            finally:
                probe.close()

            # Attach the verified/migrated backup and copy only the target campaign.
            self.conn.execute("ATTACH DATABASE ? AS incoming", (str(incoming_db),))
            try:
                self.conn.execute("BEGIN IMMEDIATE")
                self.conn.execute("DELETE FROM campaigns WHERE id=?", (campaign_id,))
                self.conn.execute("INSERT INTO campaigns SELECT * FROM incoming.campaigns WHERE id=?", (campaign_id,))
                for table in [
                    "timelines", "entity_documents", "entity_links", "applied_updates",
                    "rest_points", "dead_timelines", "dead_timeline_resolutions",
                    "technical_backups", "audit_log", "assets",
                ]:
                    self.conn.execute(
                        f"INSERT INTO {table} SELECT * FROM incoming.{table} WHERE campaign_id=?",
                        (campaign_id,),
                    )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise
            finally:
                self.conn.execute("DETACH DATABASE incoming")

            # Replace only the restored campaign's managed assets, preserving every
            # other campaign's files.
            campaign_dir = self.asset_root / campaign_id
            if campaign_dir.exists():
                import shutil
                shutil.rmtree(campaign_dir)
            for name, data in archived_assets.items():
                relative = Path(name).relative_to("assets")
                if relative.is_absolute() or ".." in relative.parts:
                    raise KitabaError("Unsafe asset path in backup")
                if not relative.parts or relative.parts[0] != campaign_id:
                    raise KitabaError("Campaign backup contains an asset from another campaign")
                target = self.asset_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        return manifest

    def list_archived_campaigns(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self.conn.execute(
            "SELECT id,name,current_revision,current_timeline_id,game_time,death_pending,death_summary,last_gm_export_revision,last_gm_export_at,last_player_export_revision,last_player_export_at,archived_at FROM campaigns WHERE archived_at IS NOT NULL ORDER BY archived_at DESC"
        ).fetchall()]

    def archive_campaign(self, campaign_id: str) -> None:
        campaign = self.campaign(campaign_id)
        if campaign["archived_at"] is not None:
            return
        now = utc_now()
        with self.conn:
            self.conn.execute(
                "UPDATE campaigns SET archived_at=?,updated_at=? WHERE id=?",
                (now, now, campaign_id),
            )
            self._audit(campaign_id, campaign["current_timeline_id"], "campaign_archived", "Campaign archived", {})

    def restore_archived_campaign(self, campaign_id: str) -> None:
        campaign = self.campaign(campaign_id)
        if campaign["archived_at"] is None:
            return
        now = utc_now()
        with self.conn:
            self.conn.execute(
                "UPDATE campaigns SET archived_at=NULL,updated_at=? WHERE id=?",
                (now, campaign_id),
            )
            self._audit(campaign_id, campaign["current_timeline_id"], "campaign_unarchived", "Campaign restored from archive", {})

    def delete_campaign_permanently(self, campaign_id: str, expected_name: str) -> None:
        campaign = self.campaign(campaign_id)
        if campaign["name"] != expected_name:
            raise ValidationError("Campaign name confirmation does not match")
        campaign_dir = self.asset_root / campaign_id
        with self.conn:
            # The DB cascades every campaign-scoped row. The audit trail is also
            # campaign-scoped and intentionally disappears with a permanent deletion.
            self.conn.execute("DELETE FROM campaigns WHERE id=?", (campaign_id,))
        if campaign_dir.exists():
            import shutil
            shutil.rmtree(campaign_dir)

    def integrity_report(self, campaign_id: str) -> dict[str, Any]:
        campaign = self.campaign(campaign_id)
        checks: list[dict[str, Any]] = []

        def add(code: str, ok: bool, message: str) -> None:
            checks.append({"code": code, "ok": bool(ok), "message": message})

        integrity = self.conn.execute("PRAGMA integrity_check").fetchone()[0]
        add("sqlite_integrity", integrity == "ok", "Base SQLite saine" if integrity == "ok" else "Échec du contrôle SQLite")
        fk = self.conn.execute("PRAGMA foreign_key_check").fetchall()
        add("foreign_keys", not fk, "Clés étrangères cohérentes" if not fk else f"{len(fk)} violation(s) de clé étrangère")

        active = self.conn.execute(
            "SELECT id FROM timelines WHERE campaign_id=? AND status='ACTIVE'",
            (campaign_id,),
        ).fetchall()
        active_ids = {r["id"] for r in active}
        active_ok = len(active_ids) == 1 and campaign["current_timeline_id"] in active_ids
        add("active_timeline", active_ok, "Timeline active cohérente" if active_ok else "Incohérence de timeline active")

        future_update = self.conn.execute(
            "SELECT COUNT(*) FROM applied_updates WHERE campaign_id=? AND target_revision>?",
            (campaign_id, campaign["current_revision"]),
        ).fetchone()[0]
        add("revision_bounds", future_update == 0, "Révisions appliquées cohérentes" if future_update == 0 else "Une mise à jour dépasse la révision canonique")

        bad_rest = 0
        for row in self.conn.execute(
            "SELECT snapshot_json,snapshot_sha256 FROM rest_points WHERE campaign_id=?",
            (campaign_id,),
        ):
            if sha256_text(row["snapshot_json"]) != row["snapshot_sha256"]:
                bad_rest += 1
        add("rest_point_hashes", bad_rest == 0, "Rest Points intègres" if bad_rest == 0 else f"{bad_rest} Rest Point(s) altéré(s)")

        bad_dead = 0
        for row in self.conn.execute(
            "SELECT state_snapshot_json,state_snapshot_sha256 FROM dead_timelines WHERE campaign_id=?",
            (campaign_id,),
        ):
            if sha256_text(row["state_snapshot_json"]) != row["state_snapshot_sha256"]:
                bad_dead += 1
        add("dead_timeline_hashes", bad_dead == 0, "Timelines mortes intègres" if bad_dead == 0 else f"{bad_dead} timeline(s) morte(s) altérée(s)")

        missing_assets = 0
        altered_assets = 0
        for row in self.conn.execute(
            "SELECT relative_path,sha256 FROM assets WHERE campaign_id=?",
            (campaign_id,),
        ):
            try:
                path = self._managed_asset_path(campaign_id, row["relative_path"])
            except ValidationError:
                altered_assets += 1
                continue
            if not path.is_file():
                missing_assets += 1
                continue
            if row["sha256"] and hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                altered_assets += 1
        asset_ok = missing_assets == 0 and altered_assets == 0
        add("assets", asset_ok, "Assets intègres" if asset_ok else f"Assets: {missing_assets} manquant(s), {altered_assets} altéré(s)")

        gm_bad = self.conn.execute(
            "SELECT COUNT(*) FROM entity_documents WHERE campaign_id=? AND visibility NOT IN ('PLAYER','GM')",
            (campaign_id,),
        ).fetchone()[0]
        add("visibility_domain", gm_bad == 0, "Domaines de visibilité valides" if gm_bad == 0 else "Valeur de visibilité invalide détectée")

        return {
            "campaign_id": campaign_id,
            "checked_at": utc_now(),
            "ok": all(c["ok"] for c in checks),
            "checks": checks,
        }

    def _audit(self, campaign_id: str | None, timeline_id: str | None, event_type: str, summary: str, metadata: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO audit_log(id,campaign_id,timeline_id,event_type,summary,metadata_json,created_at) VALUES (?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), campaign_id, timeline_id, event_type, summary, stable_json(metadata), utc_now()),
        )
