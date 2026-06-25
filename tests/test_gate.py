from api.artifact_binding import ArtifactBindingStore
from api.route_gate import apply_gate


def test_gate_missing_binding(tmp_path) -> None:
    result = apply_gate("ailovanta-owned", "candidate", "r1", ArtifactBindingStore(tmp_path / "b.sqlite3"))
    assert result["assigned"] is False


def test_gate_ready_binding(tmp_path) -> None:
    p = tmp_path / "c.bin"
    p.write_text("{}", encoding="utf-8")
    store = ArtifactBindingStore(tmp_path / "b.sqlite3")
    store.register_binding({"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:r", "status": "active"}, {"artifact_id": "a", "artifact_hash": "sha256:a", "checkpoint_uri": "file://" + str(p)}, backend_ref="file://" + str(p), status="active")
    assert apply_gate("ailovanta-owned", "candidate", "r1", store) is None
