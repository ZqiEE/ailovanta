from api.cost_guard import zero_cash_status


def test_zero_cash_mode_has_no_required_external_services(monkeypatch) -> None:
    for name in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "SENTRY_DSN",
        "POSTHOG_API_KEY",
        "STRIPE_SECRET_KEY",
        "AWS_ACCESS_KEY_ID",
        "CLOUDFLARE_API_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AILOVANTA_ZERO_CASH_MODE", "true")

    status = zero_cash_status()
    assert status["zero_cash_ready"] is True
    assert status["required_external_model_apis"] == []
    assert status["required_managed_databases"] == []
    assert status["required_managed_storage"] == []


def test_zero_cash_guard_reports_external_service_without_secret_value(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "do-not-expose-this-value")
    status = zero_cash_status()
    assert status["zero_cash_ready"] is False
    assert "OPENAI_API_KEY" in status["external_service_variables_detected"]
    assert "do-not-expose-this-value" not in repr(status)
