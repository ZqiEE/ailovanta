from api.runtime_quality import benchmark_summary_from_binding


def test_benchmark_summary_from_binding_reads_code_generation_eval() -> None:
    binding = {
        "metadata": {
            "promotion_gate": {
                "decision": "promote_active",
                "code_generation_eval": {
                    "ok": True,
                    "score": 1.0,
                    "passed_cases": 2,
                    "total_cases": 2,
                    "backend_kind": "transformers-local",
                },
                "model_eval": {
                    "runtime_evidence": {
                        "actual_backend": "qlora",
                        "real_training_executed": True,
                        "trained_rows": 64,
                    }
                },
            }
        }
    }

    summary = benchmark_summary_from_binding(binding)

    assert summary["ok"] is True
    assert summary["available"] is True
    assert summary["score"] == 1.0
    assert summary["runtime_backend"] == "qlora"
    assert summary["trained_rows"] == 64
