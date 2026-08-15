from __future__ import annotations

import os
from typing import Any


# These variables are not required by Ailovanta Coding. Their presence usually
# means an operator intentionally connected an external service that may have
# its own billing model. Values are never returned.
EXTERNAL_SERVICE_ENV_VARS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "MISTRAL_API_KEY",
    "GROQ_API_KEY",
    "TOGETHER_API_KEY",
    "FIREWORKS_API_KEY",
    "SENTRY_DSN",
    "POSTHOG_API_KEY",
    "STRIPE_SECRET_KEY",
    "AWS_ACCESS_KEY_ID",
    "CLOUDFLARE_API_TOKEN",
)


def zero_cash_status() -> dict[str, Any]:
    detected = sorted(name for name in EXTERNAL_SERVICE_ENV_VARS if os.getenv(name))
    zero_cash_mode = os.getenv("AILOVANTA_ZERO_CASH_MODE", "true").strip().lower() not in {"0", "false", "no", "off"}
    runtime_mode = os.getenv("AILOVANTA_RUNTIME_MODE", "server-local").strip().lower() or "server-local"
    if runtime_mode == "control-plane":
        components = ["FastAPI", "SQLite scheduler metadata", "Caddy HTTPS"]
        operator_costs = ["server", "domain", "server bandwidth if separately billed"]
    elif runtime_mode == "private-local":
        components = ["FastAPI", "local project storage", "Ollama", "user-owned CPU/GPU"]
        operator_costs = ["user electricity/hardware usage"]
    else:
        components = ["FastAPI", "SQLite", "local project storage", "Ollama"]
        operator_costs = ["server", "domain", "server electricity/bandwidth if separately billed"]
    return {
        "runtime_mode": runtime_mode,
        "zero_cash_mode": zero_cash_mode,
        "zero_cash_ready": zero_cash_mode and not detected,
        "external_service_variables_detected": detected,
        "required_external_model_apis": [],
        "required_managed_databases": [],
        "required_managed_storage": [],
        "local_components": components,
        "operator_costs_not_eliminated": operator_costs,
    }
