from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.artifact_shards import build_file_shards, verify_shards

router = APIRouter(prefix="/artifact-shards", tags=["artifact-shards"])


class ShardRequest(BaseModel):
    path: str
    out_dir: str = "runtime_data/artifact_shards"
    chunk_size: int = Field(default=4 * 1024 * 1024, ge=1024)


class VerifyRequest(BaseModel):
    manifest: dict[str, Any]


@router.post("/build")
def build_shards(body: ShardRequest) -> dict[str, Any]:
    try:
        return {"ok": True, **build_file_shards(body.path, body.out_dir, body.chunk_size)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/verify")
def verify(body: VerifyRequest) -> dict[str, Any]:
    try:
        return verify_shards(body.manifest)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/manifests")
def list_manifests(root: str = "runtime_data/artifact_shards") -> dict[str, Any]:
    base = Path(root)
    if not base.exists():
        return {"ok": True, "items": []}
    items = [str(path) for path in base.rglob("manifest.json")]
    return {"ok": True, "items": items}
