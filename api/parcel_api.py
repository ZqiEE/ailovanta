from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.parcel_store import ParcelStore

router = APIRouter(prefix="/parcels", tags=["parcels"])
store = ParcelStore()


class ParcelBatch(BaseModel):
    group_id: str
    items: list[dict[str, Any]]


class ParcelItem(BaseModel):
    payload: dict[str, Any]


@router.post("/inbox")
def put_inbox(body: ParcelBatch) -> dict:
    try:
        return {"ok": True, "result": store.put_many(body.group_id, body.items)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/inbox")
def list_inbox() -> dict:
    return {"items": store.list_inbox()}


@router.post("/outbox")
def put_outbox(body: ParcelItem) -> dict:
    try:
        return {"ok": True, "result": store.put_outbox(body.payload)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/outbox")
def list_outbox() -> dict:
    return {"items": store.list_outbox()}
