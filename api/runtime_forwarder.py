from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib import request


class RuntimeEndpointStore:
    def __init__(self, path: str | Path = "runtime_data/runtime_endpoints.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def register(self, runtime_id: str, url: str) -> dict[str, str]:
        data = self.all()
        data[runtime_id] = url.rstrip("/")
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"runtime_id": runtime_id, "url": data[runtime_id]}

    def get(self, runtime_id: str) -> str | None:
        return self.all().get(runtime_id)

    def all(self) -> dict[str, str]:
        return json.loads(self.path.read_text(encoding="utf-8"))


def post_json(url: str, body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=60) as res:
        return json.loads(res.read().decode("utf-8"))
