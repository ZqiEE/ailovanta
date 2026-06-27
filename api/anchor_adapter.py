from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any, Protocol
from urllib import request
from uuid import uuid4

from api.prod_config import load_config


def digest_payload(payload: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AnchorRecord:
    anchor_id: str
    anchor_uri: str
    anchor_type: str
    payload_hash: str
    payload: dict[str, Any]
    created_at: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "anchor_uri": self.anchor_uri,
            "anchor_type": self.anchor_type,
            "payload_hash": self.payload_hash,
            "payload": self.payload,
            "created_at": self.created_at,
        }


class AnchorAdapter(Protocol):
    def anchor(self, payload: dict[str, Any]) -> AnchorRecord:
        ...


class FileAnchorAdapter:
    def __init__(self, root: str | Path = "runtime_data/anchors") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def anchor(self, payload: dict[str, Any]) -> AnchorRecord:
        payload_hash = str(payload.get("artifact_hash") or payload.get("decision_hash") or payload.get("hash") or digest_payload(payload))
        anchor_id = "anchor_" + uuid4().hex[:12]
        record = AnchorRecord(
            anchor_id=anchor_id,
            anchor_uri=str(self.root / f"{anchor_id}.json"),
            anchor_type="file",
            payload_hash=payload_hash,
            payload=payload,
            created_at=round(time(), 3),
        )
        path = Path(record.anchor_uri)
        path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        with (self.root / "anchor_log.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return record


class HttpNotaryAnchorAdapter:
    def __init__(self, uri: str | None) -> None:
        self.uri = uri

    def anchor(self, payload: dict[str, Any]) -> AnchorRecord:
        if not self.uri:
            raise RuntimeError("external anchor uri required")
        payload_hash = str(payload.get("artifact_hash") or payload.get("decision_hash") or payload.get("hash") or digest_payload(payload))
        body = {"schema": "ailovanta.notary_request.v1", "payload_hash": payload_hash, "payload": payload, "created_at": round(time(), 3)}
        req = request.Request(self.uri, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=60) as res:
            response = json.loads(res.read().decode("utf-8"))
        return AnchorRecord(
            anchor_id=str(response.get("anchor_id") or response.get("receipt_id") or "anchor_" + uuid4().hex[:12]),
            anchor_uri=str(response.get("anchor_uri") or response.get("receipt_uri") or self.uri),
            anchor_type=str(response.get("anchor_type") or "http_notary"),
            payload_hash=payload_hash,
            payload={"request": body, "receipt": response},
            created_at=round(time(), 3),
        )


ExternalAnchorAdapter = HttpNotaryAnchorAdapter


def get_anchor_adapter() -> AnchorAdapter:
    cfg = load_config()
    if cfg.chain_anchor == "file":
        return FileAnchorAdapter(cfg.chain_anchor_uri or "runtime_data/anchors")
    return HttpNotaryAnchorAdapter(cfg.chain_anchor_uri)
