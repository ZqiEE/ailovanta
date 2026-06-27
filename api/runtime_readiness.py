from __future__ import annotations

from typing import Any
from uuid import uuid4

from api.route_book import RouteBook
from api.runtime_router import RuntimeRequest
from api.runtime_store import RuntimeStore


def split_model_key(model_key: str) -> tuple[str, str]:
    if ":" not in model_key:
        return model_key, "latest"
    model_id, version = model_key.split(":", 1)
    return model_id, version


class RuntimeReadiness:
    def __init__(self, routes: RouteBook | None = None, runtime: RuntimeStore | None = None) -> None:
        self.routes = routes or RouteBook()
        self.runtime = runtime or RuntimeStore()

    def check_route(self, route_key: str = "owned-chat/default") -> dict[str, Any]:
        route = self.routes.active(route_key)
        if not route:
            return {"ok": False, "reason": "active_route_missing", "route_key": route_key}
        model_key = str(route.get("model_key") or "")
        if not model_key:
            return {"ok": False, "reason": "model_key_missing", "route_key": route_key, "route": route}
        model_id, version = split_model_key(model_key)
        routed = self.runtime.route(RuntimeRequest(request_id="readiness_" + uuid4().hex[:10], model_id=model_id, version=version, verification_required=True))
        if not routed.get("assigned"):
            return {"ok": False, "reason": "no_verified_capable_runtime", "route_key": route_key, "route": route, "runtime_route": routed}
        assignment = routed.get("assignment") or {}
        return {"ok": True, "route_key": route_key, "route": route, "runtime_route": routed, "assignment": assignment}
