from pathlib import Path

from api.model_score_store import ModelScoreStore


def test_model_score_accepts_first_and_rejects_lower_score(tmp_path: Path) -> None:
    store = ModelScoreStore(tmp_path / "scores.sqlite3")
    decision = store.should_accept("ailovanta-owned:candidate", 0.5)
    assert decision["accept"] is True
    store.record("ailovanta-owned:candidate", 0.5, "test")
    lower = store.should_accept("ailovanta-owned:candidate", 0.4)
    assert lower["accept"] is False
    higher = store.should_accept("ailovanta-owned:candidate", 0.6)
    assert higher["accept"] is True
