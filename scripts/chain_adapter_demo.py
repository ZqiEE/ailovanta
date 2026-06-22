from __future__ import annotations

import json

from api.contribution_ledger import ContributionLedger
from api.local_chain_adapter import LocalChainAdapter
from api.model_commit_registry import ModelCommitRegistry
from api.object_store_adapter import LocalObjectStoreAdapter
from api.testnet_chain_adapter import TestnetChainAdapter


def main() -> None:
    ledger = ContributionLedger()
    models = ModelCommitRegistry()
    objects = LocalObjectStoreAdapter()
    testnet = TestnetChainAdapter()
    local = LocalChainAdapter(ledger, models)

    snapshot = {
        "ledger": ledger.network_summary(),
        "events": ledger.list_events(limit=20),
        "model_commits": models.list_commits(limit=20),
    }
    stored = objects.put_json(snapshot, prefix="snapshot")
    receipts = []
    for event in snapshot["events"]:
        receipts.append(testnet.submit_event(event).__dict__)
    for commit in snapshot["model_commits"]:
        receipts.append(testnet.submit_model_commit(commit).__dict__)

    output = {"object": stored, "local_status": local.status(), "testnet_status": testnet.status(), "receipts": receipts}
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
