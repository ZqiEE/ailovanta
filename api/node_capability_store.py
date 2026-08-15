from __future__ import annotations

import json
import os
from pathlib import Path
from time import time
from typing import Any


class NodeCapabilityStore:
    """Private scheduler-only node capabilities.

    Installed model tags are useful for routing but are intentionally kept out
    of the public node discovery response.
    """

    def __init__(self, path: str | Path = "runtime_data/coding_node_capabilities.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})
        else:
            self._protect()

    def _protect(self) -> None:
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def _read(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._protect()

    def update(self, node_id: str, ollama_models: list[str]) -> dict[str, Any]:
        clean = sorted({str(name).strip() for name in ollama_models if str(name).strip()})[:128]
        data = self._read()
        data[node_id] = {"ollama_models": clean, "updated_at": round(time(), 3)}
        self._write(data)
        return data[node_id]

    def models(self, node_id: str) -> set[str]:
        row = self._read().get(node_id)
        if not isinstance(row, dict):
            return set()
        values = row.get("ollama_models")
        if not isinstance(values, list):
            return set()
        return {str(value) for value in values if value}

    def supports_model(self, node_id: str, model: str) -> bool:
        models = self.models(node_id)
        if ":" in model:
            return model in models
        return any(value.split(":", 1)[0] == model for value in models)
