from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BOOK = Path("runtime_data/replica_book.json")


def load(path: Path = BOOK) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": "ailovanta.replica_book.v1", "artifacts": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save(data: dict[str, Any], path: Path = BOOK) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def add_manifest(manifest: dict[str, Any], node_id: str = "local", location: str | None = None) -> dict[str, Any]:
    data = load()
    ah = manifest["artifact_hash"]
    artifact = data.setdefault("artifacts", {}).setdefault(ah, {"artifact_hash": ah, "artifact_name": manifest.get("artifact_name"), "artifact_bytes": manifest.get("artifact_bytes"), "min_replicas": manifest.get("min_replicas", 3), "chunks": {}})
    for chunk in manifest.get("chunks", []):
        ch = chunk["hash"]
        rec = artifact.setdefault("chunks", {}).setdefault(ch, {"index": chunk.get("index"), "bytes": chunk.get("bytes"), "copies": []})
        copy = {"node_id": node_id, "location": location or chunk.get("source"), "status": "available"}
        if copy not in rec["copies"]:
            rec["copies"].append(copy)
    return save(data)


def status() -> dict[str, Any]:
    data = load()
    rows = []
    for ah, artifact in data.get("artifacts", {}).items():
        need = int(artifact.get("min_replicas") or 1)
        chunks = artifact.get("chunks", {})
        weak = [ch for ch, rec in chunks.items() if len(rec.get("copies", [])) < need]
        rows.append({"artifact_hash": ah, "artifact_name": artifact.get("artifact_name"), "chunk_count": len(chunks), "under_replicated_chunks": len(weak), "healthy": not weak})
    return {"artifact_count": len(rows), "artifacts": rows}
