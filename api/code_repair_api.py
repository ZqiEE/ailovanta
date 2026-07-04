from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.code_repair import CodeRepairError, verified_repair

router = APIRouter(prefix="/code-repair", tags=["code-repair"])


class RepairRequest(BaseModel):
    project_dir: str
    test_command: str = "pytest"
    replacements: list[dict[str, str]] | None = None
    project_hint: str = ""


@router.post("/run")
def run_repair(body: RepairRequest) -> dict[str, Any]:
    try:
        return verified_repair(body.project_dir, body.test_command, replacements=body.replacements, project_hint=body.project_hint)
    except (CodeRepairError, FileNotFoundError, TimeoutError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
