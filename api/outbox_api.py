from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.outbox_run import list_runs, run_from_payload
from api.parcel_store import ParcelStore

router = APIRouter(prefix="/outbox", tags=["outbox"])
store = ParcelStore()


class Body(BaseModel):
    payload: dict[str, Any]


@router.post("/submit")
def submit(body: Body) -> dict[str, Any]:
    item = store.put_outbox(body.payload)
    run = run_from_payload(body.payload)
    return {"ok": True, "item": item, "run": run}


@router.get("/runs")
def runs(limit: int = 20) -> dict[str, Any]:
    return {"items": list_runs(limit=limit)}
