from __future__ import annotations

from api.content_addressing import hash_object
from api.contribution_ledger import ContributionLedger
from api.distributed_model_registry import DistributedModelRegistry
from api.gateway_audit_log import GatewayAuditLog
from api.model_node_inventory import ModelNodeInventory
from api.model_router import ModelRouter


class InferenceGateway:
    def __init__(
        self,
        registry: DistributedModelRegistry | None = None,
        inventory: ModelNodeInventory | None = None,
        audit: GatewayAuditLog | None = None,
        ledger: ContributionLedger | None = None,
    ) -> None:
        self.registry = registry or DistributedModelRegistry()
        self.inventory = inventory or ModelNodeInventory()
        self.audit = audit or GatewayAuditLog()
        self.ledger = ledger or ContributionLedger()
        self.router = ModelRouter(self.registry, self.inventory)

    def handle(self, payload: dict) -> dict:
        route = self.router.route(
            tag=payload.get("tag"),
            min_score=float(payload.get("min_score", 0.0)),
            require_gpu=bool(payload.get("require_gpu", False)),
        )
        if not route.get("routable"):
            event = self.audit.record(
                user_ref=payload.get("user_ref", "anonymous"),
                prompt_hash=payload["prompt_hash"],
                tag=payload.get("tag"),
                status="failed",
                details={"reason": route.get("reason")},
            )
            return {"ok": False, "request_id": payload["request_id"], "trace": event, "route": route}

        package = route["package"]
        node = route["node"]
        result = self._simulate_node_result(payload, package, node)
        result_hash = hash_object(result)
        event = self.audit.record(
            user_ref=payload.get("user_ref", "anonymous"),
            prompt_hash=payload["prompt_hash"],
            tag=payload.get("tag"),
            status="ok",
            package_hash=package["package_hash"],
            node_id=node["node_id"],
            result_hash=result_hash,
            details={"route_reason": route.get("reason"), "request_id": payload["request_id"]},
        )
        ledger_event = self.ledger.append(
            node_id=node["node_id"],
            event_type="gateway_result",
            object_hash=result_hash,
            score=float(package.get("score", 0.0)),
            credits=round(float(package.get("score", 0.0)) * 2, 3),
            details={"trace_id": event["trace_id"], "package_hash": package["package_hash"]},
        )
        return {
            "ok": True,
            "request_id": payload["request_id"],
            "result": result,
            "result_hash": result_hash,
            "trace": event,
            "ledger_event": ledger_event,
            "route": route,
        }

    @staticmethod
    def _simulate_node_result(payload: dict, package: dict, node: dict) -> dict:
        prompt = payload.get("prompt", "")
        preview = prompt[:120]
        return {
            "answer": f"Simulated private AI response for: {preview}",
            "package_hash": package["package_hash"],
            "package_name": package["name"],
            "node_id": node["node_id"],
            "runtime": package["runtime"],
        }
