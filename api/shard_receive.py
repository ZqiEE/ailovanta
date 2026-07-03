from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def safe_artifact_dir(artifact_hash: str) -> str:
    return artifact_hash.replace(":", "_").replace("/", "_")


def receive_shard(
    *,
    artifact_hash: str,
    shard_index: int,
    shard_hash: str,
    data_base64: str,
    root: str | Path = "runtime_data/received_shards",
    source_runtime_id: str | None = None,
) -> dict[str, Any]:
    data = base64.b64decode(data_base64.encode("utf-8"))
    actual = sha256_bytes(data)
    accepted = actual == shard_hash
    artifact_dir = Path(root) / safe_artifact_dir(artifact_hash)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    shard_path = artifact_dir / ("shard_%06d.bin" % shard_index)
    if accepted:
        shard_path.write_bytes(data)
    return {
        "ok": accepted,
        "artifact_hash": artifact_hash,
        "shard_index": shard_index,
        "expected_hash": shard_hash,
        "actual_hash": actual,
        "size_bytes": len(data),
        "stored_path": str(shard_path) if accepted else None,
        "source_runtime_id": source_runtime_id,
    }


def list_received_shards(root: str | Path = "runtime_data/received_shards") -> dict[str, Any]:
    base = Path(root)
    if not base.exists():
        return {"ok": True, "items": []}
    items = []
    for path in base.rglob("shard_*.bin"):
        items.append({"path": str(path), "size_bytes": path.stat().st_size, "hash": sha256_bytes(path.read_bytes())})
    return {"ok": True, "items": items}
