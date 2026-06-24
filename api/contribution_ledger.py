from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.content_addressing import hash_object
from api.sqlite_utils import connect_sqlite


class ContributionLedger:
    def __init__(self, path: str | Path = "runtime_data/decentralized_ledger.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS ledger_events (
                    event_id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    object_hash TEXT NOT NULL,
                    score REAL NOT NULL,
                    credits REAL NOT NULL,
                    details_json TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def append(self, node_id: str, event_type: str, object_hash: str, score: float, credits: float, details: dict[str, Any] | None = None) -> dict:
        event_id = "evt_" + uuid4().hex[:12]
        details = details or {}
        event_hash = hash_object({"event_id": event_id, "node_id": node_id, "event_type": event_type, "object_hash": object_hash, "score": score, "credits": credits, "details": details})
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO ledger_events (event_id, node_id, event_type, object_hash, score, credits, details_json, event_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (event_id, node_id, event_type, object_hash, score, credits, json.dumps(details, ensure_ascii=False), event_hash),
            )
        return self.get_event(event_id) or {}

    def get_event(self, event_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM ledger_events WHERE event_id = ?", (event_id,)).fetchone()
        return self._row(dict(row)) if row else None

    def list_events(self, node_id: str | None = None, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            if node_id:
                rows = conn.execute("SELECT * FROM ledger_events WHERE node_id = ? ORDER BY created_at DESC LIMIT ?", (node_id, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM ledger_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row(dict(row)) for row in rows]

    def node_summary(self, node_id: str) -> dict:
        with self.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS events, COALESCE(SUM(score), 0) AS score, COALESCE(SUM(credits), 0) AS credits FROM ledger_events WHERE node_id = ?", (node_id,)).fetchone()
        return {"node_id": node_id, "events": row["events"], "score": round(row["score"], 3), "credits": round(row["credits"], 3)}

    def network_summary(self) -> dict:
        with self.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS events, COUNT(DISTINCT node_id) AS nodes, COALESCE(SUM(score), 0) AS score, COALESCE(SUM(credits), 0) AS credits FROM ledger_events").fetchone()
        return {"events": row["events"], "nodes": row["nodes"], "score": round(row["score"], 3), "credits": round(row["credits"], 3)}

    @staticmethod
    def _row(item: dict) -> dict:
        item["details"] = json.loads(item.pop("details_json") or "{}")
        return item
