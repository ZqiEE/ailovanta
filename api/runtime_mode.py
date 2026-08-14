from __future__ import annotations

import os
from typing import Any


def runtime_privacy_status() -> dict[str, Any]:
    mode = os.getenv("AILOVANTA_RUNTIME_MODE", "server-local").strip().lower() or "server-local"
    private_local = mode == "private-local"
    return {
        "mode": mode,
        "private_local": private_local,
        "project_files_leave_device": False if private_local else None,
        "prompt_leaves_device": False if private_local else None,
        "inference_device": "this computer" if private_local else "configured server runtime",
        "telemetry_required": False,
        "commercial_model_api_required": False,
    }
