from api.owned_model_readiness import classify_owned_model_readiness
from api.owned_promotion_proof import stable_hash


def _ready_promotion_proof() -> dict:
    proof = {
        "schema_version": "ailovanta.owned_promotion_proof.v1",
        "promotion_gate": {"ok": True},
        "code_generation_eval": {"ok": True},
        "training_worker_receipt": {"passed": True},
        "runtime_evidence": {"real_training_executed": True, "fallback_used": False},
        "artifact_integrity": {"ok": True},
        "artifact_distribution": {"ok": True},
        "created_at": 1.0,
    }
    proof["proof_hash"] = stable_hash(proof)
    return proof


def test_readiness_marks_bootstrap_as_connected_not_self_trained() -> None:
    result = classify_owned_model_readiness(
        {
            "status": "active",
            "backend_kind": "checkpoint-artifact",
            "metadata": {"source": "bootstrap_owned_runtime"},
        }
    )

    assert result["stage"] == "bootstrap_connected"
    assert result["owned_model_ready"] is False
    assert result["self_trained_ready"] is False
    assert "bootstrap_not_self_trained" in result["blockers"]


def test_readiness_marks_real_training_artifact_ready() -> None:
    result = classify_owned_model_readiness(
        {
            "status": "active",
            "backend_kind": "transformers-local",
            "metadata": {
                "promotion_gate": {
                    "ok": True,
                    "model_eval": {
                        "runtime_evidence": {
                            "actual_backend": "lora",
                            "real_training_executed": True,
                        }
                    },
                },
                "training_worker_receipt": {"passed": True},
                "route_publish": {"ok": True},
                "promotion_proof": _ready_promotion_proof(),
            },
        }
    )

    assert result["stage"] == "self_trained_ready"
    assert result["owned_model_ready"] is True
    assert result["self_trained_ready"] is True
    assert result["blockers"] == []


def test_readiness_blocks_real_artifact_without_worker_receipt() -> None:
    result = classify_owned_model_readiness(
        {
            "status": "active",
            "backend_kind": "transformers-local",
            "metadata": {
                "promotion_gate": {
                    "ok": True,
                    "model_eval": {
                        "runtime_evidence": {
                            "actual_backend": "lora",
                            "real_training_executed": True,
                        }
                    },
                }
            },
        }
    )

    assert result["stage"] == "self_trained_candidate"
    assert result["self_trained_ready"] is False
    assert "training_worker_receipt_not_passed" in result["blockers"]


def test_readiness_blocks_real_artifact_without_promotion_proof() -> None:
    result = classify_owned_model_readiness(
        {
            "status": "active",
            "backend_kind": "transformers-local",
            "metadata": {
                "promotion_gate": {
                    "ok": True,
                    "model_eval": {
                        "runtime_evidence": {
                            "actual_backend": "lora",
                            "real_training_executed": True,
                        }
                    },
                },
                "training_worker_receipt": {"passed": True},
                "route_publish": {"ok": True},
            },
        }
    )

    assert result["stage"] == "self_trained_candidate"
    assert result["self_trained_ready"] is False
    assert "promotion_proof_not_ok" in result["blockers"]
