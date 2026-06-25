from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from time import time
from typing import Any

from api.sqlite_utils import connect_sqlite


class RouteBook:
    def __init__(self, path: str | Path = "runtime_data/route_book.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS route_book (
                    route_key TEXT PRIMARY KEY,
                    model_key TEXT NOT NULL,
                    binding_id TEXT,
                    status TEXT NOT NULL,
                    reason TEXT,
                    metadata_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_route_book_status ON route_book(status);
                """
            )

    def set_active(self, route_key: str, model_key: str, binding_id: str | None = None, reason: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        now = round(time(), 3)
        with self.connect() as conn:
            before = conn.execute("SELECT created_at FROM route_book WHERE route_key = ?", (route_key,)).fetchone()
            conn.execute(
                "INSERT OR REPLACE INTO route_book VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (route_key, model_key, binding_id, "active", reason, json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True), before[0] if before else now, now),
            )
        return self.get(route_key) or {}

    def disable(self, route_key: str, reason: str | None = None) -> dict[str, Any] | None:
        with self.connect() as conn:
            conn.execute("UPDATE route_book SET status = ?, reason = ?, updated_at = ? WHERE route_key = ?", ("disabled", reason, round(time(), 3), route_key))
        return self.get(route_key)

    def get(self, route_key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM route_book WHERE route_key = ?", (route_key,)).fetchone()
        if not row:
            return None
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        return item

    def active(self, route_key: str) -> dict[str, Any] | None:
        item = self.get(route_key)
        if not item or item.get("status") != "active":
            return None
        return item

    def list_routes(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM route_book ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
            out.append(item)
        return out
