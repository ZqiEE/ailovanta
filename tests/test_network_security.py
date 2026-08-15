from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.ip_rate_guard import IpRateGuard
from api.network_routes import build_network_router
from api.node_capability_store import NodeCapabilityStore
from api.node_security import NodeTokenStore
from api.storage import SchedulerStore


def _client(tmp_path, registration_guard=None):
    store = SchedulerStore(tmp_path / "scheduler.sqlite3")
    with store.connect() as conn:
        conn.execute("DELETE FROM jobs")
    tokens = NodeTokenStore(tmp_path / "node_tokens.json")
    capabilities = NodeCapabilityStore(tmp_path / "node_capabilities.json")
    app = FastAPI()
    app.include_router(build_network_router(store, tokens, capabilities, registration_guard))
    return TestClient(app), store, capabilities


def _register_gpu(client: TestClient, node_id: str = "node_security_test", models=None):
    response = client.post(
        "/nodes/register",
        json={
            "node_id": node_id,
            "device_name": "Ailovanta Test Node",
            "cpu_threads": 16,
            "memory_gb": 64,
            "has_gpu": True,
            "gpu_name": "Test GPU",
            "gpu_memory_gb": 24,
            "ollama_models": models if models is not None else ["qwen2.5-coder:7b"],
            "contribution_percent": 30,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["node_id"] == node_id
    assert body.get("node_token")
    return body["node_token"]


def test_node_token_is_required_after_enrollment(tmp_path):
    client, _, _ = _client(tmp_path)
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


def test_public_node_list_is_deidentified_and_hides_model_inventory(tmp_path):
    client, _, capabilities = _client(tmp_path)
    _register_gpu(client)
    assert capabilities.supports_model("node_security_test", "qwen2.5-coder:7b") is True
    response = client.get("/network/nodes")
    assert response.status_code == 200
    node = response.json()["nodes"][0]
    assert "node_id" not in node
    assert "device_name" not in node
    assert "ollama_models" not in node
    assert node["gpu_memory_gb"] == 24


def test_new_node_enrollment_is_rate_limited_but_existing_tokenized_node_can_refresh(tmp_path):
    guard = IpRateGuard(prefix="test_enroll", default_limit=2, default_window_seconds=600)
    client, _, _ = _client(tmp_path, guard)
    token_a = _register_gpu(client, "node_a")
    _register_gpu(client, "node_b")

    blocked = client.post(
        "/nodes/register",
        json={
            "node_id": "node_c",
            "device_name": "Ailovanta Test Node",
            "cpu_threads": 8,
            "memory_gb": 16,
            "has_gpu": False,
            "ollama_models": [],
            "contribution_percent": 30,
        },
    )
    assert blocked.status_code == 429

    refresh = client.post(
        "/nodes/register",
        headers={"X-Ailovanta-Node-Token": token_a},
        json={
            "node_id": "node_a",
            "device_name": "Ailovanta Test Node",
            "cpu_threads": 16,
            "memory_gb": 64,
            "has_gpu": True,
            "gpu_name": "Test GPU",
            "gpu_memory_gb": 24,
            "ollama_models": ["qwen2.5-coder:7b"],
            "contribution_percent": 30,
        },
    )
    assert refresh.status_code == 200
    assert "node_token" not in refresh.json()


def test_public_inference_is_disabled_without_operator_token(tmp_path, monkeypatch):
    monkeypatch.delenv("AILOVANTA_PUBLIC_INFERENCE_TOKEN", raising=False)
    client, _, _ = _client(tmp_path)
    response = client.post(
        "/jobs/public-inference",
        json={"prompt": "public code task", "privacy_scope": "public"},
    )
    assert response.status_code == 503


def test_node_without_requested_model_cannot_claim_coding_inference(tmp_path, monkeypatch):
    monkeypatch.setenv("AILOVANTA_PUBLIC_INFERENCE_TOKEN", "job-secret")
    client, _, _ = _client(tmp_path)
    node_token = _register_gpu(client, models=["qwen2.5-coder:7b"])

    queued = client.post(
        "/jobs/public-inference",
        headers={"X-Ailovanta-Job-Token": "job-secret"},
        json={
            "prompt": "public task for a different model",
            "privacy_scope": "public",
            "model": "qwen3-coder:30b",
            "min_gpu_memory_gb": 20,
        },
    )
    assert queued.status_code == 200
    assert queued.json()["eligible_nodes"] == 0
    assert queued.json()["status"] == "waiting_for_compatible_node"

    assigned = client.get(
        "/jobs/next",
        params={"node_id": "node_security_test"},
        headers={"X-Ailovanta-Node-Token": node_token},
    )
    assert assigned.status_code == 200
    assert assigned.json()["job"] is None


def test_authenticated_public_inference_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("AILOVANTA_PUBLIC_INFERENCE_TOKEN", "job-secret")
    client, _, _ = _client(tmp_path)
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
    assert queued.json()["eligible_nodes"] == 1
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
    assert job["payload"]["model"] == "qwen2.5-coder:7b"

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
    client, _, _ = _client(tmp_path)
    response = client.post(
        "/jobs/public-inference",
        headers={"X-Ailovanta-Job-Token": "job-secret"},
        json={"prompt": "private source", "privacy_scope": "private"},
    )
    assert response.status_code == 422
