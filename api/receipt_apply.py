from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from api.artifact_integrity import verify_artifact_uri
from api.foundation_result_import import import_foundation_result_file
from api.model_warm import ModelWarm, WarmSpec
from api.owned_doctor import OwnedDoctor


def should_verify(value: bool | None) -> bool:
    if value is not None:
        return bool(value)
    return os.getenv("AILOVANTA_VERIFY_ROUTE_ARTIFACT", "false").lower() in {"1", "true", "yes", "on"}


def apply_result(path: str | Path, runtime_id: str = "rt-owned-1", node_id: str = "node-owned-1", verify_artifact: bool | None = None) -> dict[str, Any]:
    imported = import_foundation_result_file(path)
    binding = imported.get("artifact_binding") or {}
    model_key = binding.get("model_key") or "ailovanta-owned:candidate"
    verify_enabled = should_verify(verify_artifact)
    artifact_integrity = {"ok": True, "skipped": True, "reason": "disabled"}
    if verify_enabled:
        artifact_integrity = verify_artifact_uri(str(binding.get("checkpoint_uri") or binding.get("backend_ref") or ""), str(binding.get("artifact_hash") or ""))
    before = OwnedDoctor().check(model_key)
    action = None
    if artifact_integrity.get("ok"):
        action = ModelWarm().run(WarmSpec(model_key=model_key, runtime_id=runtime_id, node_id=node_id))
    after = OwnedDoctor().check(model_key)
    return {"ok": bool(artifact_integrity.get("ok") and after.get("ok")), "imported": imported, "artifact_integrity": artifact_integrity, "before": before, "action": action, "after": after}
