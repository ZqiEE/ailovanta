from fastapi.testclient import TestClient

from api.main import app


def test_ailovanta_native_run_returns_runtime_route() -> None:
    client = TestClient(app)
    response = client.post(
        "/ailovanta/v1/run",
        json={"prompt": "hello", "model_id": "ailovanta-local", "version": "local", "use_runtime_router": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "ailovanta.run"
    assert body["model_id"] == "ailovanta-local"
    assert body["answer"]
    assert "runtime_route" in body
    assert body["usage"]["total_tokens"] >= 1
