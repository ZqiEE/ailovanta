from __future__ import annotations

from typing import Any

from api.chain_adapter import ChainAdapter, ChainReceipt
from api.content_addressing import content_id, hash_object
from api.contribution_ledger import ContributionLedger
from api.model_commit_registry import ModelCommitRegistry


class LocalChainAdapter(ChainAdapter):
    name = "local-simulated-chain"

    def __init__(self, ledger: ContributionLedger | None = None, models: ModelCommitRegistry | None = None) -> None:
        self.ledger = ledger or ContributionLedger()
        self.models = models or ModelCommitRegistry()

    def submit_event(self, event: dict[str, Any]) -> ChainReceipt:
        payload_hash = hash_object(event)
        reference = event.get("event_id") or content_id(event, prefix="evtref")
        return ChainReceipt(True, self.name, "submit_event", reference, payload_hash, "stored in local ledger simulation")

    def submit_model_commit(self, commit: dict[str, Any]) -> ChainReceipt:
        payload_hash = hash_object(commit)
        reference = commit.get("commit_id") or content_id(commit, prefix="mref")
        return ChainReceipt(True, self.name, "submit_model_commit", reference, payload_hash, "stored in local model registry simulation")

    def status(self) -> dict[str, Any]:
        return {
            "adapter": self.name,
            "ledger": self.ledger.network_summary(),
            "model_commits": len(self.models.list_commits(limit=1000)),
        }
