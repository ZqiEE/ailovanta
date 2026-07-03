from __future__ import annotations

from typing import Any


def extract_metrics(result: dict[str, Any]) -> dict[str, Any]:
    pipeline = result.get("pipeline") or {}
    out: dict[str, Any] = {}
    for key in ["metrics", "gate", "eval_gate", "promotion"]:
        value = pipeline.get(key)
        if isinstance(value, dict):
            out.update(value)
    artifact = pipeline.get("artifact") or pipeline.get("foundation_artifact")
    if isinstance(artifact, dict) and isinstance(artifact.get("metrics"), dict):
        out.update(artifact["metrics"])
    return out


def candidate_score(metrics: dict[str, Any], fallback: float = 0.0) -> float:
    for key in ["score", "candidate_score", "pass_rate", "quality_score", "eval_score"]:
        if key in metrics:
            try:
                return float(metrics[key])
            except Exception:
                pass
    for key in ["eval_loss", "avg_eval_loss"]:
        if key in metrics:
            try:
                return max(0.0, 1.0 - float(metrics[key]))
            except Exception:
                pass
    return fallback


def training_proof(model_key: str, metrics: dict[str, Any], previous_best: float | None, min_delta: float = 0.0, fallback: float = 0.0) -> dict[str, Any]:
    score = candidate_score(metrics, fallback=fallback)
    accepted = previous_best is None or score >= previous_best + min_delta
    return {
        "model_key": model_key,
        "candidate_score": score,
        "previous_best": previous_best,
        "min_delta": min_delta,
        "accepted": accepted,
        "reason": "improved_or_first_candidate" if accepted else "candidate_did_not_beat_previous_best",
        "metrics": metrics,
    }
