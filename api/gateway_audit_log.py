from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4


class GatewayAuditLog:
    def __init__(self, path: str | Path = "runtime_data/gateway.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS gateway_events (
                    trace_id TEXT PRIMARY KEY,
                    user_ref TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    tag TEXT,
                    package_hash TEXT,
                    node_id TEXT,
                    status TEXT NOT NULL,
                    result_hash TEXT,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def record(self, user_ref: str, prompt_hash: str, tag: str | None, status: str, package_hash: str | None = None, node_id: str | None = None, result_hash: str | None = None, details: dict[str, Any] | None = None) -> dict:
        trace_id = "trace_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO gateway_events (trace_id, user_ref, prompt_hash, tag, package_hash, node_id, status, result_hash, details_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (trace_id, user_ref, prompt_hash, tag, package_hash, node_id, status, result_hash, json.dumps(details or {}, ensure_ascii=False)),
            )
        return self.get(trace_id) or {}

    def get(self, trace_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM gateway_events WHERE trace_id = ?", (trace_id,)).fetchone()
        return self._row(dict(row)) if row else None

    def list_events(self, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM gateway_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row(dict(row)) for row in rows]

    def summary(self) -> dict:
        with self.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS events, SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) AS ok_events FROM gateway_events").fetchone()
        return {"events": row["events"], "ok_events": row["ok_events"] or 0}

    @staticmethod
    def _row(item: dict) -> dict:
        item["details"] = json.loads(item.pop("details_json") or "{}")
        return item
