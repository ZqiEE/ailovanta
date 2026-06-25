from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.ap import ok as apply_gate
from api.g2 import eval_payload
from api.route_health import RouteHealth


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def final_blockers(gate: dict[str, Any], artifact: dict[str, Any], route_health: dict[str, Any], model_key: str) -> list[str]:
    blockers: list[str] = []
    if not artifact.get("artifact_hash"):
        blockers.append("missing_artifact_hash")
    if route_health.get("model_key") and route_health.get("model_key") != model_key:
        blockers.append("active_route_model_mismatch")
    blockers.extend(str(item) for item in gate.get("blockers", []) or [])
    blockers.extend(str(item) for item in route_health.get("blockers", []) or [])
    return sorted(set(blockers))


def report(result_path: str | Path, model_key: str = "ailovanta-owned:candidate", route_key: str = "owned-chat/default") -> dict[str, Any]:
    result = load(result_path)
    artifact = result.get("artifact") if isinstance(result.get("artifact"), dict) else {}
    gate = apply_gate(result_path)
    health = RouteHealth().check(route_key)
    payload = eval_payload(result)
    blockers = final_blockers(gate, artifact, health, model_key)
    return {
        "ok": not blockers,
        "stage": "runtime_ready" if not blockers else "blocked",
        "blockers": blockers,
        "artifact_id": artifact.get("artifact_id"),
        "artifact_hash": artifact.get("artifact_hash"),
        "model_key": model_key,
        "route_key": route_key,
        "active_route": health.get("route"),
        "route_health": health,
        "apply_gate": gate,
        "runtime": health.get("runtime"),
        "eval_guardrails": payload.get("guardrails"),
    }
