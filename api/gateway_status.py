from __future__ import annotations

from api.contribution_ledger import ContributionLedger
from api.distributed_model_registry import DistributedModelRegistry
from api.gateway_audit_log import GatewayAuditLog
from api.model_node_inventory import ModelNodeInventory


def gateway_status() -> dict:
    return {
        "registry": DistributedModelRegistry().summary(),
        "inventory": ModelNodeInventory().summary(),
        "audit": GatewayAuditLog().summary(),
        "ledger": ContributionLedger().network_summary(),
    }
