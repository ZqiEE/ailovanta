from api.artifact_binding import ArtifactBindingStore
from api.model_monitor import ModelMonitorStore
from api.rollback_executor import RollbackExecutor
from api.route_book import RouteBook
from api.runtime_store import RuntimeStore


def test_rollback_disables_bad_route(tmp_path) -> None:
    routes = RouteBook(tmp_path / "routes.sqlite3")
    routes.set_active("owned-chat/default", "bad:model")
    monitor = ModelMonitorStore(tmp_path / "monitor")
    runtime = RuntimeStore(tmp_path / "runtime.sqlite3")
    bindings = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    executor = RollbackExecutor(monitor=monitor, runtime=runtime, binding_store=bindings, route_book=routes, log_root=tmp_path / "logs")
    result = executor.execute_action({"action": "rollback", "model": "bad:model", "action_id": "a1"})
    assert result["executed"] is True
    assert routes.active("owned-chat/default") is None
    assert result["route_update"]["count"] >= 1
