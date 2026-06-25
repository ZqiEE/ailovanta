from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.artifact_binding import ArtifactBindingStore

router = APIRouter(prefix="/artifact-bindings", tags=["artifact-bindings"])
store = ArtifactBindingStore()


class StatusRequest(BaseModel):
    status: str


@router.get("")
def list_bindings(limit: int = 100) -> dict:
    return {"items": store.list_bindings(limit=limit)}


@router.get("/{binding_id}")
def get_binding(binding_id: str) -> dict:
    item = store.get(binding_id)
    if not item:
        raise HTTPException(status_code=404, detail="binding not found")
    return {"binding": item}


@router.get("/by-model/{model_key:path}")
def latest_for_model(model_key: str) -> dict:
    return {"binding": store.latest_for_model(model_key)}


@router.post("/{binding_id}/status")
def set_status(binding_id: str, body: StatusRequest) -> dict:
    item = store.set_status(binding_id, body.status)
    if not item:
        raise HTTPException(status_code=404, detail="binding not found")
    return {"binding": item}
