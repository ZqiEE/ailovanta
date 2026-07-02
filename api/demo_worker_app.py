from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from fastapi import FastAPI
from pydantic import BaseModel

from api.artifact_binding import ArtifactBindingStore

app = FastAPI(title="Ailovanta Worker", version="0.2.3")


class InferRequest(BaseModel):
    prompt: str
    model_id: str
    version: str
    policy_mode: str = "open_research"
    runtime_id: str
    node_id: str
    model_manifest_hash: str


def ref_path(value: str | None) -> Path | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme == "file":
        raw = unquote(parsed.path)
        if len(raw) >= 3 and raw[0] == "/" and raw[2] == ":":
            raw = raw[1:]
        return Path(raw)
    if parsed.scheme == "":
        return Path(value)
    return None


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "ailovanta-worker"}


@app.post("/v1/owned/infer")
def infer(body: InferRequest) -> dict:
    model_key = body.model_id + ":" + body.version
    binding = ArtifactBindingStore().latest_for_model(model_key, active_only=True)
    backend_kind = binding.get("backend_kind") if binding else None
    backend_ref = binding.get("backend_ref") if binding else None
    path = ref_path(backend_ref)
    path_ready = bool(path and path.exists())
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
        "backend_kind": backend_kind,
        "backend_ref": backend_ref,
        "artifact_path_ready": path_ready,
        "artifact_path": str(path) if path else None,
    }
