from __future__ import annotations

import hashlib
import json
from time import time
from typing import Any


SCHEMA = "ailovanta.owned_promotion_proof.v1"


def build_owned_promotion_proof(
    binding: dict[str, Any],
    *,
    runtime_id: str,
    node_id: str,
    route_key: str,
) -> dict[str, Any]:
    metadata = binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}
    gate = metadata.get("promotion_gate") if isinstance(metadata.get("promotion_gate"), dict) else {}
    receipt = metadata.get("training_worker_receipt") if isinstance(metadata.get("training_worker_receipt"), dict) else {}
    model_eval = gate.get("model_eval") if isinstance(gate.get("model_eval"), dict) else {}
    runtime_evidence = model_eval.get("runtime_evidence") if isinstance(model_eval.get("runtime_evidence"), dict) else {}
    code_generation_eval = gate.get("code_generation_eval") if isinstance(gate.get("code_generation_eval"), dict) else {}
    artifact_distribution = gate.get("artifact_distribution") if isinstance(gate.get("artifact_distribution"), dict) else {}
    artifact_integrity = gate.get("artifact_integrity") if isinstance(gate.get("artifact_integrity"), dict) else {}

    proof = {
        "schema_version": SCHEMA,
        "model_key": binding.get("model_key"),
        "binding_id": binding.get("binding_id"),
        "artifact_hash": binding.get("artifact_hash"),
        "backend_kind": binding.get("backend_kind"),
        "route_key": route_key,
        "runtime_id": runtime_id,
        "node_id": node_id,
        "promotion_gate": {
            "ok": gate.get("ok"),
            "decision": gate.get("decision"),
            "blockers": gate.get("blockers", []),
        },
        "code_generation_eval": {
            "ok": code_generation_eval.get("ok"),
            "score": code_generation_eval.get("score"),
            "passed_cases": code_generation_eval.get("passed_cases"),
            "total_cases": code_generation_eval.get("total_cases"),
            "backend_kind": code_generation_eval.get("backend_kind"),
        },
        "training_worker_receipt": {
            "receipt_id": receipt.get("receipt_id"),
            "receipt_hash": receipt.get("receipt_hash"),
            "passed": receipt.get("passed"),
            "node_id": receipt.get("node_id"),
            "job_id": receipt.get("job_id"),
            "artifact_hash": receipt.get("artifact_hash"),
        },
        "runtime_evidence": {
            "requested_backend": runtime_evidence.get("requested_backend"),
            "actual_backend": runtime_evidence.get("actual_backend"),
            "real_training_executed": runtime_evidence.get("real_training_executed"),
            "fallback_used": runtime_evidence.get("fallback_used"),
            "gpu_execution_evidence": runtime_evidence.get("gpu_execution_evidence"),
            "trained_rows": runtime_evidence.get("trained_rows"),
        },
        "artifact_integrity": {
            "ok": artifact_integrity.get("ok"),
            "actual_hash": artifact_integrity.get("actual_hash"),
            "expected_hash": artifact_integrity.get("expected_hash"),
        },
        "artifact_distribution": {
            "ok": artifact_distribution.get("ok"),
            "manifest_hash": (artifact_distribution.get("distribution") or {}).get("manifest_hash") if isinstance(artifact_distribution.get("distribution"), dict) else None,
            "storage_artifact_hash": (artifact_distribution.get("distribution") or {}).get("storage_artifact_hash") if isinstance(artifact_distribution.get("distribution"), dict) else None,
        },
        "created_at": round(time(), 3),
    }
    proof["proof_hash"] = stable_hash({key: value for key, value in proof.items() if key != "proof_hash"})
    return proof


def promotion_proof_ok(proof: dict[str, Any] | None) -> bool:
    if not isinstance(proof, dict):
        return False
    proof_hash = proof.get("proof_hash")
    expected_hash = stable_hash({key: value for key, value in proof.items() if key != "proof_hash"})
    return (
        proof.get("schema_version") == SCHEMA
        and proof_hash == expected_hash
        and proof.get("promotion_gate", {}).get("ok") is True
        and proof.get("code_generation_eval", {}).get("ok") is True
        and proof.get("training_worker_receipt", {}).get("passed") is True
        and proof.get("runtime_evidence", {}).get("real_training_executed") is True
        and proof.get("runtime_evidence", {}).get("fallback_used") is not True
        and proof.get("artifact_integrity", {}).get("ok") is True
        and proof.get("artifact_distribution", {}).get("ok") is True
    )


def stable_hash(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()
