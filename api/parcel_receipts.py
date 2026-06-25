from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from api.parcel_store import ParcelStore

RECEIPT_SCHEMA = "ailovanta.checkpoint_receipt.v1"


def stable_hash(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key not in {"receipt_hash"}}
    raw = json.dumps(material, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sha_from_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload.get("result") if isinstance(payload.get("result"), dict) else payload
    task = source.get("task") if isinstance(source.get("task"), dict) else {}
    metrics = source.get("metrics") if isinstance(source.get("metrics"), dict) else {}
    task_id = str(source.get("task_id") or task.get("task_id") or payload.get("task_id") or "unknown_task")
    node_id = str(source.get("node_id") or task.get("node_id") or payload.get("node_id") or "unknown_node")
    checkpoint_uri = str(source.get("checkpoint_uri") or source.get("local_checkpoint_uri") or task.get("checkpoint_uri") or "artifact://" + task_id)
    checkpoint_hash = str(source.get("checkpoint_hash") or source.get("artifact_hash") or sha_from_text(json.dumps(source, ensure_ascii=False, sort_keys=True)))
    if not checkpoint_hash.startswith("sha256:"):
        checkpoint_hash = sha_from_text(checkpoint_hash)
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "receipt_id": str(source.get("receipt_id") or payload.get("id") or "ckpt_receipt_" + uuid4().hex[:12]),
        "task_id": task_id,
        "node_id": node_id,
        "checkpoint_uri": checkpoint_uri,
        "checkpoint_hash": checkpoint_hash,
        "token_count": int(source.get("token_count") or metrics.get("token_count") or 0),
        "train_loss": float(source.get("train_loss") or metrics.get("train_loss") or 0.0),
        "eval_loss": float(source.get("eval_loss") or metrics.get("eval_loss") or 0.0),
        "created_at": float(source.get("created_at") or payload.get("created_at") or round(time(), 3)),
    }
    for key in ["local_checkpoint_uri", "backend_ref", "backend"]:
        if source.get(key):
            receipt[key] = source[key]
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def export_receipts(store: ParcelStore | None = None, output_path: str | Path = "runtime_data/parcels/checkpoint_receipts.json") -> dict[str, Any]:
    parcel_store = store or ParcelStore()
    receipts = [normalize_receipt(item) for item in parcel_store.list_outbox()]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": "ailovanta.checkpoint_receipt_export.v1", "count": len(receipts), "receipts": receipts, "created_at": round(time(), 3)}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "count": len(receipts), "output_path": str(path), "receipts": receipts}
