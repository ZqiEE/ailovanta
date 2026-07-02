from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.autotrain import AutoTrainError, ensure_autotrain_pack, run_autotrain

router = APIRouter(prefix="/autotrain", tags=["autotrain"])


class AutoTrainPackRequest(BaseModel):
    min_events: int = Field(default=1, ge=1)
    event_limit: int = Field(default=1000, ge=1, le=10000)
    model_id: str = "ailovanta-owned"
    target_version: str = "candidate"
    reuse_latest_pack: bool = True


class AutoTrainRunRequest(AutoTrainPackRequest):
    core_path: str | None = None
    work_dir: str = "runtime_data/autotrain_pipeline"
    baseline_model: str = "ailovanta-owned:baseline"
    baseline_score: float = 0.45
    allow_shadow_import: bool = False
    execute_checkpoints: bool = False
    checkpoint_output_root: str | None = None
    training_command: str | None = None
    model_backend: str | None = None
    base_model: str | None = None
    backend_output_dir: str | None = None
    backend_device: str | None = None
    backend_max_steps: int | None = None
    backend_lr: float | None = None
    prepare_runtime: bool = True
    runtime_id: str = "rt-owned-1"
    node_id: str = "learning_node_1"
    gpu_memory_gb: float = 24.0
    max_steps: int = 100


@router.post("/pack")
def create_autotrain_pack(body: AutoTrainPackRequest) -> dict[str, Any]:
    try:
        return {"ok": True, **ensure_autotrain_pack(**body.model_dump())}
    except AutoTrainError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run")
def run_autotrain_endpoint(body: AutoTrainRunRequest) -> dict[str, Any]:
    try:
        return run_autotrain(**body.model_dump())
    except (AutoTrainError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status")
def autotrain_status() -> dict[str, Any]:
    default_core = Path("../ailovanta-core").resolve()
    return {
        "ok": True,
        "stage": "autotrain_api_ready",
        "core_default_exists": default_core.exists(),
        "core_default_path": str(default_core),
        "run_endpoint": "POST /autotrain/run",
        "pack_endpoint": "POST /autotrain/pack",
        "boundary": "This starts the automatic training loop, but real model improvement requires a configured core path and training backend.",
    }
