from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app, store
from api.storage import SchedulerStore


def test_reputation_endpoints() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        local_store = SchedulerStore(Path(tmp) / "scheduler.sqlite3")
        original_path = store.path
        store.path = local_store.path
        try:
            client = TestClient(app)
            client.post(
                "/nodes/register",
                json={
                    "node_id": "node_reputation_test",
                    "device_name": "rep-node",
                    "cpu_threads": 8,
                    "memory_gb": 16,
                    "has_gpu": True,
                    "gpu_name": "test-gpu",
                    "contribution_percent": 30,
                },
            )
            leaderboard = client.get("/reputation/leaderboard")
            assert leaderboard.status_code == 200
            body = leaderboard.json()
            assert "nodes" in body
            assert body["nodes"][0]["node_id"] == "node_reputation_test"
            assert "reputation_score" in body["nodes"][0]

            summary = client.get("/reputation/summary")
            assert summary.status_code == 200
            assert summary.json()["nodes"] >= 1
        finally:
            store.path = original_path
