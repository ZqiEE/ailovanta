from __future__ import annotations

from typing import Any


def benchmark_summary_from_binding(binding: dict[str, Any] | None) -> dict[str, Any]:
    if not binding:
        return {"ok": False, "available": False, "reason": "missing_binding"}
    metadata = binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}
    gate = metadata.get("promotion_gate") if isinstance(metadata.get("promotion_gate"), dict) else {}
    code_generation = gate.get("code_generation_eval") if isinstance(gate.get("code_generation_eval"), dict) else {}
    model_eval = gate.get("model_eval") if isinstance(gate.get("model_eval"), dict) else {}
    runtime_evidence = model_eval.get("runtime_evidence") if isinstance(model_eval.get("runtime_evidence"), dict) else {}
    if not code_generation:
        return {"ok": False, "available": False, "reason": "missing_code_generation_eval"}
    return {
        "ok": bool(code_generation.get("ok")),
        "available": True,
        "score": code_generation.get("score"),
        "passed_cases": code_generation.get("passed_cases"),
        "total_cases": code_generation.get("total_cases"),
        "backend_kind": code_generation.get("backend_kind"),
        "reason": code_generation.get("reason") or gate.get("decision"),
        "runtime_backend": runtime_evidence.get("actual_backend"),
        "real_training_executed": runtime_evidence.get("real_training_executed"),
        "trained_rows": runtime_evidence.get("trained_rows"),
    }
