from __future__ import annotations

import hmac
import os
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from api.ip_rate_guard import IpRateGuard
from api.node_capability_store import NodeCapabilityStore
from api.node_security import NodeTokenStore
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
    ollama_models: list[str] = Field(default_factory=list, max_length=128)
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


def build_network_router(
    store: SchedulerStore,
    node_tokens: NodeTokenStore | None = None,
    node_capabilities: NodeCapabilityStore | None = None,
    registration_guard: IpRateGuard | None = None,
) -> APIRouter:
    router = APIRouter(tags=["distributed-compute"])
    verifier = VerificationEngine()
    token_store = node_tokens or NodeTokenStore("runtime_data/coding_node_tokens.json")
    capability_store = node_capabilities or NodeCapabilityStore("runtime_data/coding_node_capabilities.json")
    enroll_guard = registration_guard or IpRateGuard(
        prefix="node_enroll",
        default_limit=12,
        default_window_seconds=600,
    )

    def require_node_token(node_id: str, token: str | None) -> None:
        if not store.get_node(node_id):
            raise HTTPException(status_code=404, detail="node not found")
        if not token_store.verify(token, node_id):
            raise HTTPException(status_code=401, detail="invalid node token")

    def require_job_token(token: str | None) -> None:
        configured = os.getenv("AILOVANTA_PUBLIC_INFERENCE_TOKEN", "")
        if not configured:
            raise HTTPException(status_code=503, detail="public inference enqueue is disabled")
        if not hmac.compare_digest(token or "", configured):
            raise HTTPException(status_code=401, detail="invalid job token")

    def eligible_for_inference(node: dict, body: PublicInferenceRequest) -> bool:
        if node.get("status") not in {"online", "idle"}:
            return False
        if not node.get("has_gpu"):
            return False
        if float(node.get("memory_gb") or 0) < body.min_memory_gb:
            return False
        if float(node.get("gpu_memory_gb") or 0) < body.min_gpu_memory_gb:
            return False
        return capability_store.supports_model(str(node.get("node_id") or ""), body.model)

    def claim_next_compatible_job(node_id: str) -> dict | None:
        node = store.get_node(node_id)
        if not node:
            return None
        with store.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status = 'queued' ORDER BY attempts ASC, created_at ASC LIMIT 100"
            ).fetchall()
            candidates = [dict(row) for row in rows]
            matches: list[dict] = []
            for job in candidates:
                if not store.router.can_assign(node, job)[0]:
                    continue
                job_type = job.get("job_type") or job.get("type")
                if job_type == "coding_inference":
                    payload = store.router.payload(job)
                    requested_model = str(payload.get("model") or "")
                    if not requested_model or not capability_store.supports_model(node_id, requested_model):
                        continue
                matches.append(job)
            if not matches:
                return None
            matches.sort(
                key=lambda job: (store.router.job_priority(job), -int(job.get("attempts", 0))),
                reverse=True,
            )
            chosen = matches[0]
            conn.execute(
                "UPDATE jobs SET status = 'assigned', assigned_to = ?, assigned_at = CURRENT_TIMESTAMP, attempts = attempts + 1 WHERE job_id = ? AND status = 'queued'",
                (node_id, chosen["job_id"]),
            )
            if conn.total_changes < 1:
                return None
        job = store.get_job(chosen["job_id"])
        return store._api_job(job) if job else None

    @router.post("/nodes/register")
    def register_node(
        body: NodeRegister,
        request: Request,
        x_ailovanta_node_token: str | None = Header(default=None, alias="X-Ailovanta-Node-Token"),
    ) -> dict:
        requested_id = body.node_id
        existing = store.get_node(requested_id) if requested_id else None
        known_tokens = token_store.all()
        if existing and requested_id in known_tokens and not token_store.verify(x_ailovanta_node_token, requested_id):
            raise HTTPException(status_code=401, detail="invalid node token")
        if not existing:
            client_host = request.client.host if request.client else "unknown"
            if not enroll_guard.allow(client_host):
                raise HTTPException(status_code=429, detail="node enrollment rate limit reached")

        node_payload = body.model_dump(exclude={"ollama_models"})
        node = store.register_node(node_payload)
        node_id = str(node["node_id"])
        capability_store.update(node_id, body.ollama_models)
        issued_token: str | None = None
        if node_id not in token_store.all():
            issued_token = token_store.issue(node_id)["token"]

        response = {
            "node_id": node_id,
            "score": node.get("score"),
            "trust": node.get("trust"),
            "status": node.get("status"),
            "has_gpu": bool(node.get("has_gpu")),
            "gpu_name": node.get("gpu_name"),
            "gpu_memory_gb": node.get("gpu_memory_gb"),
            "installed_model_count": len(capability_store.models(node_id)),
        }
        if issued_token:
            response["node_token"] = issued_token
        return response

    @router.post("/nodes/heartbeat")
    def heartbeat(
        body: Heartbeat,
        x_ailovanta_node_token: str | None = Header(default=None, alias="X-Ailovanta-Node-Token"),
    ) -> dict:
        require_node_token(body.node_id, x_ailovanta_node_token)
        node = store.update_heartbeat(body.node_id, body.status)
        return {"node_id": body.node_id, "status": node.get("status") if node else body.status}

    @router.get("/network/status")
    def network_status() -> dict:
        status = store.status()
        return {
            "nodes": status.get("nodes", 0),
            "queued_jobs": status.get("queued_jobs", 0),
            "assigned_jobs": status.get("assigned_jobs", 0),
            "done_jobs": status.get("done_jobs", 0),
            "failed_jobs": status.get("failed_jobs", 0),
            "passed_verifications": status.get("passed_verifications", 0),
            "node_enrollment_policy": enroll_guard.policy(),
        }

    @router.get("/network/nodes")
    def network_nodes(limit: int = 50) -> dict:
        nodes = store.list_nodes(max(1, min(limit, 200)))
        return {
            "nodes": [
                {
                    "has_gpu": bool(node.get("has_gpu")),
                    "gpu_name": node.get("gpu_name"),
                    "gpu_memory_gb": node.get("gpu_memory_gb"),
                    "memory_gb": node.get("memory_gb"),
                    "status": node.get("status"),
                    "contribution_percent": node.get("contribution_percent"),
                }
                for node in nodes
            ]
        }

    @router.get("/jobs/next")
    def next_job(
        node_id: str,
        x_ailovanta_node_token: str | None = Header(default=None, alias="X-Ailovanta-Node-Token"),
    ) -> dict:
        require_node_token(node_id, x_ailovanta_node_token)
        return {"job": claim_next_compatible_job(node_id)}

    @router.get("/jobs/{job_id}")
    def get_job(
        job_id: str,
        x_ailovanta_job_token: str | None = Header(default=None, alias="X-Ailovanta-Job-Token"),
    ) -> dict:
        require_job_token(x_ailovanta_job_token)
        job = store.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        item = store._api_job(job)
        item["payload"] = {
            key: value
            for key, value in item.get("payload", {}).items()
            if key not in {"prompt", "messages", "repository", "files"}
        }
        return item

    @router.get("/jobs/{job_id}/result")
    def get_job_result(
        job_id: str,
        x_ailovanta_job_token: str | None = Header(default=None, alias="X-Ailovanta-Job-Token"),
    ) -> dict:
        require_job_token(x_ailovanta_job_token)
        with store.connect() as conn:
            row = conn.execute(
                "SELECT * FROM results WHERE job_id = ? ORDER BY submitted_at DESC LIMIT 1", (job_id,)
            ).fetchone()
        if not row:
            job = store.get_job(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="job not found")
            return {"job_id": job_id, "status": job.get("status"), "result": None}
        result = dict(row)
        return {
            "job_id": job_id,
            "status": "done" if result.get("status") == "ok" else "failed",
            "result": {
                "status": result.get("status"),
                "output_summary": result.get("output_summary"),
                "submitted_at": result.get("submitted_at"),
            },
        }

    @router.post("/jobs/result")
    def submit_result(
        body: JobResult,
        x_ailovanta_node_token: str | None = Header(default=None, alias="X-Ailovanta-Node-Token"),
    ) -> dict:
        require_node_token(body.node_id, x_ailovanta_node_token)
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
    def enqueue_public_inference(
        body: PublicInferenceRequest,
        x_ailovanta_job_token: str | None = Header(default=None, alias="X-Ailovanta-Job-Token"),
    ) -> dict:
        require_job_token(x_ailovanta_job_token)
        eligible_nodes = [node for node in store.list_nodes(200) if eligible_for_inference(node, body)]
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
        return {
            "ok": True,
            "job_id": job["id"],
            "status": "queued" if eligible_nodes else "waiting_for_compatible_node",
            "eligible_nodes": len(eligible_nodes),
        }

    return router
