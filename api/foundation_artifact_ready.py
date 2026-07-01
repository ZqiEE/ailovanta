from __future__ import annotations

import os
from typing import Any

from api.artifact_binding import ArtifactBindingStore
from api.runtime_ref import check_runtime_ref

BOOTSTRAP_HASHES = {"sha256:local-owned-candidate"}
BOOTSTRAP_SOURCES = {"bootstrap_owned_runtime"}


def check_foundation_artifact_ready(model_key: str | None = None, binding_store: ArtifactBindingStore | None = None) -> dict[str, Any]:
    key = model_key or os.getenv("AILOVANTA_OWNED_MODEL_KEY", "ailovanta-owned:candidate")
    store = binding_store or ArtifactBindingStore()
    binding = store.latest_for_model(key, active_only=True)
    blockers: list[str] = []
    warnings: list[str] = []

    if not binding:
        return {"ok": False, "model_key": key, "blockers": ["no_active_binding"], "warnings": [], "binding": None, "ref_check": None}

    metadata = binding.get("metadata") or {}
    source = str(metadata.get("source") or "")
    artifact_hash = str(binding.get("artifact_hash") or "")
    backend_ref = str(binding.get("backend_ref") or "")
    artifact_id = str(binding.get("artifact_id") or "")

    if source in BOOTSTRAP_SOURCES or artifact_hash in BOOTSTRAP_HASHES or artifact_id == "local_owned_runtime_bootstrap":
        blockers.append("bootstrap_artifact_only")
    if source != "foundation_import":
        blockers.append("not_foundation_import")
    if not artifact_hash.startswith("sha256:"):
        blockers.append("bad_artifact_hash")
    if not backend_ref:
        blockers.append("missing_backend_ref")

    ref_check = check_runtime_ref(binding)
    if not ref_check.get("ready"):
        blockers.append("runtime_ref_not_ready:" + str(ref_check.get("reason")))

    if binding.get("status") not in {"active", "candidate"}:
        blockers.append("binding_not_active:" + str(binding.get("status")))

    if metadata.get("source") == "foundation_import" and not metadata.get("core_result_id"):
        warnings.append("missing_core_result_id")

    return {"ok": not blockers, "model_key": key, "blockers": sorted(set(blockers)), "warnings": sorted(set(warnings)), "binding": binding, "ref_check": ref_check}
