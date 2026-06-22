from __future__ import annotations

import tempfile
from pathlib import Path

from api.source_registry import SourceRegistry


def test_source_registry_adds_and_lists_source() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = SourceRegistry(Path(tmp) / "corpus.sqlite3")
        source = registry.add_source({"name": "demo", "source_type": "local", "base_url": "local://demo"})
        assert source["source_id"]
        assert source["allowed_for_search"] is True
        assert len(registry.list_sources()) == 1
