from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4


class AutoTruthEventStore:
    def __init__(self, root: str | Path = "runtime_data/autotruth_public") -> None:
        self.root = Path(root)
        self.events_dir = self.root / "events"
        self.runs_dir = self.root / "runs"
        self.packs_dir = self.root / "packs"
        for path in [self.events_dir, self.runs_dir, self.packs_dir]:
            path.mkdir(parents=True, exist_ok=True)

    def add_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "event_id": payload.get("event_id") or "evt_" + uuid4().hex[:12],
            "input": str(payload.get("input") or payload.get("prompt") or ""),
            "output": str(payload.get("output") or payload.get("answer") or ""),
            "source": str(payload.get("source") or "public-runtime"),
            "context": dict(payload.get("context") or {}),
            "metadata": dict(payload.get("metadata") or {}),
            "behavior": dict(payload.get("behavior") or {}),
            "created_at": round(time(), 3),
        }
        if not event["input"] or not event["output"]:
            raise ValueError("input and output are required")
        self._write(self.events_dir / f"{event['event_id']}.json", event)
        return event

    def list_events(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = sorted(self.events_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        return [self._read(path) for path in rows[:limit]]

    def export_events(self, output_path: str | Path = "runtime_data/autotruth_public/events_export.json") -> dict[str, Any]:
        events = list(reversed(self.list_events(limit=10000)))
        payload = {"schema_version": "ailovanta.autotruth.events_export.v1", "events": events, "exported_at": round(time(), 3)}
        self._write(Path(output_path), payload)
        return {"event_count": len(events), "export_path": str(output_path)}

    def import_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        run_id = payload.get("run_id") or "atrun_" + uuid4().hex[:12]
        payload = {**payload, "run_id": run_id, "imported_at": round(time(), 3)}
        self._write(self.runs_dir / f"{run_id}.json", payload)
        pack = payload.get("training_pack") or {}
        if pack.get("pack_id"):
            self._write(self.packs_dir / f"{pack['pack_id']}.json", pack)
        return {"run_id": run_id, "pack_id": pack.get("pack_id"), "row_count": len(payload.get("rows", []))}

    def latest_run(self) -> dict[str, Any] | None:
        rows = sorted(self.runs_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        return self._read(rows[0]) if rows else None

    def latest_pack(self) -> dict[str, Any] | None:
        rows = sorted(self.packs_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        return self._read(rows[0]) if rows else None

    @staticmethod
    def _write(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))
