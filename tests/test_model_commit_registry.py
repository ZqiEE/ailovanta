from __future__ import annotations

import tempfile
from pathlib import Path

from api.model_commit_registry import ModelCommitRegistry


def test_model_commit_registry_registers_item() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = ModelCommitRegistry(Path(tmp) / "ledger.sqlite3")
        item = registry.register("demo", "v1", "hash_a", "proof_a", 0.9, {"note": "ok"})
        assert item["commit_id"]
        assert item["model_name"] == "demo"
        assert item["metadata"]["note"] == "ok"
        assert len(registry.list_commits()) == 1
