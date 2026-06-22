from __future__ import annotations

from api.local_chain_adapter import LocalChainAdapter
from api.testnet_chain_adapter import TestnetChainAdapter


def test_local_chain_adapter_returns_receipt() -> None:
    receipt = LocalChainAdapter().submit_event({"event_id": "evt_test", "node_id": "node_a"})
    assert receipt.ok is True
    assert receipt.adapter == "local-simulated-chain"
    assert receipt.reference == "evt_test"
    assert receipt.payload_hash


def test_testnet_chain_adapter_dry_run_receipt() -> None:
    adapter = TestnetChainAdapter("pytest-net")
    receipt = adapter.submit_model_commit({"commit_id": "commit_test", "model_hash": "hash_a"})
    assert receipt.ok is True
    assert receipt.adapter == "testnet-dry-run"
    assert receipt.reference.startswith("txdry_")
    assert adapter.status()["dry_run_submissions"] == 1
