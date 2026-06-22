from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4


class NodeIdentity:
    def __init__(self, path: str | Path = "runtime_data/node_identity.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get_or_create(self) -> str:
        data = self._read()
        node_id = data.get("node_id")
        if node_id:
            return node_id
        node_id = "node_" + uuid4().hex[:12]
        self._write({"node_id": node_id})
        return node_id

    def set(self, node_id: str) -> None:
        self._write({"node_id": node_id})

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
