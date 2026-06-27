from __future__ import annotations

from typing import Any
from uuid import uuid4

from api.main import runtime_registry
from api.owned_default import DefaultOwnedChatRequest, default_owned_chat


def check_owned_chat_default(route_key: str = "owned-chat/default") -> dict[str, Any]:
    result = default_owned_chat(
        DefaultOwnedChatRequest(
            prompt="health check",
            user_id="release-gate",
            conversation_id="probe_" + uuid4().hex[:10],
            route_key=route_key,
        ),
        runtime_registry,
    )
    return {
        "ok": bool(result.get("ok") and result.get("owned_model_ready")),
        "owned_model_ready": bool(result.get("owned_model_ready")),
        "route_key": route_key,
        "source": result.get("source"),
        "model_id": result.get("model_id"),
        "version": result.get("version"),
        "result": result,
    }
