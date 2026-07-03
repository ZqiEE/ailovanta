import json
from pathlib import Path

from api.artifact_binding import ArtifactBindingStore
from api.autonomous_source_training import build_autonomous_training_job_payload, corpus_to_training_dataset, run_autonomous_source_training_cycle, training_text_from_record
from api.continuous_training_ledger import source_fingerprint
from api.owned_promotion_proof import build_owned_promotion_proof
from api.route_book import RouteBook


def test_training_text_from_instruction_record() -> None:
    text = training_text_from_record(
        {
            "training_record_kind": "instruction",
            "instruction": "Explain setup",
            "context": "Install dependencies and run tests.",
            "expected_response": "Give actionable setup steps.",
        }
    )

    assert "Instruction: Explain setup" in text
    assert "Context: Install dependencies" in text
    assert "Expected: Give actionable" in text


def test_corpus_to_training_dataset(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "training_record_kind": "code",
                        "text": "def add(a, b): return a + b",
                        "path": "algorithms/add.py",
                        "source_name": "local",
                        "rights_id": "rights_1",
                        "curriculum_tags": ["algorithmic_core"],
                        "priority_score": 220,
                        "priority_tier": "high",
                    }
                ),
                json.dumps(
                    {
                        "training_record_kind": "code",
                        "text": "SERVICE_NAME=ailovanta",
                        "path": "config/env.py",
                        "source_name": "local",
                        "rights_id": "rights_1",
                        "curriculum_tags": ["project_usage"],
                        "priority_score": 20,
                        "priority_tier": "baseline",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = corpus_to_training_dataset(corpus, tmp_path / "train.jsonl", max_records=1)

    assert result["ok"] is True
    assert result["records"] == 1
    assert "def add" in (tmp_path / "train.jsonl").read_text(encoding="utf-8")
    assert result["selected_tags"]["algorithmic_core"] == 1


def test_corpus_to_training_dataset_deduplicates_duplicate_content(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "training_record_kind": "code",
                        "text": "def fib(n):\n    return n if n < 2 else fib(n - 1) + fib(n - 2)\n",
                        "path": "algorithms/fib.py",
                        "source_name": "repo-a",
                        "rights_id": "rights_1",
                        "curriculum_tags": ["algorithmic_core"],
                        "priority_score": 220,
                        "priority_tier": "high",
                    }
                ),
                json.dumps(
                    {
                        "training_record_kind": "code",
                        "text": "def fib(n): return n if n < 2 else fib(n - 1) + fib(n - 2)",
                        "path": "examples/fib.py",
                        "source_name": "repo-b",
                        "rights_id": "rights_2",
                        "curriculum_tags": ["syntax_foundation"],
                        "priority_score": 40,
                        "priority_tier": "baseline",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = corpus_to_training_dataset(corpus, tmp_path / "train.jsonl", max_records=5)
    lines = (tmp_path / "train.jsonl").read_text(encoding="utf-8").strip().splitlines()

    assert result["records"] == 1
    assert result["duplicates_skipped"] == 1
    assert len(lines) == 1
    assert "algorithms/fib.py" in lines[0]


def test_autonomous_source_training_cycle_queues_job(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    (docs / "README.md").write_text("Ailovanta local source explains autonomous training setup and worker execution." * 3, encoding="utf-8")
    sources = tmp_path / "sources.json"
    sources.write_text(
        json.dumps(
            {
                "schema_version": "ailovanta.github_code_sources.v1",
                "sources": [
                    {
                        "name": "local-source",
                        "path": str(repo),
                        "license_policy": "owner_controlled",
                        "enabled": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    posted = {}

    def fake_post(server: str, path: str, body: dict):
        posted["server"] = server
        posted["path"] = path
        posted["body"] = body
        return {"ok": True, "job": {"id": "train_auto_1", "status": "queued", "payload": body}}

    monkeypatch.setattr("api.autonomous_source_training.post_json", fake_post)

    result = run_autonomous_source_training_cycle(
        server="http://127.0.0.1:8000",
        sources_path=sources,
        work_root=tmp_path / "work",
        discover=False,
        fetch=False,
        max_sources=5,
        max_records=10,
        corpus_mode="mixed",
    )

    assert result["ok"] is True
    assert result["stage"] == "training_job_queued"
    assert result["dataset"]["records"] > 0
    assert posted["path"] == "/training/jobs"
    assert posted["body"]["kind"] == "lora_micro"
    assert posted["body"]["real"] is True
    assert posted["body"]["use_transformers"] is True
    assert posted["body"]["training_backend"] == "auto"
    assert "peft" not in posted["body"]
    assert "lora" not in posted["body"]
    assert posted["body"]["requires_gpu"] is True
    assert posted["body"]["allow_lightweight_fallback"] is False
    assert posted["body"]["dataset_uri"].startswith("file://")
    assert result["state"]["stage"] == "training_job_queued"
    assert result["state"]["job"]["status"] == "queued"
    assert result["state"]["selection"]["selected"] == 1


def seed_ready_owned_runtime(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AILOVANTA_ARTIFACT_BINDINGS_PATH", str(tmp_path / "artifact_bindings.sqlite3"))
    monkeypatch.setenv("AILOVANTA_ROUTE_BOOK_PATH", str(tmp_path / "route_book.sqlite3"))
    artifact = tmp_path / "owned-transformers"
    artifact.mkdir()
    artifact_hash = "sha256:" + "a" * 64
    store = ArtifactBindingStore(tmp_path / "artifact_bindings.sqlite3")
    binding = store.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:model", "status": "active"},
        {"artifact_id": "artifact-owned", "artifact_hash": artifact_hash, "checkpoint_uri": artifact.resolve().as_uri()},
        backend_kind="transformers-local",
        backend_ref=artifact.resolve().as_uri(),
        status="active",
        metadata={
            "promotion_gate": {
                "ok": True,
                "decision": "promote_active",
                "blockers": [],
                "code_generation_eval": {"ok": True, "score": 1.0, "passed_cases": 2, "total_cases": 2, "backend_kind": "transformers-local"},
                "model_eval": {"runtime_evidence": {"requested_backend": "qlora", "actual_backend": "qlora", "real_training_executed": True, "fallback_used": False, "gpu_execution_evidence": True, "trained_rows": 64}},
                "artifact_integrity": {"ok": True, "actual_hash": artifact_hash, "expected_hash": artifact_hash},
                "artifact_distribution": {"ok": True, "distribution": {"manifest_hash": "sha256:" + "b" * 64, "storage_artifact_hash": artifact_hash}},
            },
            "training_worker_receipt": {
                "receipt_id": "receipt-1",
                "receipt_hash": "sha256:" + "c" * 64,
                "passed": True,
                "node_id": "node-1",
                "job_id": "job-1",
                "artifact_hash": artifact_hash,
            },
            "route_publish": {"ok": True},
        },
    )
    proof = build_owned_promotion_proof(binding, runtime_id="rt-owned-1", node_id="node-owned-1", route_key="owned-chat/default")
    store.update_metadata(binding["binding_id"], {**binding["metadata"], "promotion_proof": proof})
    RouteBook(tmp_path / "route_book.sqlite3").set_active("owned-chat/default", "ailovanta-owned:candidate", binding_id=binding["binding_id"], reason="test")


def test_autonomous_training_payload_supports_qlora() -> None:
    payload = build_autonomous_training_job_payload(
        dataset_path="runtime_data/train.jsonl",
        max_steps=32,
        base_model="codellama/CodeLlama-7b-hf",
        training_backend="qlora",
    )

    assert payload["kind"] == "lora_micro"
    assert payload["base_model"] == "codellama/CodeLlama-7b-hf"
    assert payload["real"] is True
    assert payload["training_backend"] == "qlora"
    assert payload["qlora"] is True
    assert payload["requires_gpu"] is True
    assert payload["allow_lightweight_fallback"] is False


def test_limit_sources_prefers_high_discovery_score(tmp_path: Path) -> None:
    from api.autonomous_source_training import limit_sources

    source_path = tmp_path / "sources.json"
    source_path.write_text(
        json.dumps(
            {
                "schema_version": "ailovanta.github_code_sources.v1",
                "sources": [
                    {"name": "low", "path": str(tmp_path), "enabled": True, "discovery_score": 1},
                    {"name": "high", "path": str(tmp_path), "enabled": True, "discovery_score": 100},
                ],
            }
        ),
        encoding="utf-8",
    )

    limited = limit_sources(source_path, tmp_path / "limited.json", max_sources=1, ledger_path=tmp_path / "ledger.json")
    payload = json.loads(Path(limited["output"]).read_text(encoding="utf-8"))
    assert payload["sources"][0]["name"] == "high"


def test_limit_sources_prefers_higher_training_value_score(tmp_path: Path) -> None:
    from api.autonomous_source_training import limit_sources

    source_path = tmp_path / "sources.json"
    source_path.write_text(
        json.dumps(
            {
                "schema_version": "ailovanta.github_code_sources.v1",
                "sources": [
                    {
                        "name": "popular-noisy",
                        "path": str(tmp_path / "repo-a"),
                        "enabled": True,
                        "discovery_score": 95,
                        "commercial_use_allowed": False,
                        "distillation_allowed": False,
                    },
                    {
                        "name": "compiler-kit",
                        "path": str(tmp_path / "repo-b"),
                        "enabled": True,
                        "discovery_score": 70,
                        "language": "Python",
                        "license_hint": "MIT",
                        "commercial_use_allowed": True,
                        "distillation_allowed": True,
                        "topics": ["compiler", "testing"],
                        "stars": 800,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    limited = limit_sources(source_path, tmp_path / "limited.json", max_sources=1, ledger_path=tmp_path / "ledger.json")
    payload = json.loads(Path(limited["output"]).read_text(encoding="utf-8"))
    assert payload["sources"][0]["name"] == "compiler-kit"


def test_autonomous_source_training_cycle_skips_when_no_new_sources(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("Ailovanta repeated source should not be queued twice." * 3, encoding="utf-8")
    sources = tmp_path / "sources.json"
    source = {
        "name": "local-source",
        "path": str(repo),
        "license_policy": "owner_controlled",
        "enabled": True,
        "discovery_score": 10,
    }
    sources.write_text(json.dumps({"schema_version": "ailovanta.github_code_sources.v1", "sources": [source]}), encoding="utf-8")

    posts = []

    def fake_post(server: str, path: str, body: dict):
        posts.append(body)
        return {"ok": True, "job": {"id": "train_auto_1", "status": "queued", "payload": body}}

    monkeypatch.setattr("api.autonomous_source_training.post_json", fake_post)
    monkeypatch.setattr("api.autonomous_source_training.get_json", lambda server, path: {"jobs": []})

    first = run_autonomous_source_training_cycle(
        server="http://127.0.0.1:8000",
        sources_path=sources,
        work_root=tmp_path / "work",
        discover=False,
        fetch=False,
        max_sources=1,
        max_records=10,
        corpus_mode="mixed",
        ledger_path=tmp_path / "ledger.json",
    )
    second = run_autonomous_source_training_cycle(
        server="http://127.0.0.1:8000",
        sources_path=sources,
        work_root=tmp_path / "work",
        discover=False,
        fetch=False,
        max_sources=1,
        max_records=10,
        corpus_mode="mixed",
        ledger_path=tmp_path / "ledger.json",
    )

    assert first["stage"] == "training_job_queued"
    assert second["stage"] == "no_new_sources"
    assert len(posts) == 1


def test_autonomous_source_training_cycle_reports_owned_runtime_ready_without_new_sources(monkeypatch, tmp_path: Path) -> None:
    seed_ready_owned_runtime(monkeypatch, tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("Ailovanta repeated source should not be queued twice." * 3, encoding="utf-8")
    sources = tmp_path / "sources.json"
    source = {
        "name": "local-source",
        "path": str(repo),
        "license_policy": "owner_controlled",
        "enabled": True,
        "discovery_score": 10,
    }
    sources.write_text(json.dumps({"schema_version": "ailovanta.github_code_sources.v1", "sources": [source]}), encoding="utf-8")

    monkeypatch.setattr("api.autonomous_source_training.get_json", lambda server, path: {"jobs": [{"id": "train_auto_1", "status": "done"}]})
    ledger = tmp_path / "ledger.json"
    training_fingerprint = source_fingerprint(source, corpus_mode="mixed")
    ledger.write_text(
        json.dumps(
            {
                "schema_version": "ailovanta.continuous_training_ledger.v1",
                "sources": {training_fingerprint: {"fingerprint": training_fingerprint, "status": "done"}},
                "datasets": {},
                "batches": {},
            }
        ),
        encoding="utf-8",
    )

    result = run_autonomous_source_training_cycle(
        server="http://127.0.0.1:8000",
        sources_path=sources,
        work_root=tmp_path / "work",
        discover=False,
        fetch=False,
        max_sources=1,
        max_records=10,
        corpus_mode="mixed",
        ledger_path=ledger,
        state_path=tmp_path / "full_auto_state.json",
    )

    assert result["ok"] is True
    assert result["stage"] == "owned_runtime_ready"
    assert result["owned_runtime"]["self_trained_ready"] is True
    assert result["owned_runtime"]["benchmark_summary"]["ok"] is True
    assert result["state"]["owned_runtime"]["route_matches_active_binding"] is True
