from pathlib import Path

from api.model_monitor import ModelMonitorStore
from api.rollback_executor import RollbackExecutor
from api.runtime_router import ModelManifest
from api.runtime_store import RuntimeStore


def test_rollback_executor_updates_runtime_status(tmp_path: Path) -> None:
    runtime = RuntimeStore(tmp_path / "runtime.sqlite3")
    runtime.register_model(
        ModelManifest(
            model_id="ailovanta-owned",
            version="baseline",
            manifest_hash="sha256:baseline",
            privacy_level="protected",
            min_gpu_memory_gb=0,
            allowed_pools=["trusted_runtime_pool"],
            quantization="local",
            context_length=8192,
            adapter_compatible=True,
            status="active",
        )
    )
    runtime.register_model(
        ModelManifest(
            model_id="ailovanta-owned",
            version="candidate",
            manifest_hash="sha256:candidate",
            privacy_level="protected",
            min_gpu_memory_gb=0,
            allowed_pools=["trusted_runtime_pool"],
            quantization="local",
            context_length=8192,
            adapter_compatible=True,
            status="active",
        )
    )
    monitor = ModelMonitorStore(tmp_path / "monitor")
    shadow = monitor.register_shadow("ailovanta-owned:candidate", "ailovanta-owned:baseline", artifact_hash="sha256:candidate")
    monitor.promote_live(shadow["shadow_id"])
    monitor.record_metric("ailovanta-owned:candidate", {"quality": 0.7}, mode="live")
    action = monitor.evaluate_rollback("ailovanta-owned:candidate", {"quality": 0.9}, max_drop=0.05)

    result = RollbackExecutor(monitor=monitor, runtime=runtime, log_root=tmp_path / "logs").execute_action(action)

    assert result["executed"] is True
    assert runtime.get_model("ailovanta-owned:candidate")["status"] == "rolled_back"
    assert runtime.get_model("ailovanta-owned:baseline")["status"] == "active"
