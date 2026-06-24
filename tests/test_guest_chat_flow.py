from fastapi.testclient import TestClient

from api.main import app


def test_guest_chat_flow_creates_and_reuses_conversation() -> None:
    client = TestClient(app)
    user_id = "guest_pytest_flow"

    first = client.post(
        "/ailovanta/v1/chat",
        json={"prompt": "my first guest message", "user_id": user_id, "title": "Guest flow"},
    )
    assert first.status_code == 200
    first_body = first.json()
    conversation_id = first_body["conversation_id"]
    assert conversation_id.startswith("conv_")
    assert first_body["context_messages_used"] >= 1

    second = client.post(
        "/ailovanta/v1/chat",
        json={"prompt": "continue this conversation", "user_id": user_id, "conversation_id": conversation_id},
    )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["conversation_id"] == conversation_id
    assert second_body["context_messages_used"] >= 3

    history = client.get(f"/ailovanta/v1/conversations/{conversation_id}/messages")
    assert history.status_code == 200
    messages = history.json()["messages"]
    assert len(messages) >= 4
    assert [message["role"] for message in messages[-4:]] == ["user", "assistant", "user", "assistant"]

    listed = client.get("/ailovanta/v1/conversations", params={"user_id": user_id})
    assert listed.status_code == 200
    assert any(item["id"] == conversation_id for item in listed.json()["conversations"])

    deleted = client.delete(f"/ailovanta/v1/conversations/{conversation_id}")
    assert deleted.status_code == 200
    assert deleted.json()["ok"] is True


def test_guest_chat_does_not_break_usage_and_reputation_endpoints() -> None:
    client = TestClient(app)
    usage = client.get("/usage/summary", params={"user_id": "guest_pytest_flow"})
    assert usage.status_code == 200
    assert "by_type" in usage.json()

    leaderboard = client.get("/reputation/leaderboard")
    assert leaderboard.status_code == 200
    assert "nodes" in leaderboard.json()
