from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import time
from uuid import uuid4

from fastapi import APIRouter


router = APIRouter()
ROOT = Path("runtime_data/notary")
ROOT.mkdir(parents=True, exist_ok=True)


@router.post("/notary/mock/anchor")
def mock_anchor(payload: dict) -> dict:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    receipt_id = "notary_" + uuid4().hex[:12]
    receipt = {
        "receipt_id": receipt_id,
        "anchor_id": receipt_id,
        "anchor_type": "mock_notary",
        "payload_hash": payload.get("payload_hash") or digest,
        "receipt_uri": str(ROOT / f"{receipt_id}.json"),
        "created_at": round(time(), 3),
    }
    Path(receipt["receipt_uri"]).write_text(json.dumps({"receipt": receipt, "payload": payload}, ensure_ascii=False, indent=2), encoding="utf-8")
    return receipt
