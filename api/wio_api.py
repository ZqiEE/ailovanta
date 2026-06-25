from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.parcel_store import ParcelStore
from api.wio import task_envelope, verify_result

router = APIRouter(prefix="/wio", tags=["wio"])
store = ParcelStore()


class TaskBody(BaseModel):
    plan: dict[str, Any]
    node_id: str
    input_uri: str
    output_uri: str


class ResultBody(BaseModel):
    payload: dict[str, Any]
    require_valid: bool = True


@router.post("/task")
def create_task(body: TaskBody) -> dict[str, Any]:
    item = task_envelope(body.plan, body.node_id, body.input_uri, body.output_uri)
    store.put_many("worker_tasks", [item])
    return {"ok": True, "item": item}


@router.post("/result")
def submit_result(body: ResultBody) -> dict[str, Any]:
    checked = verify_result(body.payload)
    if body.require_valid and not checked.get("ok"):
        raise HTTPException(status_code=400, detail=checked)
    item = store.put_outbox(body.payload)
    return {"ok": True, "checked": checked, "item": item}
