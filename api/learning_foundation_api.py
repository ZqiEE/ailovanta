from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.foundation_pipeline import run_foundation_pipeline
from api.learning_foundation import create_job_from_latest_pack

router = APIRouter(prefix="/learning/foundation", tags=["learning-foundation"])


class LearningJobRequest(BaseModel):
    model_id: str = "ailovanta-owned"
    target_version: str = "candidate"
    node_id: str = "learning_node_1"
    gpu_memory_gb: float = 24.0
    max_steps: int = 100


class LearningPipelineRequest(LearningJobRequest):
    core_path: str | None = None
    work_dir: str = "runtime_data/learning_foundation_pipeline"


@router.post("/jobs")
def create_learning_job(body: LearningJobRequest) -> dict:
    try:
        job = create_job_from_latest_pack(
            model_id=body.model_id,
            target_version=body.target_version,
            node_id=body.node_id,
            gpu_memory_gb=body.gpu_memory_gb,
            max_steps=body.max_steps,
        )
        return {"ok": True, "job": job}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run")
def run_learning_pipeline(body: LearningPipelineRequest) -> dict[str, Any]:
    try:
        job = create_job_from_latest_pack(
            model_id=body.model_id,
            target_version=body.target_version,
            node_id=body.node_id,
            gpu_memory_gb=body.gpu_memory_gb,
            max_steps=body.max_steps,
        )
        result = run_foundation_pipeline(job["job_id"], core_path=body.core_path, work_dir=body.work_dir)
        return {"ok": True, "job": job, "pipeline": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
