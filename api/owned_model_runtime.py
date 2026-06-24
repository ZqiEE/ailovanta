from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from api.worker_transport import WorkerInferenceClient, WorkerInferenceRequest, WorkerInferenceUnavailable


PolicyMode = Literal["standard", "open_research"]


@dataclass(frozen=True)
class OwnedModelRequest:
    prompt: str
    model_id: str = "ailovanta-owned"
    version: str = "candidate"
    policy_mode: PolicyMode = "open_research"
    user_id: str = "local"
    conversation_id: str | None = None


@dataclass(frozen=True)
class OwnedModelResult:
    answer: str
    source: str
    model_id: str
    version: str
    runtime_route: dict
    policy_mode: PolicyMode


class OwnedModelUnavailable(RuntimeError):
    pass


class OwnedModelRuntime:
    def __init__(self, runtime_registry, worker_client: WorkerInferenceClient | None = None) -> None:
        self.runtime_registry = runtime_registry
        self.worker_client = worker_client or WorkerInferenceClient()

    def route(self, request: OwnedModelRequest) -> dict:
        from api.runtime_router import RuntimeRequest

        return self.runtime_registry.route(
            RuntimeRequest(
                request_id=f"owned-{request.conversation_id or request.user_id}",
                model_id=request.model_id,
                version=request.version,
                task_type="chat_completion",
                privacy_level="protected",
                latency_target_ms=2000,
                max_price_per_1k_tokens=0.1,
                region_hint="auto",
                verification_required=True,
            )
        )

    def generate(self, request: OwnedModelRequest) -> OwnedModelResult:
        route = self.route(request)
        if not route.get("assigned"):
            raise OwnedModelUnavailable("no verified Ailovanta runtime manifest is available")

        assignment = route.get("assignment") or {}
        manifest_hash = assignment.get("model_manifest_hash")
        runtime_id = assignment.get("runtime_id")
        node_id = assignment.get("node_id")
        if not manifest_hash:
            raise OwnedModelUnavailable("assigned runtime has no model manifest hash")
        if not runtime_id or not node_id:
            raise OwnedModelUnavailable("assigned runtime is missing runtime_id or node_id")

        try:
            worker_result = self.worker_client.infer(
                WorkerInferenceRequest(
                    prompt=request.prompt,
                    model_id=request.model_id,
                    version=request.version,
                    policy_mode=request.policy_mode,
                    runtime_id=runtime_id,
                    node_id=node_id,
                    model_manifest_hash=manifest_hash,
                )
            )
        except WorkerInferenceUnavailable as exc:
            raise OwnedModelUnavailable(f"worker inference unavailable: {exc}") from exc

        return OwnedModelResult(
            answer=worker_result.answer,
            source=worker_result.source,
            model_id=request.model_id,
            version=request.version,
            runtime_route=route,
            policy_mode=request.policy_mode,
        )
