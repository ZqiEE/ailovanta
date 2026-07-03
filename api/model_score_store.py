from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from time import time
from typing import Any

from api.sqlite_utils import connect_sqlite


class ModelScoreStore:
    def __init__(self, path: str | Path = "runtime_data/model_scores.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS model_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_key TEXT NOT NULL,
                    score REAL NOT NULL,
                    source TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_model_scores_model_key ON model_scores(model_key);
                """
            )

    def record(self, model_key: str, score: float, source: str, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        now = round(time(), 3)
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO model_scores (model_key, score, source, metrics_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (model_key, score, source, json.dumps(metrics or {}, ensure_ascii=False, sort_keys=True), now),
            )
            row_id = cur.lastrowid
        return {"id": row_id, "model_key": model_key, "score": score, "source": source, "metrics": metrics or {}, "created_at": now}

    def best(self, model_key: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM model_scores WHERE model_key = ? ORDER BY score DESC, id DESC LIMIT 1", (model_key,)).fetchone()
        return self._row(dict(row)) if row else None

    def should_accept(self, model_key: str, candidate_score: float, min_delta: float = 0.0) -> dict[str, Any]:
        best = self.best(model_key)
        best_score = float(best["score"]) if best else None
        accept = best_score is None or candidate_score >= best_score + min_delta
        return {"model_key": model_key, "candidate_score": candidate_score, "best_score": best_score, "min_delta": min_delta, "accept": accept, "reason": "score_improved" if accept else "score_not_improved"}

    def history(self, model_key: str, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM model_scores WHERE model_key = ? ORDER BY id DESC LIMIT ?", (model_key, limit)).fetchall()
        return [self._row(dict(row)) for row in rows]

    @staticmethod
    def _row(row: dict[str, Any]) -> dict[str, Any]:
        row["metrics"] = json.loads(row.pop("metrics_json") or "{}")
        return row
