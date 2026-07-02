from pathlib import Path

from api.artifact_binding import ArtifactBindingStore
from api.worker_transport import WorkerInferenceClient, WorkerInferenceRequest, WorkerInferenceUnavailable


def test_worker_url_uses_specific_env(monkeypatch) -> None:
    monkeypatch.setenv("AILOVANTA_WORKER_URL_RT_OWNED_1", "http://127.0.0.1:9001/")
    assert WorkerInferenceClient.worker_url("rt-owned-1") == "http://127.0.0.1:9001"


def test_worker_url_uses_default_env(monkeypatch) -> None:
    monkeypatch.delenv("AILOVANTA_WORKER_URL_RT_OWNED_1", raising=False)
    monkeypatch.setenv("AILOVANTA_DEFAULT_WORKER_URL", "http://127.0.0.1:9002")
    assert WorkerInferenceClient.worker_url("rt-owned-1") == "http://127.0.0.1:9002"


def test_worker_url_needs_config(monkeypatch) -> None:
    monkeypatch.delenv("AILOVANTA_WORKER_URL_RT_OWNED_1", raising=False)
    monkeypatch.delenv("AILOVANTA_DEFAULT_WORKER_URL", raising=False)
    try:
        WorkerInferenceClient.worker_url("rt-owned-1")
    except WorkerInferenceUnavailable as exc:
        assert "not configured" in str(exc)
    else:
        raise AssertionError("configuration required")


def test_infer_uses_local_artifact_when_worker_url_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AILOVANTA_WORKER_URL_RT_OWNED_1", raising=False)
    monkeypatch.delenv("AILOVANTA_DEFAULT_WORKER_URL", raising=False)
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text('{"backend":"jsonl-stat","token_count":3}', encoding="utf-8")
    ArtifactBindingStore().register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "manifest_hash": "sha256:test"},
        {"artifact_hash": "sha256:test", "artifact_id": "artifact_test", "checkpoint_uri": checkpoint.as_uri()},
        backend_kind="jsonl-stat",
        backend_ref=checkpoint.as_uri(),
        status="candidate",
    )
    result = WorkerInferenceClient().infer(
        WorkerInferenceRequest(
            prompt="hello",
            model_id="ailovanta-owned",
            version="candidate",
            policy_mode="open_research",
            runtime_id="rt-owned-1",
            node_id="node-owned-1",
            model_manifest_hash="sha256:test",
        )
    )
    assert result.source == "ailovanta-local-artifact-worker"
    assert "metadata loaded" in result.answer
    assert result.raw["local_artifact_worker"] is True
