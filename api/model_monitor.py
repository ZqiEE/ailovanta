from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4


class ModelMonitorStore:
    def __init__(self, root: str | Path = "runtime_data/model_monitor") -> None:
        self.root = Path(root)
        self.shadow_dir = self.root / "shadow"
        self.live_dir = self.root / "live"
        self.metrics_dir = self.root / "metrics"
        self.actions_dir = self.root / "actions"
        for path in [self.shadow_dir, self.live_dir, self.metrics_dir, self.actions_dir]:
            path.mkdir(parents=True, exist_ok=True)

    def register_shadow(self, candidate_model: str, baseline_model: str, artifact_hash: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        shadow_id = "shadow_" + uuid4().hex[:12]
        payload = {
            "shadow_id": shadow_id,
            "candidate_model": candidate_model,
            "baseline_model": baseline_model,
            "artifact_hash": artifact_hash,
            "status": "shadow",
            "metadata": metadata or {},
            "created_at": round(time(), 3),
        }
        self._write(self.shadow_dir / f"{shadow_id}.json", payload)
        return payload

    def promote_live(self, shadow_id: str) -> dict[str, Any]:
        shadow = self.get_shadow(shadow_id)
        if not shadow:
            raise ValueError("shadow not found")
        live_id = "live_" + uuid4().hex[:12]
        payload = {
            "live_id": live_id,
            "shadow_id": shadow_id,
            "model": shadow["candidate_model"],
            "previous_model": shadow["baseline_model"],
            "artifact_hash": shadow.get("artifact_hash"),
            "status": "live",
            "created_at": round(time(), 3),
        }
        shadow["status"] = "promoted"
        shadow["promoted_live_id"] = live_id
        self._write(self.shadow_dir / f"{shadow_id}.json", shadow)
        self._write(self.live_dir / f"{live_id}.json", payload)
        return payload

    def record_metric(self, model: str, metrics: dict[str, float], mode: str = "shadow", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        metric_id = "metric_" + uuid4().hex[:12]
        payload = {
            "metric_id": metric_id,
            "model": model,
            "mode": mode,
            "metrics": {key: float(value) for key, value in metrics.items()},
            "metadata": metadata or {},
            "created_at": round(time(), 3),
        }
        self._write(self.metrics_dir / f"{metric_id}.json", payload)
        return payload

    def evaluate_rollback(self, live_model: str, baseline_metrics: dict[str, float], max_drop: float = 0.05) -> dict[str, Any]:
        latest = self.latest_metrics(live_model)
        if not latest:
            return self._write_action({"action": "hold", "reason": "no_live_metrics", "model": live_model})
        drops: dict[str, float] = {}
        for key, baseline in baseline_metrics.items():
            current = float(latest["metrics"].get(key, baseline))
            drop = float(baseline) - current
            if drop > max_drop:
                drops[key] = round(drop, 4)
        if drops:
            return self._write_action({"action": "rollback", "reason": "metric_drop", "model": live_model, "drops": drops, "metric_id": latest["metric_id"]})
        return self._write_action({"action": "hold", "reason": "metrics_ok", "model": live_model, "metric_id": latest["metric_id"]})

    def latest_metrics(self, model: str) -> dict[str, Any] | None:
        rows = [self._read(path) for path in self.metrics_dir.glob("*.json")]
        rows = [row for row in rows if row.get("model") == model]
        rows.sort(key=lambda row: row.get("created_at", 0), reverse=True)
        return rows[0] if rows else None

    def get_shadow(self, shadow_id: str) -> dict[str, Any] | None:
        path = self.shadow_dir / f"{shadow_id}.json"
        return self._read(path) if path.exists() else None

    def list_shadows(self) -> list[dict[str, Any]]:
        return [self._read(path) for path in sorted(self.shadow_dir.glob("*.json"))]

    def list_live(self) -> list[dict[str, Any]]:
        return [self._read(path) for path in sorted(self.live_dir.glob("*.json"))]

    def list_actions(self) -> list[dict[str, Any]]:
        return [self._read(path) for path in sorted(self.actions_dir.glob("*.json"))]

    def _write_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload = {**payload, "action_id": "action_" + uuid4().hex[:12], "created_at": round(time(), 3)}
        self._write(self.actions_dir / f"{payload['action_id']}.json", payload)
        return payload

    @staticmethod
    def _write(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))
