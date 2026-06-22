from __future__ import annotations

import json
from pathlib import Path


class MemoryStore:
    def __init__(self, path: str | Path = "runtime_data/memory.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list(self, user_id: str = "local") -> list[str]:
        data = self._read()
        return list(data.get(user_id, []))

    def add(self, memory: str, user_id: str = "local") -> list[str]:
        memory = memory.strip()
        if not memory:
            return self.list(user_id)
        data = self._read()
        values = list(data.get(user_id, []))
        values.append(memory)
        data[user_id] = values[-50:]
        self._write(data)
        return data[user_id]

    def wipe(self, user_id: str = "local") -> None:
        data = self._read()
        data[user_id] = []
        self._write(data)

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
