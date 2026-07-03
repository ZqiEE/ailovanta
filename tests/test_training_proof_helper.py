from api.training_proof import candidate_score, training_proof


def test_score_uses_explicit_value() -> None:
    assert candidate_score({"score": 0.8, "eval_loss": 0.9}) == 0.8


def test_score_can_use_eval_loss() -> None:
    assert candidate_score({"eval_loss": 0.25}) == 0.75


def test_proof_rejects_lower_candidate() -> None:
    proof = training_proof("ailovanta-owned:candidate", {"score": 0.4}, previous_best=0.5)
    assert proof["accepted"] is False


def test_proof_accepts_better_candidate() -> None:
    proof = training_proof("ailovanta-owned:candidate", {"score": 0.6}, previous_best=0.5)
    assert proof["accepted"] is True
