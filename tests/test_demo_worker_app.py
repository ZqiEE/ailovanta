from pathlib import Path

from api.demo_worker_app import generate_local, looks_loadable, read_checkpoint, ref_path, resolve_model_dir


def test_ref_path_supports_file_uri(tmp_path: Path) -> None:
    item = tmp_path / "checkpoint.json"
    item.write_text("{}", encoding="utf-8")
    assert ref_path(item.as_uri()) == item


def test_read_checkpoint_returns_json(tmp_path: Path) -> None:
    item = tmp_path / "checkpoint.json"
    item.write_text('{"backend":"transformers-causal-lm","model_dir":"/tmp/model"}', encoding="utf-8")
    assert read_checkpoint(item)["backend"] == "transformers-causal-lm"


def test_resolve_model_dir_uses_checkpoint_parent_for_relative_paths(tmp_path: Path) -> None:
    checkpoint = tmp_path / "run" / "checkpoint.json"
    checkpoint.parent.mkdir()
    resolved = resolve_model_dir({"model_dir": "runtime_data/model_backend"}, checkpoint)
    assert resolved == str((checkpoint.parent / "runtime_data/model_backend").resolve())


def test_generate_local_gracefully_rejects_missing_model_dir() -> None:
    result = generate_local(None, "hello", 8)
    assert result["ok"] is False
    assert result["reason"] == "missing_model_dir"


def test_generate_local_gracefully_rejects_unloadable_dir(tmp_path: Path) -> None:
    assert looks_loadable(tmp_path) is False
    result = generate_local(str(tmp_path), "hello", 8)
    assert result["ok"] is False
    assert result["reason"] == "model_dir_not_loadable"
