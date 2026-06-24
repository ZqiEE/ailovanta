from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.foundation_pipeline import run_foundation_pipeline

router = APIRouter(prefix="/foundation/pipeline", tags=["foundation-pipeline"])


class FoundationPipelineRequest(BaseModel):
    job_id: str
    core_path: str | None = None
    work_dir: str = "runtime_data/foundation_pipeline"


@router.post("/run")
def run_pipeline(body: FoundationPipelineRequest) -> dict:
    try:
        result = run_foundation_pipeline(body.job_id, core_path=body.core_path, work_dir=body.work_dir)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result
