from __future__ import annotations

from api.execution_window import open_execution_window, window_is_active


def test_execution_window_is_active() -> None:
    window = open_execution_window("node_a", "pkg_a", "task_a", "runtime_a", seconds=60)
    assert window["window_id"].startswith("window_")
    assert window_is_active(window) is True
