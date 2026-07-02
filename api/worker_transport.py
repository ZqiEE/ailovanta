from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


class WorkerInferenceUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkerInferenceRequest:
    prompt: str
    model_id: str
    version: str
    policy_mode: str
    runtime_id: str
    node_id: str
    model_manifest_hash: str


@dataclass(frozen=True)
class WorkerInferenceResult:
    answer: str
    source: str
    worker_url: str
    runtime_id: str
    node_id: str
    raw: dict[str, Any]


class WorkerInferenceClient:
    def __init__(self, timeout_seconds: float | None = None) -> None:
        self.timeout_seconds = timeout_seconds or float(os.getenv("AILOVANTA_WORKER_TIMEOUT_SECONDS", "60"))

    def infer(self, request: WorkerInferenceRequest) -> WorkerInferenceResult:
        try:
            worker_url = self.worker_url(request.runtime_id)
        except WorkerInferenceUnavailable:
            return self.infer_local_artifact(request)
        payload = {
            "prompt": request.prompt,
            "model_id": request.model_id,
            "version": request.version,
            "policy_mode": request.policy_mode,
            "runtime_id": request.runtime_id,
            "node_id": request.node_id,
            "model_manifest_hash": request.model_manifest_hash,
        }
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{worker_url}/v1/owned/infer", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise WorkerInferenceUnavailable(str(exc)) from exc

        answer = str(data.get("answer") or "").strip()
        if not answer:
            raise WorkerInferenceUnavailable("worker returned empty answer")
        return WorkerInferenceResult(
            answer=answer,
            source="ailovanta-worker",
            worker_url=worker_url,
            runtime_id=request.runtime_id,
            node_id=request.node_id,
            raw=data,
        )

    def infer_local_artifact(self, request: WorkerInferenceRequest) -> WorkerInferenceResult:
        if os.getenv("AILOVANTA_DISABLE_LOCAL_ARTIFACT_WORKER", "").lower() in {"1", "true", "yes"}:
            raise WorkerInferenceUnavailable(f"worker url not configured for runtime: {request.runtime_id}")
        from api.artifact_binding import ArtifactBindingStore
        from api.local_runtime import LocalRuntime

        model_key = f"{request.model_id}:{request.version}"
        binding = ArtifactBindingStore().latest_for_model(model_key, active_only=True)
        if not binding:
            raise WorkerInferenceUnavailable("no active artifact binding for " + model_key)
        location = str(binding.get("backend_ref") or binding.get("checkpoint_uri") or "")
        if not location:
            raise WorkerInferenceUnavailable("artifact binding has no backend_ref or checkpoint_uri")
        runtime = LocalRuntime()
        loaded = runtime.load(model_key, location)
        generated = runtime.generate(model_key, request.prompt, max_new_tokens=int(os.getenv("AILOVANTA_LOCAL_WORKER_MAX_NEW_TOKENS", "128")))
        answer = str(generated.get("text") or generated.get("answer") or "").strip()
        if not answer:
            raise WorkerInferenceUnavailable("local artifact runtime returned empty answer")
        raw = {"binding": binding, "loaded": loaded, "generated": generated, "local_artifact_worker": True}
        return WorkerInferenceResult(
            answer=answer,
            source="ailovanta-local-artifact-worker",
            worker_url="local-artifact://" + request.runtime_id,
            runtime_id=request.runtime_id,
            node_id=request.node_id,
            raw=raw,
        )

    @staticmethod
    def worker_url(runtime_id: str) -> str:
        key = "AILOVANTA_WORKER_URL_" + runtime_id.upper().replace("-", "_")
        specific = os.getenv(key)
        if specific:
            return specific.rstrip("/")
        default = os.getenv("AILOVANTA_DEFAULT_WORKER_URL")
        if default:
            return default.rstrip("/")
        raise WorkerInferenceUnavailable(f"worker url not configured for runtime: {runtime_id}")
