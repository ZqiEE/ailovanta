from __future__ import annotations

from api.owned_promotion_proof import build_owned_promotion_proof, promotion_proof_ok


def _real_binding() -> dict:
    artifact_hash = "sha256:" + "a" * 64
    return {
        "model_key": "ailovanta-owned:candidate",
        "binding_id": "bind-1",
        "artifact_hash": artifact_hash,
        "backend_kind": "transformers-local",
        "metadata": {
            "promotion_gate": {
                "ok": True,
                "decision": "promote_active",
                "blockers": [],
                "code_generation_eval": {
                    "ok": True,
                    "score": 1.0,
                    "passed_cases": 3,
                    "total_cases": 3,
                    "backend_kind": "transformers-local",
                },
                "model_eval": {
                    "runtime_evidence": {
                        "requested_backend": "qlora",
                        "actual_backend": "qlora",
                        "real_training_executed": True,
                        "fallback_used": False,
                        "gpu_execution_evidence": {"device_count": 1},
                        "trained_rows": 128,
                    }
                },
                "artifact_integrity": {
                    "ok": True,
                    "actual_hash": artifact_hash,
                    "expected_hash": artifact_hash,
                },
                "artifact_distribution": {
                    "ok": True,
                    "distribution": {
                        "manifest_hash": "sha256:" + "b" * 64,
                        "storage_artifact_hash": artifact_hash,
                    },
                },
            },
            "training_worker_receipt": {
                "receipt_id": "receipt-1",
                "receipt_hash": "sha256:" + "c" * 64,
                "passed": True,
                "node_id": "node-1",
                "job_id": "job-1",
                "artifact_hash": artifact_hash,
            },
        },
    }


def test_owned_promotion_proof_accepts_complete_real_training_chain() -> None:
    proof = build_owned_promotion_proof(_real_binding(), runtime_id="runtime-1", node_id="node-1", route_key="owned-chat/default")

    assert proof["proof_hash"].startswith("sha256:")
    assert proof["promotion_gate"]["ok"] is True
    assert proof["runtime_evidence"]["real_training_executed"] is True
    assert promotion_proof_ok(proof) is True


def test_owned_promotion_proof_rejects_missing_codegen_eval() -> None:
    binding = _real_binding()
    binding["metadata"]["promotion_gate"]["code_generation_eval"]["ok"] = False

    proof = build_owned_promotion_proof(binding, runtime_id="runtime-1", node_id="node-1", route_key="owned-chat/default")

    assert promotion_proof_ok(proof) is False
