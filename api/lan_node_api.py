from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.node_trust import NodeTrustStore
from api.runtime_forwarder import RuntimeEndpointStore
from api.runtime_router import RuntimeNodeProfile
from api.runtime_store import RuntimeStore

router = APIRouter(prefix="/lan", tags=["lan-node"])
trust_store = NodeTrustStore()
runtime_store = RuntimeStore()
endpoint_store = RuntimeEndpointStore()


class LanJoinRequest(BaseModel):
    node_id: str = Field(min_length=1)
    runtime_id: str = "rt-owned-1"
    worker_url: str = Field(min_length=1)
    secret: str = "lan-local-secret"
    gpu_memory_gb: float = 0.0
    available_gpu_memory_gb: float | None = None
    trust_score: float = 0.8
    region: str = "lan"
    cached_models: list[str] = ["ailovanta-owned:candidate"]
    supported_engines: list[str] = ["ailovanta-worker"]
    metadata: dict[str, Any] = {}


@router.post("/nodes/join")
def join_lan_node(body: LanJoinRequest) -> dict[str, Any]:
    node = trust_store.register(
        body.node_id,
        body.secret,
        trust_score=body.trust_score,
        metadata={"source": "lan_join", "worker_url": body.worker_url, **body.metadata},
    )
    runtime = runtime_store.register_runtime(
        RuntimeNodeProfile(
            runtime_id=body.runtime_id,
            node_id=body.node_id,
            pool="trusted_runtime_pool",
            region=body.region,
            status="online",
            gpu_memory_gb=body.gpu_memory_gb,
            available_gpu_memory_gb=body.available_gpu_memory_gb if body.available_gpu_memory_gb is not None else body.gpu_memory_gb,
            trust_score=body.trust_score,
            current_load=0.0,
            price_per_1k_tokens=0.0,
            latency_ms=200,
            supported_engines=body.supported_engines,
            cached_models=body.cached_models,
            cached_adapters=[],
        )
    )
    endpoint = endpoint_store.register(body.runtime_id, body.worker_url, body.secret)
    return {"ok": True, "node": node, "runtime": runtime, "endpoint": endpoint, "stage": "lan_node_joined"}


@router.get("/nodes")
def list_lan_nodes() -> dict[str, Any]:
    runtimes = [item for item in runtime_store.list_runtimes() if item.get("region") == "lan"]
    return {"ok": True, "nodes": trust_store.list_nodes(), "lan_runtimes": runtimes, "endpoints": endpoint_store.all()}
