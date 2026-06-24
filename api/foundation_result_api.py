from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.foundation_result_import import import_foundation_result

router = APIRouter(prefix="/foundation/results", tags=["foundation-results"])


class FoundationResultImportRequest(BaseModel):
    plan: dict[str, Any]
    artifact: dict[str, Any]


@router.post("/import")
def import_result(body: FoundationResultImportRequest) -> dict:
    try:
        result = import_foundation_result(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "import_result": result}
