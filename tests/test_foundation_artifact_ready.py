from __future__ import annotations

from pathlib import Path

from api.artifact_binding import ArtifactBindingStore
from api.foundation_artifact_ready import check_foundation_artifact_ready


def runtime_model() -> dict:
    return {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:real123"}


def artifact(path: Path, artifact_hash: str = "sha256:real123", artifact_id: str = "artifact_real") -> dict:
    return {"artifact_id": artifact_id, "artifact_hash": artifact_hash, "checkpoint_uri": "file://" + str(path.resolve()), "backend_ref": "file://" + str(path.resolve()), "backend_kind": "checkpoint-artifact"}


def test_bootstrap_artifact_is_not_foundation_ready(tmp_path: Path) -> None:
    checkpoint = tmp_path / "bootstrap.json"
    checkpoint.write_text("{}", encoding="utf-8")
    store = ArtifactBindingStore(":memory:")
    store.register_binding(runtime_model(), artifact(checkpoint, "sha256:local-owned-candidate", "local_owned_runtime_bootstrap"), status="active", metadata={"source": "bootstrap_owned_runtime"})
    result = check_foundation_artifact_ready(binding_store=store)
    assert not result["ok"]
    assert "bootstrap_artifact_only" in result["blockers"]
    assert "not_foundation_import" in result["blockers"]


def test_foundation_import_artifact_is_ready(tmp_path: Path) -> None:
    checkpoint = tmp_path / "foundation.json"
    checkpoint.write_text("{}", encoding="utf-8")
    store = ArtifactBindingStore(":memory:")
    store.register_binding(runtime_model(), artifact(checkpoint), status="active", metadata={"source": "foundation_import", "core_result_id": "core_result_1"})
    result = check_foundation_artifact_ready(binding_store=store)
    assert result["ok"]
    assert result["blockers"] == []
