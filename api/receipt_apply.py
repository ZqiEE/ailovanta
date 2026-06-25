from __future__ import annotations

from pathlib import Path
from typing import Any

from api.foundation_result_import import import_foundation_result_file
from api.model_warm import ModelWarm, WarmSpec
from api.owned_doctor import OwnedDoctor


def apply_result(path: str | Path, runtime_id: str = "rt-owned-1", node_id: str = "node-owned-1") -> dict[str, Any]:
    imported = import_foundation_result_file(path)
    binding = imported.get("artifact_binding") or {}
    model_key = binding.get("model_key") or "ailovanta-owned:candidate"
    before = OwnedDoctor().check(model_key)
    action = ModelWarm().run(WarmSpec(model_key=model_key, runtime_id=runtime_id, node_id=node_id))
    after = OwnedDoctor().check(model_key)
    return {"ok": bool(after.get("ok")), "imported": imported, "before": before, "action": action, "after": after}
