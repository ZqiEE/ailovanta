from __future__ import annotations

import argparse
import json

from api.contribution_ledger import ContributionLedger
from api.local_chain_adapter import LocalChainAdapter
from api.model_commit_registry import ModelCommitRegistry
from api.testnet_chain_adapter import TestnetChainAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit local records through a chain adapter")
    parser.add_argument("--adapter", choices=["local", "testnet"], default="testnet")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    adapter = LocalChainAdapter() if args.adapter == "local" else TestnetChainAdapter()
    ledger = ContributionLedger()
    models = ModelCommitRegistry()
    receipts = []
    for event in ledger.list_events(limit=args.limit):
        receipts.append(adapter.submit_event(event).__dict__)
    for commit in models.list_commits(limit=args.limit):
        receipts.append(adapter.submit_model_commit(commit).__dict__)
    print(json.dumps({"adapter": adapter.status(), "receipts": receipts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
