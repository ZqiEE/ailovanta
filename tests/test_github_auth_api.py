from fastapi.testclient import TestClient

from api.auth_store import AuthStore
from api.main import app


def test_github_login_requires_config_when_not_set(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_CLIENT_ID", raising=False)
    client = TestClient(app)
    response = client.get("/auth/github/login")
    assert response.status_code == 503


def test_auth_store_session_roundtrip(tmp_path) -> None:
    store = AuthStore(tmp_path / "auth.sqlite3")
    user = store.upsert_github_user(
        {
            "id": 123,
            "login": "demo-user",
            "name": "Demo User",
            "email": "demo@example.com",
            "avatar_url": "https://example.com/avatar.png",
        }
    )
    session = store.create_session(user["id"])
    loaded = store.get_session(session["token"])
    assert loaded is not None
    assert loaded["user_id"] == user["id"]
    assert store.revoke_session(session["token"]) is True
    assert store.get_session(session["token"]) is None
