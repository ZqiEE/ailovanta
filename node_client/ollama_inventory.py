from __future__ import annotations

from typing import Any

import httpx


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"


def installed_ollama_models(base_url: str = DEFAULT_OLLAMA_URL) -> list[str]:
    """Return only local Ollama model tags needed for scheduling.

    This never uploads prompts, model contents, local paths, or Ollama history.
    A missing/unreachable Ollama runtime simply means the node is not currently
    eligible for coding_inference jobs.
    """
    try:
        response = httpx.get(base_url.rstrip("/") + "/api/tags", timeout=2.0)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    except Exception:
        return []
    names = {
        str(row.get("name") or "").strip()
        for row in payload.get("models", [])
        if isinstance(row, dict) and str(row.get("name") or "").strip()
    }
    return sorted(names)[:128]
