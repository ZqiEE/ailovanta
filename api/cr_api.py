from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from api.ckpt_run import newest_ref, run_ckpt

router = APIRouter(prefix="/ck", tags=["ck"])


class Body(BaseModel):
    text: str
    ref: str | None = None
    max_new: int = 80


@router.post("/run")
def run(body: Body) -> dict:
    ref = body.ref or newest_ref()
    if not ref:
        return {"ok": False, "error": "no checkpoint found"}
    try:
        result = run_ckpt(body.text, ref, body.max_new)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "checkpoint_ref": ref}
    return {"ok": True, **result}
