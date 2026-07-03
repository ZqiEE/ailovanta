from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/shard-export", tags=["shard-export"])


@router.get("/manifest")
def export_manifest(path: str) -> dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.exists() or manifest_path.name != "manifest.json":
        raise HTTPException(status_code=404, detail="manifest not found")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "manifest_path": str(manifest_path), "manifest": manifest}


@router.get("/shard")
def export_shard(path: str) -> dict[str, Any]:
    shard_path = Path(path)
    if not shard_path.exists() or not shard_path.is_file():
        raise HTTPException(status_code=404, detail="shard not found")
    return {"ok": True, "path": str(shard_path), "size_bytes": shard_path.stat().st_size}
