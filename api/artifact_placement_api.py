from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.artifact_placement import plan_shard_placement, verify_placement, write_placement

router = APIRouter(prefix="/artifact-placement", tags=["artifact-placement"])


class PlacementRequest(BaseModel):
    manifest: dict[str, Any]
    replication: int = Field(default=2, ge=1)


class VerifyPlacementRequest(BaseModel):
    placement: dict[str, Any]


@router.post("/plan")
def plan(body: PlacementRequest) -> dict[str, Any]:
    try:
        planned = plan_shard_placement(body.manifest, replication=body.replication)
        return {"ok": True, **write_placement(planned)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/verify")
def verify(body: VerifyPlacementRequest) -> dict[str, Any]:
    try:
        return {"ok": True, "report": verify_placement(body.placement)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/plans")
def list_plans(root: str = "runtime_data/artifact_placements") -> dict[str, Any]:
    base = Path(root)
    if not base.exists():
        return {"ok": True, "items": []}
    return {"ok": True, "items": [str(path) for path in base.glob("*.placement.json")]}
