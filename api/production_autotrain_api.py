from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.autotrain import run_autotrain
from api.model_score_store import ModelScoreStore
from api.training_proof import extract_metrics, training_proof

router = APIRouter(prefix="/production-autotrain", tags=["production-autotrain"])
score_store = ModelScoreStore()


class ProductionAutoTrainRequest(BaseModel):
    model_id: str = "ailovanta-owned"
    target_version: str = "candidate"
    min_delta: float = 0.0
    score_fallback: float = 0.0
    core_path: str | None = None
    work_dir: str = "runtime_data/production_autotrain_pipeline"
    min_events: int = 1
    event_limit: int = 1000
    reuse_latest_pack: bool = True
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


def write_audit(run_id: str, payload: dict[str, Any]) -> str:
    root = Path("runtime_data/production_autotrain")
    root.mkdir(parents=True, exist_ok=True)
    path = root / (run_id + ".json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


@router.post("/run")
def run_production_autotrain(body: ProductionAutoTrainRequest) -> dict[str, Any]:
    run_id = "prod_autotrain_" + uuid4().hex[:12]
    model_key = body.model_id + ":" + body.target_version
    try:
        result = run_autotrain(
            core_path=body.core_path,
            work_dir=body.work_dir,
            min_events=body.min_events,
            event_limit=body.event_limit,
            reuse_latest_pack=body.reuse_latest_pack,
            allow_shadow_import=body.allow_shadow_import,
            execute_checkpoints=body.execute_checkpoints,
            checkpoint_output_root=body.checkpoint_output_root,
            training_command=body.training_command,
            model_backend=body.model_backend,
            base_model=body.base_model,
            backend_output_dir=body.backend_output_dir,
            backend_device=body.backend_device,
            backend_max_steps=body.backend_max_steps,
            backend_lr=body.backend_lr,
            prepare_runtime=body.prepare_runtime,
            runtime_id=body.runtime_id,
            node_id=body.node_id,
            gpu_memory_gb=body.gpu_memory_gb,
            model_id=body.model_id,
            target_version=body.target_version,
            max_steps=body.max_steps,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    best = score_store.best(model_key)
    previous_best = float(best["score"]) if best else None
    metrics = extract_metrics(result)
    proof = training_proof(model_key, metrics, previous_best, min_delta=body.min_delta, fallback=body.score_fallback)
    record = score_store.record(model_key, proof["candidate_score"], "production_autotrain", {"run_id": run_id, "proof": proof})
    audit = {
        "ok": bool(proof["accepted"]),
        "stage": "accepted" if proof["accepted"] else "rejected",
        "run_id": run_id,
        "created_at": round(time(), 3),
        "proof": proof,
        "score_record": record,
        "autotrain": result,
    }
    audit["audit_path"] = write_audit(run_id, audit)
    return audit


@router.get("/audits")
def list_audits() -> dict[str, Any]:
    root = Path("runtime_data/production_autotrain")
    if not root.exists():
        return {"ok": True, "items": []}
    return {"ok": True, "items": [str(path) for path in root.glob("prod_autotrain_*.json")]}
