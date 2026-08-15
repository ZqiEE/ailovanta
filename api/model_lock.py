from __future__ import annotations

import json
import os
from pathlib import Path
from time import time
from typing import Any


class ModelLockStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or os.getenv("AILOVANTA_MODEL_LOCK_PATH", "runtime_data/model_locks.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def all(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    def check(self, model: str, digest: str | None) -> dict[str, Any]:
        row = self.all().get(model)
        expected = str(row.get("digest")) if isinstance(row, dict) and row.get("digest") else None
        if not digest:
            return {
                "status": "unverifiable",
                "model": model,
                "locked": bool(expected),
                "expected_digest": expected,
                "actual_digest": None,
                "match": None,
            }
        if not expected:
            return {
                "status": "unlocked",
                "model": model,
                "locked": False,
                "expected_digest": None,
                "actual_digest": digest,
                "match": None,
            }
        match = expected == digest
        return {
            "status": "verified" if match else "mismatch",
            "model": model,
            "locked": True,
            "expected_digest": expected,
            "actual_digest": digest,
            "match": match,
        }

    def record(self, model: str, digest: str) -> dict[str, Any]:
        if not model or not digest:
            raise ValueError("model and digest are required")
        data = self.all()
        data[model] = {
            "digest": digest,
            "locked_at": round(time(), 3),
        }
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass
        return self.check(model, digest)

    def ensure(self, model: str, digest: str | None, accept_change: bool = False) -> dict[str, Any]:
        state = self.check(model, digest)
        if state["status"] == "unlocked" and digest:
            result = self.record(model, digest)
            result["recorded_now"] = True
            return result
        if state["status"] == "mismatch" and accept_change and digest:
            result = self.record(model, digest)
            result["accepted_change"] = True
            return result
        return state
