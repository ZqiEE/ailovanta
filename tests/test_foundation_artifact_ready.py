from __future__ import annotations

from api.foundation_artifact_ready import check_foundation_artifact_ready


def test_artifact_ready_smoke() -> None:
    result = check_foundation_artifact_ready(model_key="missing:model")
    assert result["ok"] is False
    assert "no_active_binding" in result["blockers"]
