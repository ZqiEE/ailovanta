from __future__ import annotations

import pytest

from api.node_trust import NodeTrustStore


@pytest.fixture(autouse=True)
def api_contract_runtime_trust(request, tmp_path, monkeypatch):
    if request.node.path.name != "test_api_contract.py":
        yield
        return
    path = tmp_path / "runtime-trust.sqlite3"
    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(path))
    store = NodeTrustStore(path)
    for node_id, score in [("node-cold", 0.95), ("node-warm", 0.90), ("node-public-large", 0.99), ("node-trusted", 0.92)]:
        store.register(node_id, "fixture-value", trust_score=score)
    yield
