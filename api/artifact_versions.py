from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.migrations import MigrationRunner
from api.sqlite_utils import connect_sqlite


class ArtifactVersions:
    def __init__(self, path: str | Path = "runtime_data/scheduler.sqlite3") -> None:
        self.path = Path(path)
        MigrationRunner(path).run()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def create(self, name: str, version: str, location: str, catalog_item_id: str | None = None, previous_artifact_id: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        artifact_id = "art_" + uuid4().hex[:12]
        with self.connect() as conn:
            if previous_artifact_id:
                conn.execute("UPDATE artifact_versions SET status = 'inactive' WHERE name = ? AND status = 'active'", (name,))
            conn.execute(
                """
                INSERT INTO artifact_versions (artifact_id, name, version, location, catalog_item_id, status, previous_artifact_id, metadata_json)
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (artifact_id, name, version, location, catalog_item_id, previous_artifact_id, json.dumps(metadata or {}, ensure_ascii=False)),
            )
        return self.get(artifact_id) or {}

    def get(self, artifact_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM artifact_versions WHERE artifact_id = ?", (artifact_id,)).fetchone()
        return self._api(dict(row)) if row else None

    def list(self, name: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            if name:
                rows = conn.execute("SELECT * FROM artifact_versions WHERE name = ? ORDER BY created_at DESC LIMIT ?", (name, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM artifact_versions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._api(dict(row)) for row in rows]

    def active(self, name: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM artifact_versions WHERE name = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1", (name,)).fetchone()
        return self._api(dict(row)) if row else None

    def rollback(self, name: str, artifact_id: str) -> dict[str, Any]:
        target = self.get(artifact_id)
        if not target:
            return {"ok": False, "reason": "artifact not found", "name": name, "artifact_id": artifact_id}
        with self.connect() as conn:
            conn.execute("UPDATE artifact_versions SET status = 'inactive' WHERE name = ?", (name,))
            conn.execute("UPDATE artifact_versions SET status = 'active' WHERE artifact_id = ?", (artifact_id,))
        return {"ok": True, "active": self.get(artifact_id)}

    @staticmethod
    def _api(row: dict[str, Any]) -> dict[str, Any]:
        row["metadata"] = json.loads(row.pop("metadata_json") or "{}")
        return row
