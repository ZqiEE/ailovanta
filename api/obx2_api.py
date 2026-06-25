from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.outbox_run_v2 import list_runs_v2, run_from_payload_v2
from api.parcel_store import ParcelStore

router = APIRouter(prefix="/obx2", tags=["obx2"])
store = ParcelStore()


class Body(BaseModel):
    payload: dict[str, Any]


@router.post("/submit")
def submit(body: Body) -> dict[str, Any]:
    item = store.put_outbox(body.payload)
    run = run_from_payload_v2(body.payload)
    return {"ok": True, "item": item, "run": run}


@router.get("/runs")
def runs(limit: int = 20) -> dict[str, Any]:
    return {"items": list_runs_v2(limit=limit)}
