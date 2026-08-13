from __future__ import annotations

from typing import Any

import httpx

from api.ollama_adapter import OllamaAdapter


def coding_model_status(model: OllamaAdapter) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(f"{model.config.base_url}/api/tags")
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        return {"available": False, "model": model.config.model, "model_present": False, "error": str(exc)}
    names = {str(row.get("name") or "") for row in payload.get("models", [])}
    wanted = model.config.model
    model_present = wanted in names or any(name.split(":", 1)[0] == wanted.split(":", 1)[0] for name in names)
    return {"available": True, "model": wanted, "model_present": model_present, "installed_models": sorted(names)}
