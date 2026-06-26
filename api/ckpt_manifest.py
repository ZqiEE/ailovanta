from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from api.ckpt_merge import to_path


def make_manifest(ref: str, output_dir: str | Path = "runtime_data/manifests", chunk_bytes: int = 8 * 1024 * 1024, min_replicas: int = 3) -> dict[str, Any]:
    path = to_path(ref)
    if path is None or not path.exists() or not path.is_file():
        raise RuntimeError("checkpoint file not found: " + ref)
    chunks: list[dict[str, Any]] = []
    full = hashlib.sha256()
    with path.open("rb") as fh:
        index = 0
        while True:
            data = fh.read(chunk_bytes)
            if not data:
                break
            full.update(data)
            digest = "sha256:" + hashlib.sha256(data).hexdigest()
            chunks.append({"index": index, "bytes": len(data), "hash": digest, "source": "file://" + str(path.resolve())})
            index += 1
    artifact_hash = "sha256:" + full.hexdigest()
    manifest = {
        "schema_version": "ailovanta.artifact_manifest.v1",
        "artifact_ref": "file://" + str(path.resolve()),
        "artifact_name": path.name,
        "artifact_bytes": path.stat().st_size,
        "artifact_hash": artifact_hash,
        "chunk_bytes": chunk_bytes,
        "chunk_count": len(chunks),
        "min_replicas": min_replicas,
        "chunks": chunks,
        "storage_policy": "storage_pool_required",
    }
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    target = out / (path.stem + ".manifest.json")
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest | {"manifest_ref": "file://" + str(target.resolve())}
