from __future__ import annotations

from typing import Any

from api.owned_promotion_proof import promotion_proof_ok


REAL_BACKENDS = {"transformers-local", "transformers-causal-lm"}
REAL_TRAINING_BACKENDS = {"transformers", "lora", "qlora"}


def classify_owned_model_readiness(binding: dict[str, Any] | None) -> dict[str, Any]:
    if not binding:
        return _status("missing", ready=False, self_trained=False, blockers=["missing_artifact_binding"])
    metadata = binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}
    backend_kind = str(binding.get("backend_kind") or "")
    source = str(metadata.get("source") or "")
    blockers: list[str] = []

    if binding.get("status") != "active":
        blockers.append("binding_not_active")

    gate = metadata.get("promotion_gate") if isinstance(metadata.get("promotion_gate"), dict) else {}
    receipt = metadata.get("training_worker_receipt") if isinstance(metadata.get("training_worker_receipt"), dict) else {}
    route_publish = metadata.get("route_publish") if isinstance(metadata.get("route_publish"), dict) else {}
    promotion_proof = metadata.get("promotion_proof") if isinstance(metadata.get("promotion_proof"), dict) else {}

    if backend_kind in REAL_BACKENDS:
        if gate.get("ok") is not True:
            blockers.append("promotion_gate_not_ok")
        if receipt.get("passed") is not True:
            blockers.append("training_worker_receipt_not_passed")
        if route_publish and route_publish.get("ok") is not True:
            blockers.append("route_publish_not_ok")
        if not promotion_proof_ok(promotion_proof):
            blockers.append("promotion_proof_not_ok")
        model_eval = gate.get("model_eval") if isinstance(gate.get("model_eval"), dict) else {}
        runtime_evidence = model_eval.get("runtime_evidence") if isinstance(model_eval.get("runtime_evidence"), dict) else {}
        if runtime_evidence.get("actual_backend") not in REAL_TRAINING_BACKENDS:
            blockers.append("runtime_evidence_not_real_training_backend")
        if runtime_evidence.get("real_training_executed") is not True:
            blockers.append("runtime_evidence_not_executed")
        return _status("self_trained_ready" if not blockers else "self_trained_candidate", ready=not blockers, self_trained=not blockers, blockers=blockers)

    if source == "bootstrap_owned_runtime" or backend_kind == "checkpoint-artifact":
        return _status("bootstrap_connected", ready=False, self_trained=False, blockers=blockers or ["bootstrap_not_self_trained"])

    if backend_kind == "lightweight-ngram":
        return _status("lightweight_candidate", ready=False, self_trained=False, blockers=blockers or ["lightweight_not_code_generation_model"])

    return _status("unknown_artifact", ready=False, self_trained=False, blockers=blockers or ["unknown_artifact_backend"])


def _status(stage: str, *, ready: bool, self_trained: bool, blockers: list[str]) -> dict[str, Any]:
    return {
        "stage": stage,
        "owned_model_ready": ready,
        "self_trained_ready": self_trained,
        "blockers": sorted(set(blockers)),
    }
