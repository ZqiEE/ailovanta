from __future__ import annotations

from typing import Any

import httpx

from api.model_lock import ModelLockStore
from api.ollama_adapter import OllamaAdapter


def _name_matches(installed: str, wanted: str) -> bool:
    if ":" in wanted:
        return installed == wanted
    return installed.split(":", 1)[0] == wanted


def coding_model_status(model: OllamaAdapter) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(f"{model.config.base_url}/api/tags")
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        return {
            "available": False,
            "model": model.config.model,
            "model_present": False,
            "error": str(exc),
        }

    rows = [row for row in payload.get("models", []) if isinstance(row, dict)]
    names = {str(row.get("name") or "") for row in rows}
    wanted = model.config.model
    selected = next(
        (row for row in rows if _name_matches(str(row.get("name") or ""), wanted)),
        None,
    )
    digest = str(selected.get("digest") or "") if selected else ""
    details = selected.get("details") if selected and isinstance(selected.get("details"), dict) else {}
    integrity = ModelLockStore().check(wanted, digest or None)
    return {
        "available": True,
        "model": wanted,
        "model_present": selected is not None,
        "model_digest": digest or None,
        "model_size": selected.get("size") if selected else None,
        "model_details": details,
        "integrity": integrity,
        "installed_models": sorted(names),
    }
