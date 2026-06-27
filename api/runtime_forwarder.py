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

    def register(self, runtime_id: str, url: str, token: str | None = None) -> dict[str, str]:
        data = self.all()
        data[runtime_id] = {"url": url.rstrip("/"), "token": token or ""}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"runtime_id": runtime_id, "url": data[runtime_id]["url"], "token_set": bool(token)}

    def get(self, runtime_id: str) -> dict[str, str] | None:
        item = self.all().get(runtime_id)
        if isinstance(item, str):
            return {"url": item, "token": ""}
        return item

    def all(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))


def post_json(url: str, body: dict[str, Any], token: str | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Ailovanta-Node-Token"] = token
    req = request.Request(url, data=data, headers=headers, method="POST")
    with request.urlopen(req, timeout=60) as res:
        return json.loads(res.read().decode("utf-8"))
