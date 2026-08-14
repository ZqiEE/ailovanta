from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.network_routes import build_network_router
from api.node_security import NodeTokenStore
from api.storage import SchedulerStore


def _client(tmp_path):
    store = SchedulerStore(tmp_path / "scheduler.sqlite3")
    with store.connect() as conn:
        conn.execute("DELETE FROM jobs")
    tokens = NodeTokenStore(tmp_path / "node_tokens.json")
    app = FastAPI()
    app.include_router(build_network_router(store, tokens))
    return TestClient(app), store


def _register_gpu(client: TestClient):
    response = client.post(
        "/nodes/register",
        json={
            "node_id": "node_security_test",
            "device_name": "Ailovanta Test Node",
            "cpu_threads": 16,
            "memory_gb": 64,
            "has_gpu": True,
            "gpu_name": "Test GPU",
            "gpu_memory_gb": 24,
            "contribution_percent": 30,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["node_id"] == "node_security_test"
    assert body.get("node_token")
    return body["node_token"]


def test_node_token_is_required_after_enrollment(tmp_path):
    client, _ = _client(tmp_path)
    token = _register_gpu(client)

    denied = client.post("/nodes/heartbeat", json={"node_id": "node_security_test", "status": "idle"})
    assert denied.status_code == 401

    ok = client.post(
        "/nodes/heartbeat",
        headers={"X-Ailovanta-Node-Token": token},
        json={"node_id": "node_security_test", "status": "idle"},
    )
    assert ok.status_code == 200

    hijack = client.post(
        "/nodes/register",
        json={
            "node_id": "node_security_test",
            "device_name": "attacker",
            "cpu_threads": 1,
            "memory_gb": 1,
            "has_gpu": False,
            "contribution_percent": 30,
        },
    )
    assert hijack.status_code == 401


def test_public_node_list_is_deidentified(tmp_path):
    client, _ = _client(tmp_path)
    _register_gpu(client)
    response = client.get("/network/nodes")
    assert response.status_code == 200
    node = response.json()["nodes"][0]
    assert "node_id" not in node
    assert "device_name" not in node
    assert node["gpu_memory_gb"] == 24


def test_public_inference_is_disabled_without_operator_token(tmp_path, monkeypatch):
    monkeypatch.delenv("AILOVANTA_PUBLIC_INFERENCE_TOKEN", raising=False)
    client, _ = _client(tmp_path)
    response = client.post(
        "/jobs/public-inference",
        json={"prompt": "public code task", "privacy_scope": "public"},
    )
    assert response.status_code == 503


def test_authenticated_public_inference_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("AILOVANTA_PUBLIC_INFERENCE_TOKEN", "job-secret")
    client, _ = _client(tmp_path)
    node_token = _register_gpu(client)

    wrong = client.post(
        "/jobs/public-inference",
        headers={"X-Ailovanta-Job-Token": "wrong"},
        json={"prompt": "fix the public example", "privacy_scope": "public", "min_gpu_memory_gb": 20},
    )
    assert wrong.status_code == 401

    queued = client.post(
        "/jobs/public-inference",
        headers={"X-Ailovanta-Job-Token": "job-secret"},
        json={"prompt": "fix the public example", "privacy_scope": "public", "min_gpu_memory_gb": 20},
    )
    assert queued.status_code == 200
    job_id = queued.json()["job_id"]

    no_token = client.get("/jobs/next", params={"node_id": "node_security_test"})
    assert no_token.status_code == 401

    assigned = client.get(
        "/jobs/next",
        params={"node_id": "node_security_test"},
        headers={"X-Ailovanta-Node-Token": node_token},
    )
    assert assigned.status_code == 200
    job = assigned.json()["job"]
    assert job["id"] == job_id
    assert job["payload"]["privacy_scope"] == "public"

    submitted = client.post(
        "/jobs/result",
        headers={"X-Ailovanta-Node-Token": node_token},
        json={
            "node_id": "node_security_test",
            "job_id": job_id,
            "status": "ok",
            "output_summary": '{"schema_version":"ailovanta.public_coding_inference.v1","answer":"done"}',
        },
    )
    assert submitted.status_code == 200

    result = client.get(
        f"/jobs/{job_id}/result",
        headers={"X-Ailovanta-Job-Token": "job-secret"},
    )
    assert result.status_code == 200
    assert result.json()["status"] == "done"
    assert "done" in result.json()["result"]["output_summary"]


def test_private_scope_never_enters_public_queue(tmp_path, monkeypatch):
    monkeypatch.setenv("AILOVANTA_PUBLIC_INFERENCE_TOKEN", "job-secret")
    client, _ = _client(tmp_path)
    response = client.post(
        "/jobs/public-inference",
        headers={"X-Ailovanta-Job-Token": "job-secret"},
        json={"prompt": "private source", "privacy_scope": "private"},
    )
    assert response.status_code == 422
