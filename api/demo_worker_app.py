from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from api.artifact_binding import ArtifactBindingStore

app = FastAPI(title="Ailovanta Worker", version="0.2.1")


class InferRequest(BaseModel):
    prompt: str
    model_id: str
    version: str
    policy_mode: str = "open_research"
    runtime_id: str
    node_id: str
    model_manifest_hash: str


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "ailovanta-worker"}


@app.post("/v1/owned/infer")
def infer(body: InferRequest) -> dict:
    model_key = body.model_id + ":" + body.version
    binding = ArtifactBindingStore().latest_for_model(model_key, active_only=True)
    return {
        "answer": "Ailovanta worker routed request for " + model_key,
        "source": "ailovanta-worker",
        "model_id": body.model_id,
        "version": body.version,
        "runtime_id": body.runtime_id,
        "node_id": body.node_id,
        "model_manifest_hash": body.model_manifest_hash,
        "policy_mode": body.policy_mode,
        "artifact_binding_found": binding is not None,
        "binding_id": binding.get("binding_id") if binding else None,
    }
