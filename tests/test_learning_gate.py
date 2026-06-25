from api.learning_gate import build_eval_payload, metric_score_from_result


def test_metric_score_from_result() -> None:
    score = metric_score_from_result({"artifact": {"metrics": {"avg_eval_loss": 0.5, "accepted_checkpoints": 1}}})
    assert 0.0 < score <= 1.0


def test_build_eval_payload() -> None:
    payload = build_eval_payload({"artifact": {"model_id": "ailovanta-owned", "version": "candidate", "metrics": {}}})
    assert payload["candidate_model"] == "ailovanta-owned:candidate"
    assert payload["metrics"]
