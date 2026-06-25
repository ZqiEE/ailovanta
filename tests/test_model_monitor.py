from pathlib import Path

from api.model_monitor import ModelMonitorStore


def test_shadow_promote_and_rollback(tmp_path: Path) -> None:
    store = ModelMonitorStore(tmp_path / "monitor")
    shadow = store.register_shadow("candidate", "baseline", artifact_hash="sha256:test")
    live = store.promote_live(shadow["shadow_id"])
    assert live["model"] == "candidate"
    store.record_metric("candidate", {"quality": 0.7}, mode="live")
    action = store.evaluate_rollback("candidate", {"quality": 0.9}, max_drop=0.05)
    assert action["action"] == "rollback"
    assert action["drops"]["quality"] > 0
