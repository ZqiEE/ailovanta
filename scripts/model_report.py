from __future__ import annotations

import json

from api.distributed_model_registry import DistributedModelRegistry
from api.model_node_inventory import ModelNodeInventory
from api.model_router import ModelRouter


def main() -> None:
    registry = DistributedModelRegistry()
    inventory = ModelNodeInventory()
    router = ModelRouter(registry, inventory)
    report = {
        "registry": registry.summary(),
        "inventory": inventory.summary(),
        "packages": registry.list_packages(limit=20),
        "nodes": inventory.list_inventory(limit=20),
        "route": router.route(min_score=0.0),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
