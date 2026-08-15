from api.local_usage_guard import LocalUsageGuard


def test_local_usage_guard_limits_expensive_requests(monkeypatch) -> None:
    monkeypatch.setenv("AILOVANTA_PROPOSES_PER_WINDOW", "2")
    monkeypatch.setenv("AILOVANTA_PROPOSE_WINDOW_SECONDS", "60")
    guard = LocalUsageGuard()

    assert guard.allow("client-a") is True
    assert guard.allow("client-a") is True
    assert guard.allow("client-a") is False
    assert guard.allow("client-b") is True


def test_local_usage_guard_has_single_model_slot_by_default(monkeypatch) -> None:
    monkeypatch.setenv("AILOVANTA_MODEL_CONCURRENCY", "1")
    monkeypatch.setenv("AILOVANTA_MODEL_QUEUE_TIMEOUT_SECONDS", "0")
    guard = LocalUsageGuard()

    assert guard.acquire_model() is True
    assert guard.acquire_model() is False
    guard.release_model()
    assert guard.acquire_model() is True
    guard.release_model()
