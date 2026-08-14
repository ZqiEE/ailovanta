from __future__ import annotations

from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.storage import SchedulerStore
from api.verification import VerificationEngine


class NodeRegister(BaseModel):
    node_id: str | None = None
    device_name: str
    cpu_threads: int = Field(ge=1)
    memory_gb: float = Field(ge=0)
    has_gpu: bool = False
    gpu_name: str | None = None
    gpu_memory_gb: float | None = Field(default=None, ge=0, le=1024)
    contribution_percent: int = Field(default=30, ge=1, le=90)


class Heartbeat(BaseModel):
    node_id: str
    status: Literal["online", "busy", "idle", "offline"] = "online"


class JobResult(BaseModel):
    node_id: str
    job_id: str
    status: Literal["ok", "failed"]
    output_summary: str = Field(max_length=200000)


class PublicInferenceRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=48000)
    model: str = "qwen2.5-coder:7b"
    privacy_scope: Literal["public", "synthetic"]
    context_length: int = Field(default=16384, ge=2048, le=131072)
    min_memory_gb: float = Field(default=8.0, ge=0, le=512)
    min_gpu_memory_gb: float = Field(default=6.0, ge=0, le=512)


def build_network_router(store: SchedulerStore) -> APIRouter:
    router = APIRouter(tags=["distributed-compute"])
    verifier = VerificationEngine()

    @router.post("/nodes/register")
    def register_node(body: NodeRegister) -> dict:
        return store.register_node(body.model_dump())

    @router.post("/nodes/heartbeat")
    def heartbeat(body: Heartbeat) -> dict:
        node = store.update_heartbeat(body.node_id, body.status)
        if not node:
            raise HTTPException(status_code=404, detail="node not found")
        return node

    @router.get("/network/status")
    def network_status() -> dict:
        return store.status()

    @router.get("/network/nodes")
    def network_nodes(limit: int = 50) -> dict:
        return {"nodes": store.list_nodes(max(1, min(limit, 200)))}

    @router.get("/jobs/next")
    def next_job(node_id: str) -> dict:
        return {"job": store.next_job(node_id)}

    @router.get("/jobs/{job_id}")
    def get_job(job_id: str) -> dict:
        job = store.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        return store._api_job(job)

    @router.post("/jobs/result")
    def submit_result(body: JobResult) -> dict:
        node = store.get_node(body.node_id)
        if not node:
            raise HTTPException(status_code=404, detail="node not found")
        job = store.get_job(body.job_id)
        if not job or job.get("assigned_to") != body.node_id:
            raise HTTPException(status_code=409, detail="job is not assigned to this node")
        result = store.submit_result(body.model_dump())
        checked = verifier.verify(result)
        verification = store.record_verification(
            result,
            score=float(checked["score"]),
            passed=bool(checked["passed"]),
            reason=str(checked["reason"]),
        )
        return {"ok": True, "result": result, "verification": verification}

    @router.post("/jobs/public-inference")
    def enqueue_public_inference(body: PublicInferenceRequest) -> dict:
        # This endpoint deliberately refuses a private scope. Private project
        # inference belongs on the owner's own Ailovanta Local runtime.
        job_id = "public_infer_" + uuid4().hex[:16]
        payload = {
            "prompt": body.prompt,
            "model": body.model,
            "privacy_scope": body.privacy_scope,
            "context_length": body.context_length,
            "requires_gpu": True,
            "min_memory_gb": body.min_memory_gb,
            "min_gpu_memory_gb": body.min_gpu_memory_gb,
            "priority": 70,
        }
        job = store.enqueue_job(job_id, "coding_inference", payload)
        return {"ok": True, "job": job}

    return router
