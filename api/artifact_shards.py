from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SHARD_SCHEMA = "ailovanta.artifact_shards.v1"


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def build_file_shards(path: str | Path, out_dir: str | Path = "runtime_data/artifact_shards", chunk_size: int = 4 * 1024 * 1024) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise ValueError("artifact shard source must be a file")
    target = Path(out_dir) / source.stem
    target.mkdir(parents=True, exist_ok=True)
    shards: list[dict[str, Any]] = []
    index = 0
    with source.open("rb") as handle:
        while True:
            data = handle.read(chunk_size)
            if not data:
                break
            digest = sha256_bytes(data)
            shard_path = target / ("shard_%06d.bin" % index)
            shard_path.write_bytes(data)
            shards.append({"index": index, "path": str(shard_path), "size_bytes": len(data), "hash": digest})
            index += 1
    manifest = {
        "schema_version": SHARD_SCHEMA,
        "source_path": str(source),
        "artifact_hash": file_digest(source),
        "chunk_size": chunk_size,
        "shard_count": len(shards),
        "total_bytes": source.stat().st_size,
        "shards": shards,
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"manifest_path": str(manifest_path), "manifest": manifest}


def verify_shards(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != SHARD_SCHEMA:
        raise ValueError("unsupported shard manifest schema")
    missing = []
    bad = []
    total = 0
    for shard in manifest.get("shards", []):
        path = Path(shard["path"])
        if not path.exists():
            missing.append(shard["index"])
            continue
        data = path.read_bytes()
        total += len(data)
        if sha256_bytes(data) != shard.get("hash"):
            bad.append(shard["index"])
    return {"ok": not missing and not bad and total == manifest.get("total_bytes"), "missing": missing, "bad": bad, "total_bytes": total}
