from __future__ import annotations

from typing import Any, Protocol

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.coding_benchmark_suite import CodingBenchmarkError, score_domain, score_unified
from api.coding_factory import CodingFactoryError, CodingFactoryPlanner


class SchedulerStore(Protocol):
    def enqueue_job(self, job_id: str, job_type: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class ExpertJobRequest(BaseModel):
    expert: str
    base_model: str
    dataset_uri: str
    budget_steps: int = Field(default=100, ge=1, le=100000)
    autonomous: bool = True


class AutonomousCycleRequest(BaseModel):
    scores: dict[str, float]
    base_model: str
    dataset_uri_by_expert: dict[str, str]
    budget_steps: int = Field(default=100, ge=1, le=100000)


class UnificationRequest(BaseModel):
    base_model: str
    frontend_checkpoint: str
    backend_checkpoint: str
    repair_checkpoint: str
    method: str = "multi_teacher_on_policy_distillation"
    budget_steps: int = Field(default=100, ge=1, le=100000)


class DomainScoreRequest(BaseModel):
    metrics: dict[str, Any]


class UnifiedScoreRequest(BaseModel):
    frontend: float
    backend: float
    repair: float


def build_coding_router(store: SchedulerStore) -> APIRouter:
    planner = CodingFactoryPlanner()
    router = APIRouter(prefix="/coding", tags=["coding-model-factory"])

    @router.get("/experts")
    def list_experts() -> dict[str, Any]:
        return {"experts": [planner.expert_spec(name) for name in ("frontend", "backend", "repair")]}

    @router.post("/training/expert")
    def enqueue_expert_training(body: ExpertJobRequest) -> dict[str, Any]:
        try:
            job = planner.plan_expert_job(
                body.expert,  # type: ignore[arg-type]
                base_model=body.base_model,
                dataset_uri=body.dataset_uri,
                budget_steps=body.budget_steps,
                autonomous=body.autonomous,
            )
        except CodingFactoryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        queued = store.enqueue_job(job["job_id"], job["job_type"], job["payload"])
        return {"ok": True, "job": queued}

    @router.post("/training/next")
    def enqueue_autonomous_cycle(body: AutonomousCycleRequest) -> dict[str, Any]:
        try:
            cycle = planner.plan_autonomous_cycle(
                scores=body.scores,
                base_model=body.base_model,
                dataset_uri_by_expert=body.dataset_uri_by_expert,
                budget_steps=body.budget_steps,
            )
        except CodingFactoryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        job = cycle["job"]
        queued = store.enqueue_job(job["job_id"], job["job_type"], job["payload"])
        return {"ok": True, "selected_expert": cycle["selected_expert"], "job": queued}

    @router.post("/training/unify")
    def enqueue_unification(body: UnificationRequest) -> dict[str, Any]:
        job = planner.plan_unification_job(
            base_model=body.base_model,
            frontend_checkpoint=body.frontend_checkpoint,
            backend_checkpoint=body.backend_checkpoint,
            repair_checkpoint=body.repair_checkpoint,
            method=body.method,
            budget_steps=body.budget_steps,
        )
        queued = store.enqueue_job(job["job_id"], job["job_type"], job["payload"])
        return {"ok": True, "job": queued}

    @router.post("/score/{domain}")
    def score_specialist(domain: str, body: DomainScoreRequest) -> dict[str, Any]:
        try:
            return score_domain(domain, body.metrics)
        except CodingBenchmarkError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/score/unified/model")
    def score_unified_model(body: UnifiedScoreRequest) -> dict[str, Any]:
        return score_unified(body.frontend, body.backend, body.repair)

    return router
